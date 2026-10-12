"""Render school sites in headless Chromium (JavaScript executed) and look for tuition amounts.

For schools whose plain crawl found no tuition page or no amount (not_reached, tuition_word_no_amount).
Input : home_url from the earlier evidence files
Output: data/raw/school_sites/run5/<code>/*.txt (git-ignored) ; data/processed/tuition_evidence5.jsonl (same fields as before)
Per school: render the homepage, take internal links that look like tuition/admissions/fees pages from the rendered DOM,
render up to 4 of them. robots.txt honoured, 1 navigation per second per host, identifying User-Agent, no certificate checks disabled.
Usage: python3 -I scripts/render_crawl.py [--status not_reached,tuition_word_no_amount] [--limit N] [--workers 6]
"""
import argparse, json, os, re, subprocess, sys, threading, time, collections
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
sys.path.insert(0, "scripts")
import collect_tuition as C
import evidence_lib as E

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
PROXY = os.environ.get("HTTPS_PROXY", "")
OUT = "data/processed/tuition_evidence5.jsonl"; RAW5 = "data/raw/school_sites/run5"
KEY = re.compile(r"tuition|fees?\b|afford|financ|admission|enroll|apply|rates|pricing", re.I)
wl = threading.Lock()

def render(url, budget=9000):
    host = urlparse(url).netloc
    C.throttle(host)
    try:
        p = subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", f"--proxy-server={PROXY}",
                            "--user-agent=" + C.UA, f"--virtual-time-budget={budget}", "--dump-dom", url],
                           capture_output=True, timeout=75, errors="ignore", text=True)
        return p.stdout
    except Exception:
        return ""

def run(rec0):
    code, home = rec0["school_code"], rec0["home_url"]
    base = f"{urlparse(home).scheme}://{urlparse(home).netloc}"
    rec = {"school_code": code, "school_name": rec0["school_name"], "domain": rec0["domain"], "status": "", "home_url": home,
           "pages": [], "windows": [], "years": [], "no_price_hint": False, "notes": ["rendered"]}
    os.makedirs(f"{RAW5}/{code}", exist_ok=True)
    if not C.allowed(home, base): rec["status"] = "blocked"; rec["notes"].append("robots"); 
    else:
        dom = render(home); texts = []
        def keep(u, d):
            t = C.clean(d); i = len(texts)
            open(f"{RAW5}/{code}/{i}.txt", "w").write(f"URL: {u}\n\n{t[:200000]}")
            texts.append((u, t)); rec["pages"].append({"url": u, "chars": len(t), "pdf": False})
        if dom: keep(home, dom)
        links = []
        for h in re.findall(r'href=["\']([^"\'#]+)["\']', dom):
            u = urljoin(home, h.replace("&amp;", "&"))
            if urlparse(u).netloc.replace("www.", "") == urlparse(base).netloc.replace("www.", "") and KEY.search(u) and u != home and not re.search(r"\.(jpg|png|css|js)$", u, re.I):
                if u not in links: links.append(u)
        links.sort(key=lambda u: (0 if re.search(r"tuition|fee", u, re.I) else 1 if re.search(r"afford|financ|rates", u, re.I) else 2, len(u)))
        pdfs = [u for u in links if u.lower().endswith(".pdf")]
        for u in [x for x in links if not x.lower().endswith(".pdf")][:4]:
            if C.allowed(u, base):
                d = render(u)
                if d: keep(u, d)
        for u in pdfs[:2]:   # PDFs are not rendered; fetched as before
            if C.allowed(u, base):
                c, f, ct, data = C.curl(u, 30)
                if c == 200 and data[:4] == b"%PDF":
                    t = C.pdf_text(data); i = len(texts)
                    open(f"{RAW5}/{code}/{i}.txt", "w").write(f"URL: {f}\n\n{t[:200000]}")
                    texts.append((f, t)); rec["pages"].append({"url": f, "chars": len(t), "pdf": True})
        alltext = "\n".join(t for _, t in texts)
        best = [(u, w) for u, t in texts for w in C.windows(t)]
        best.sort(key=lambda x: -(len(re.findall(r"\$\s?\d", x[1]))))
        sw, tot = set(), 0
        for u, w in best:
            if w[:80] in sw or tot > 2200: continue
            sw.add(w[:80]); rec["windows"].append({"url": u, "text": w[:1100]}); tot += len(w[:1100])
            if len(rec["windows"]) >= 4: break
        rec["years"] = C.years(alltext)
        rec["status"] = "tuition_evidence" if rec["windows"] else ("tuition_word_no_amount" if re.search("tuition", alltext, re.I) else "not_reached")
    with wl: open(OUT, "a").write(json.dumps(rec) + "\n")
    return rec["status"]

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--status", default="not_reached,tuition_word_no_amount")
    ap.add_argument("--limit", type=int); ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    want = set(a.status.split(","))
    todo0 = [r for r in E.load_evidence() if r["status"] in want and r.get("home_url")]
    done = {json.loads(l)["school_code"] for l in open(OUT)} if os.path.exists(OUT) else set()
    todo = [r for r in todo0 if r["school_code"] not in done][: a.limit]
    print(len(todo0), "candidates;", len(todo), "to do", flush=True)
    with ThreadPoolExecutor(a.workers) as ex: print(dict(collections.Counter(ex.map(run, todo))))
