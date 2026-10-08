"""Guess school websites from the school name and verify them against the page text.

Input : data/processed/fl_directory_2026.csv ; schools to look for are selected with --which
Output: data/processed/website_guess.csv (school_code, url, score, matched), only verified hits
For each school: build candidate domains from the name (full name, without generic words, saint/st variants,
acronym), try each with common endings (.org .com .net .school .edu .academy .us), fetch the homepage, and accept
it only when the page text contains most of the school's distinctive name words AND the city, ZIP or "Florida".
Polite: one request at a time per host (hosts are all different), identifying User-Agent.
Usage: python3 -I scripts/find_websites.py [--limit N] [--which nodomain|nosite|both] [--workers 16] [--sample]
"""
import argparse, csv, html, json, os, random, re, subprocess, tempfile, threading
from concurrent.futures import ThreadPoolExecutor

UA = "FLVoucherTuitionResearch/0.1 (academic project; contact via github.com/Miinsooo)"
OUT = "data/processed/website_guess.csv"
STOP = {"inc", "llc", "corp", "the", "of", "at", "and", "a", "an", "in", "for", "co", "ltd", "school", "schools"}
GENERIC = STOP | {"academy", "academies", "christian", "catholic", "private", "preparatory", "prep", "learning", "center", "centre",
                  "elementary", "middle", "high", "montessori", "day", "country", "episcopal", "lutheran", "baptist", "community"}
TLDS = [".org", ".com", ".net", ".school", ".edu", ".academy", ".us"]
lock = threading.Lock()

def curl(url, timeout=8):
    tmp = tempfile.NamedTemporaryFile(delete=False); tmp.close()
    try:
        p = subprocess.run(["curl", "-sSL", "-m", str(timeout), "--max-filesize", "3000000", "-A", UA, "-o", tmp.name,
                            "-w", "%{http_code}\t%{url_effective}\t%{content_type}", url], capture_output=True, text=True, errors="ignore")
        try: code, final, ctype = p.stdout.strip().split("\t", 2)
        except ValueError: return 0, url, ""
        return (int(code) if code.isdigit() else 0), final, open(tmp.name, "rb").read().decode("utf8", "ignore")
    finally: os.unlink(tmp.name)

def words(name):
    n = name.lower().replace("&", " and ").replace("'", "").replace("’", "")
    n = re.sub(r"\bst\.?\b", "saint", n)
    return re.findall(r"[a-z0-9]+", n)

def slugs(name):
    w = words(name)
    core = [x for x in w if x not in STOP]
    nogen = [x for x in core if x not in GENERIC]
    out = []
    def add(s):
        s = re.sub(r"[^a-z0-9]", "", s)
        if 3 <= len(s) <= 40 and s not in out: out.append(s)
    add("".join(core)); add("".join(nogen));
    st = ["st" if x == "saint" else x for x in core]; add("".join(st)); add("".join([x for x in st if x not in GENERIC]))
    if nogen: add("".join(nogen) + "school"); add("".join(nogen) + "academy")
    ac = "".join(x[0] for x in core)
    if len(ac) >= 3: add(ac); add(ac + "school"); add(ac + "fl")
    return out[:9]

def clean(h):
    h = re.sub(r"<(script|style|noscript).*?</\1>", " ", h, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).lower()

EDU = re.compile(r"\b(students?|enroll(?:ment)?|admissions?|tuition|kindergarten|pre-?k|grades?|curriculum|classroom|teachers?|parents|campus)\b")

def verify(s, text):
    """Accept only when the name words, the school's own city or ZIP, and school vocabulary all appear."""
    toks = [x for x in words(s["school_name"]) if x not in STOP]
    distinct = [x for x in toks if x not in GENERIC] or toks
    if not distinct or len(text) < 300: return 0.0
    hit = sum(1 for x in distinct if (x in text or ("st" == x and "saint" in text)))
    cov = hit / len(distinct)
    city = re.sub(r"^(ft\.?|fort)\s", "", s["city"].lower().strip())
    city_ok = bool(city) and (city in text or city.replace("saint", "st") in text or city.replace("port saint", "port st") in text)
    zip_ok = bool(s["zip"]) and s["zip"][:5] in text
    edu = len(set(EDU.findall(text)))
    return round(cov, 2) if (city_ok or zip_ok) and edu >= 3 else 0.0

def find(s):
    for sl in slugs(s["school_name"]):
        for tld in TLDS:
            code, final, body = curl(f"https://{sl}{tld}")
            if code == 200 and len(body) > 500:
                sc = verify(s, clean(body))
                if sc >= 0.7: return {"school_code": s["school_code"], "url": final, "score": sc, "matched": f"{sl}{tld}"}
    return None

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int); ap.add_argument("--which", default="both")
    ap.add_argument("--workers", type=int, default=16); ap.add_argument("--sample", action="store_true"); ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    schools = list(csv.DictReader(open("data/processed/fl_directory_2026.csv")))
    status = {}
    if os.path.exists("data/processed/tuition_evidence.jsonl"):
        for l in open("data/processed/tuition_evidence.jsonl"):
            r = json.loads(l); status[r["school_code"]] = r["status"]
    FREE = {"gmail.com","yahoo.com","aol.com","hotmail.com","outlook.com","icloud.com","comcast.net","bellsouth.net","att.net","msn.com","live.com","me.com","sbcglobal.net","verizon.net","earthlink.net","mac.com","protonmail.com","cox.net","windstream.net","embarqmail.com","centurylink.net","charter.net","frontier.com","netzero.net","juno.com","ymail.com","gmx.com","mail.com","optonline.net","roadrunner.com","tampabay.rr.com","yahoo.co.uk","rocketmail.com"}
    def nodomain(s): return int(s["enroll_total"]) > 0 and (not s["email_domain"] or s["email_domain"] in FREE)
    def nosite(s): return status.get(s["school_code"]) == "no_website"
    pool = [s for s in schools if (a.which in ("nodomain", "both") and nodomain(s)) or (a.which in ("nosite", "both") and nosite(s))]
    done = set()
    if os.path.exists(a.out): done = {r["school_code"] for r in csv.DictReader(open(a.out))}
    tried = set()
    if os.path.exists(a.out + ".tried"): tried = set(open(a.out + ".tried").read().split())
    todo = [s for s in pool if s["school_code"] not in tried]
    if a.sample: random.Random(1).shuffle(todo)
    todo = todo[: a.limit]
    print(f"pool {len(pool)}, already tried {len(tried)}, to run {len(todo)}", flush=True)
    new = not os.path.exists(a.out)
    def run(s):
        r = find(s)
        with lock:
            open(a.out + ".tried", "a").write(s["school_code"] + "\n")
            if r:
                with open(a.out, "a", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=["school_code", "url", "score", "matched"])
                    if os.path.getsize(a.out) == 0 if os.path.exists(a.out) else True: w.writeheader()
                    w.writerow(r)
        return r
    hits = 0
    with ThreadPoolExecutor(a.workers) as ex:
        for i, r in enumerate(ex.map(run, todo), 1):
            hits += bool(r)
            if i % 50 == 0: print(i, "tried;", hits, "found", flush=True)
    print("finished;", hits, "found of", len(todo), flush=True)
