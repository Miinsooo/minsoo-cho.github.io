"""Collect tuition evidence from Florida private school websites (first collection year: current site content).

Input : data/processed/fl_directory_2026.csv (homepage guessed from the director/contact email domain)
Output: data/processed/tuition_evidence.jsonl  one line per school (resumable: finished schools are skipped)
        data/raw/school_sites/run1/<school_code>/*.txt  page text (git-ignored)
The output is evidence, not final values: for each school the text windows around "tuition" that contain a
dollar amount. Final values are read from this evidence and written to the tuition file (see docs/tuition_codebook.md).

Polite crawling: robots.txt is honoured, one request per host per second, identifying User-Agent, 8 schools at a time.
Usage: python3 -I scripts/collect_tuition.py [--codes codes.txt] [--limit N] [--workers 8]
"""
import argparse, csv, html, json, os, re, subprocess, sys, tempfile, threading, time, collections
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse

UA = "FLVoucherTuitionResearch/0.1 (academic project; contact via github.com/Miinsooo)"
RAW = "data/raw/school_sites/run1"
OUT = "data/processed/tuition_evidence.jsonl"
FREE = {"gmail.com","yahoo.com","aol.com","hotmail.com","outlook.com","icloud.com","comcast.net","bellsouth.net","att.net",
        "msn.com","live.com","me.com","sbcglobal.net","verizon.net","earthlink.net","mac.com","protonmail.com","cox.net",
        "windstream.net","embarqmail.com","centurylink.net","charter.net","frontier.com","netzero.net","juno.com","ymail.com",
        "gmx.com","mail.com","optonline.net","roadrunner.com","tampabay.rr.com","yahoo.co.uk","rocketmail.com"}
MAX_FETCH = 10
lock, host_last, robots_cache, write_lock = threading.Lock(), {}, {}, threading.Lock()

def throttle(host):
    with lock:
        wait = host_last.get(host, 0) + 1.0 - time.time()
        host_last[host] = max(time.time(), host_last.get(host, 0) + 1.0)
    if wait > 0: time.sleep(wait)

def curl(url, timeout=25, binary_ok=True):
    host = urlparse(url).netloc
    throttle(host)
    tmp = tempfile.NamedTemporaryFile(delete=False); tmp.close()
    try:
        p = subprocess.run(["curl", "-sSL", "-m", str(timeout), "--max-filesize", "8000000", "-A", UA, "-o", tmp.name,
                            "-w", "%{http_code}\t%{url_effective}\t%{content_type}", url], capture_output=True, text=True, errors="ignore")
        try: code, final, ctype = p.stdout.strip().split("\t", 2)
        except ValueError: return 0, url, "", b""
        data = open(tmp.name, "rb").read()
        return (int(code) if code.isdigit() else 0), final, ctype.lower(), data
    finally:
        os.unlink(tmp.name)

def robots_rules(base):
    host = urlparse(base).netloc
    if host in robots_cache: return robots_cache[host]
    code, _, ctype, data = curl(base + "/robots.txt", 10)
    rules = []
    if code == 200 and b"<html" not in data[:300].lower():
        star = False
        for line in data.decode("utf8", "ignore").splitlines():
            l = line.split("#")[0].strip()
            if l.lower().startswith("user-agent:"): star = l.split(":", 1)[1].strip() == "*"
            elif star and l.lower().startswith("disallow:"):
                v = l.split(":", 1)[1].strip()
                if v: rules.append(v)
    robots_cache[host] = rules
    return rules

def allowed(url, base):
    path = urlparse(url).path or "/"
    return not any(path.startswith(r) for r in robots_rules(base) if "*" not in r and "$" not in r)

def clean(h):
    h = re.sub(r"<(script|style|noscript).*?</\1>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>|</(p|div|li|tr|h\d)>", "\n", h, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", " ", h))
    return re.sub(r"[ \t\r\f\v]+", " ", re.sub(r"\n\s*\n+", "\n", t)).strip()

def pdf_text(data):
    f = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False); f.write(data); f.close()
    try:
        p = subprocess.run(["pdftotext", "-layout", "-l", "12", f.name, "-"], capture_output=True, text=True, errors="ignore", timeout=60)
        return p.stdout
    except Exception: return ""
    finally: os.unlink(f.name)

LINK = re.compile(r'<a\s[^>]*?href=["\']([^"\'#][^"\']*)["\'][^>]*>(.*?)</a>', re.S | re.I)
def score(text, href):
    s = (text + " " + href).lower()
    if "tuition" in s: return 0
    if re.search(r"\bfees?\b|cost|rates|investment|affordab", s): return 1
    if re.search(r"admission|apply|enroll|financial|scholarship|prospective", s): return 2
    return 9

def windows(text):
    out = []
    for m in re.finditer(r"tuition", text, re.I):
        a, b = max(0, m.start() - 300), min(len(text), m.end() + 450)
        w = text[a:b]
        if re.search(r"\$\s?\d", w): out.append((a, b))
    merged = []
    for a, b in out:
        if merged and a <= merged[-1][1]: merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else: merged.append((a, b))
    wins = [re.sub(r"\s+", " ", text[a:b]).strip() for a, b in merged]
    wins.sort(key=lambda w: -(len(re.findall(r"\$\s?\d", w)) + 3 * bool(re.search(r"grade|kinder|elementary|middle|high school|\bK\b", w, re.I))))
    return wins

def years(text):
    c = collections.Counter(re.sub(r"\s", "", y) for y in re.findall(r"20\d\d\s*[-–/]\s*(?:20)?\d\d", text))
    return [y for y, _ in c.most_common(3)]

def process(s):
    code = s["school_code"]; d = s["email_domain"]
    rec = {"school_code": code, "school_name": s["school_name"], "domain": d, "status": "", "home_url": "", "pages": [],
           "windows": [], "years": [], "no_price_hint": False, "notes": []}
    base = home = None
    for cand in (f"https://www.{d}", f"https://{d}", f"http://www.{d}"):
        code_, final, ctype, data = curl(cand)
        if code_ == 200 and len(data) > 300 and "html" in ctype:
            base, home, rec["home_url"] = f"{urlparse(final).scheme}://{urlparse(final).netloc}", data.decode("utf8", "ignore"), final
            break
    if not base:
        rec["status"] = "no_website"; return rec
    if not allowed(base + "/", base):
        rec["status"] = "blocked"; rec["notes"].append("robots disallows"); return rec
    odir = f"{RAW}/{code}"; os.makedirs(odir, exist_ok=True)
    texts, seen, fetched = [], {rec["home_url"]}, 0
    def add(url, ctype, data):
        t = pdf_text(data) if ("pdf" in ctype or url.lower().split("?")[0].endswith(".pdf")) else clean(data.decode("utf8", "ignore"))
        i = len(texts)
        open(f"{odir}/{i}.txt", "w").write(f"URL: {url}\n\n{t[:200000]}")
        texts.append((url, t))
        rec["pages"].append({"url": url, "chars": len(t), "pdf": "pdf" in ctype or url.lower().endswith(".pdf")})
    add(rec["home_url"], "html", home.encode())
    if len(texts[0][1]) < 300: rec["notes"].append("homepage text very short (JavaScript?)")
    def candidates(html_src, here):
        out = []
        for href, label in LINK.findall(html_src):
            href = href.strip()
            if href.startswith(("mailto:", "tel:", "javascript:")): continue
            u = urljoin(here, href).split("#")[0]
            p = urlparse(u)
            if not (p.netloc.replace("www.", "") == urlparse(base).netloc.replace("www.", "") or u.lower().endswith(".pdf")): continue
            sc = score(re.sub(r"<[^>]+>", " ", label), u)
            if sc < 9 and u not in seen: out.append((sc, u))
        out.sort(); res = []
        for _, u in out:
            if u not in res: res.append(u)
        return res
    queue = candidates(home, rec["home_url"])[:5]
    if not queue:
        queue = [base + p for p in ("/tuition", "/admissions", "/tuition-and-fees", "/admissions/tuition")]
    depth2_done = False
    while queue and fetched < MAX_FETCH:
        u = queue.pop(0)
        if u in seen: continue
        seen.add(u)
        if not allowed(u, base): rec["notes"].append(f"robots skips {urlparse(u).path}"); continue
        code_, final, ctype, data = curl(u); fetched += 1
        if code_ != 200 or not data: continue
        add(final, ctype, data)
        if not depth2_done and not any(windows(t) for _, t in texts[1:]) and "html" in ctype:
            more = [x for x in candidates(data.decode("utf8", "ignore"), final) if re.search(r"tuition|fee|cost|rate", x, re.I)][:3]
            queue = more + queue
            if more: depth2_done = True
    alltext = "\n".join(t for _, t in texts)
    best = []
    for url, t in texts:
        for w in windows(t): best.append((url, w))
    best.sort(key=lambda x: -(len(re.findall(r"\$\s?\d", x[1]))))
    seenw, total = set(), 0
    for url, w in best:
        if w[:80] in seenw or total > 2200: continue
        seenw.add(w[:80]); rec["windows"].append({"url": url, "text": w[:1100]}); total += len(w[:1100])
        if len(rec["windows"]) >= 4: break
    rec["years"] = years(alltext)
    rec["no_price_hint"] = bool(re.search(r"(call|contact|email|inquire|schedule).{0,60}(tuition|rates|pricing)|(tuition|rates).{0,60}(upon request|call|contact)", alltext, re.I))
    if rec["windows"]: rec["status"] = "tuition_evidence"
    elif re.search(r"tuition", alltext, re.I): rec["status"] = "tuition_word_no_amount"
    else: rec["status"] = "not_reached"
    return rec

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codes"); ap.add_argument("--limit", type=int); ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    schools = list(csv.DictReader(open("data/processed/fl_directory_2026.csv")))
    pool = [s for s in schools if int(s["enroll_total"]) > 0 and s["email_domain"] and s["email_domain"] not in FREE]
    if a.codes:
        want = set(open(a.codes).read().split()); pool = [s for s in pool if s["school_code"] in want]
    pool.sort(key=lambda s: int(s["school_code"]))
    done = set()
    if os.path.exists(a.out):
        done = {json.loads(l)["school_code"] for l in open(a.out) if l.strip()}
    todo = [s for s in pool if s["school_code"] not in done][: a.limit]
    print(f"pool {len(pool)}, done {len(done)}, to run {len(todo)}", flush=True)
    n = 0
    def run(s):
        try: r = process(s)
        except Exception as e: r = {"school_code": s["school_code"], "school_name": s["school_name"], "domain": s["email_domain"], "status": "error", "notes": [repr(e)[:200]], "windows": [], "pages": [], "years": []}
        with write_lock:
            with open(a.out, "a") as f: f.write(json.dumps(r) + "\n")
        return r["status"]
    with ThreadPoolExecutor(a.workers) as ex:
        for st in ex.map(run, todo):
            n += 1
            if n % 25 == 0: print(n, "done", flush=True)
    print("finished", n, flush=True)

if __name__ == "__main__":
    main()
