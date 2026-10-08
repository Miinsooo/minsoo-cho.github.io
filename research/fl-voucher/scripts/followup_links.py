"""Follow tuition-related links (PDF or page) from the pages of schools coded `unclear`, save text, find amounts.

Input : data/processed/fl_tuition_2026.csv (status unclear) and the saved first-crawl pages (url list only)
Output: data/raw/school_sites/run3/<school_code>/*.txt (git-ignored) ; data/processed/tuition_evidence3.jsonl
For each school the saved page URLs are re-fetched as HTML; links whose text or address mentions tuition, fees,
rates or pricing (and PDFs on the same site) are fetched (PDF through pdftotext). Polite: robots.txt, 1 req/s/host.
Usage: python3 -I scripts/followup_links.py [--workers 8] [--limit N]
"""
import argparse, csv, json, os, re, subprocess, sys, tempfile, threading
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
sys.path.insert(0, "scripts")
import collect_tuition as C, evidence_lib as E

OUT = "data/processed/tuition_evidence3.jsonl"  # shared by all statuses; schools done once are skipped
RAW3 = "data/raw/school_sites/run3"
KEY = re.compile(r"tuition|fee|rate|pricing|cost|afford|schedule", re.I)
wl = threading.Lock()

def links(url, html):
    out = []
    for m in re.finditer(r'<a\b[^>]*?href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', html, re.S | re.I):
        href, txt = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
        full = urljoin(url, href.replace("&amp;", "&"))
        if urlparse(full).scheme not in ("http", "https"): continue
        isdoc = re.search(r"\.(pdf)(\?|$)", full, re.I) is not None
        if (KEY.search(txt) or KEY.search(full)) and (isdoc or KEY.search(txt)): out.append((full, isdoc))
    return out

def run(s):
    code = s["school_code"]
    pages = E.load_pages(code)
    base_hosts = {urlparse(u).netloc.replace("www.", "") for u, _ in pages}
    seen, got = set(), []
    for u, _ in pages[:4]:
        c, final, ctype, data = C.curl(u, 20)
        if c != 200 or b"%PDF" in data[:5]: continue
        for full, isdoc in links(final, data.decode("utf8", "ignore")):
            if full in seen or len(seen) >= 8: continue
            host = urlparse(full).netloc.replace("www.", "")
            if not isdoc and host not in base_hosts: continue
            base = f"{urlparse(full).scheme}://{urlparse(full).netloc}"
            if not C.allowed(full, base): continue
            seen.add(full)
            c2, f2, ct2, d2 = C.curl(full, 30)
            if c2 != 200: continue
            if b"%PDF" in d2[:5]:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf"); tmp.write(d2); tmp.close()
                p = subprocess.run(["pdftotext", "-layout", tmp.name, "-"], capture_output=True, text=True, errors="ignore"); os.unlink(tmp.name)
                text = p.stdout
            else:
                text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "\n", re.sub(r"<(script|style).*?</\1>", " ", d2.decode("utf8", "ignore"), flags=re.S | re.I)))
            if len(re.findall(r"\$\s?\d", text)) >= 1: got.append((f2, text))
    if got:
        os.makedirs(f"{RAW3}/{code}", exist_ok=True)
        for i, (u, t) in enumerate(got):
            open(f"{RAW3}/{code}/{i}.txt", "w").write("URL: " + u + "\n\n" + t)
    with wl:
        open(OUT, "a").write(json.dumps({"school_code": code, "n_links": len(seen), "n_docs": len(got)}) + "\n")
    return len(got)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=8); ap.add_argument("--limit", type=int)
    ap.add_argument("--status", default="unclear")
    a = ap.parse_args()
    if a.status == "unclear":
        rows = [r for r in csv.DictReader(open("data/processed/fl_tuition_2026.csv")) if r["status"] == a.status]
    else:  # statuses of the directory file, e.g. tuition_word_no_amount, not_reached has no saved pages
        rows = [r for r in csv.DictReader(open("data/processed/fl_directory_tuition_2026.csv")) if r["tuition_status"] == a.status]
    done = set()
    if os.path.exists(OUT): done = {json.loads(l)["school_code"] for l in open(OUT)}
    todo = [r for r in rows if r["school_code"] not in done][: a.limit]
    print(len(rows), "schools,", len(todo), "to do", flush=True)
    os.makedirs(RAW3, exist_ok=True)
    with ThreadPoolExecutor(a.workers) as ex:
        n = sum(1 for k in ex.map(run, todo) if k)
    print("schools with new documents:", n)
