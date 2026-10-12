"""Second, deeper pass over schools whose first crawl reached the site but found no tuition word (status not_reached).

Input : home_url of those schools in the first-crawl evidence files
Output: data/raw/school_sites/run4/<code>/*.txt (git-ignored) ; data/processed/tuition_evidence4.jsonl (same fields as before)
Extra pages tried: sitemap.xml (urls mentioning tuition, fees, admission, afford, financial, enroll, apply), common paths,
and up to 12 internal links in two levels. Polite: robots.txt, 1 request per second per host, identifying User-Agent.
Usage: python3 -I scripts/recrawl_not_reached.py [--workers 8] [--limit N]
"""
import argparse, json, os, re, sys, threading
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
sys.path.insert(0, "scripts")
import collect_tuition as C
import evidence_lib as E

OUT = "data/processed/tuition_evidence4.jsonl"; RAW4 = "data/raw/school_sites/run4"
KEY = re.compile(r"tuition|fees?\b|cost|afford|financ|admission|enroll|apply|rates|pricing|register", re.I)
PATHS = ["/tuition", "/tuition-and-fees", "/tuition-fees", "/admissions/tuition", "/admissions/tuition-and-fees", "/admissions",
         "/financial-aid", "/enrollment", "/apply", "/tuition-financial-aid", "/admission", "/fees"]
wl = threading.Lock()

def run(rec0):
    code = rec0["school_code"]; home = rec0["home_url"]
    base = f"{urlparse(home).scheme}://{urlparse(home).netloc}"
    rec = {"school_code": code, "school_name": rec0["school_name"], "domain": rec0["domain"], "status": "", "home_url": home,
           "pages": [], "windows": [], "years": [], "no_price_hint": False, "notes": []}
    cand, seen = [], {home}
    c, f, ct, d = C.curl(base + "/sitemap.xml", 15)
    if c == 200 and b"<loc>" in d[:200000]:
        for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", d.decode("utf8", "ignore")):
            if KEY.search(urlparse(u).path) and urlparse(u).netloc.replace("www.", "") == urlparse(base).netloc.replace("www.", ""): cand.append(u)
    cand = sorted(cand, key=lambda u: (0 if re.search(r"tuition|fee", u, re.I) else 1, len(u)))[:8]
    c, f, ct, d = C.curl(home, 20)
    if c == 200:
        for href in re.findall(r'href=["\']([^"\'#]+)["\']', d.decode("utf8", "ignore")):
            u = urljoin(f, href.replace("&amp;", "&"))
            if urlparse(u).netloc.replace("www.", "") == urlparse(base).netloc.replace("www.", "") and KEY.search(u) and u not in cand: cand.append(u)
    cand += [base + p for p in PATHS]
    texts, fetched, queue = [], 0, []
    for u in cand:
        if u not in queue: queue.append(u)
    os.makedirs(f"{RAW4}/{code}", exist_ok=True)
    while queue and fetched < 18:
        u = queue.pop(0)
        if u in seen: continue
        seen.add(u)
        if not C.allowed(u, base): continue
        c, f, ct, d = C.curl(u, 25); fetched += 1
        if c != 200 or not d: continue
        isdoc = "pdf" in ct or f.lower().split("?")[0].endswith(".pdf")
        t = C.pdf_text(d) if isdoc else C.clean(d.decode("utf8", "ignore"))
        if len(t) < 200: continue
        i = len(texts)
        open(f"{RAW4}/{code}/{i}.txt", "w").write(f"URL: {f}\n\n{t[:200000]}")
        texts.append((f, t)); rec["pages"].append({"url": f, "chars": len(t), "pdf": isdoc})
        if not isdoc and fetched <= 6:   # one more level from tuition-looking pages
            for href in re.findall(r'href=["\']([^"\'#]+)["\']', d.decode("utf8", "ignore")):
                u2 = urljoin(f, href.replace("&amp;", "&"))
                if (re.search(r"tuition|fee|rates|pricing", u2, re.I) and (urlparse(u2).netloc.replace("www.", "") == urlparse(base).netloc.replace("www.", "") or u2.lower().endswith(".pdf"))) and u2 not in seen:
                    queue.append(u2)
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
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=8); ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    ev = E.load_evidence()
    todo0 = [r for r in ev if r["status"] == "not_reached" and r.get("home_url")]
    done = set()
    if os.path.exists(OUT): done = {json.loads(l)["school_code"] for l in open(OUT)}
    todo = [r for r in todo0 if r["school_code"] not in done][: a.limit]
    print(len(todo0), "not_reached;", len(todo), "to do", flush=True)
    import collections
    with ThreadPoolExecutor(a.workers) as ex: cnt = collections.Counter(ex.map(run, todo))
    print(dict(cnt))
