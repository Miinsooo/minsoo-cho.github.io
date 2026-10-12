"""Pilot: find tuition information on a random sample of Florida private school websites.

Input : data/processed/fl_directory_2026.csv (website guessed from the director/contact email domain)
Output: data/processed/pilot_tuition.csv ; fetched pages in data/raw/school_sites/<date>/ (git-ignored)
Polite: checks robots.txt, one request at a time, 1 s between requests, identifying User-Agent.
This is a feasibility test, not a finished measurement: amounts are raw text matches, not yet validated.
"""
import csv, collections, datetime, os, random, re, subprocess, sys, time, html
from urllib.parse import urljoin, urlparse

N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
SEED = 42
UA = "FLVoucherTuitionResearch/0.1 (academic pilot; contact via github.com/Miinsooo)"
FREE = {"gmail.com","yahoo.com","aol.com","hotmail.com","outlook.com","icloud.com","comcast.net","bellsouth.net","att.net",
        "msn.com","live.com","me.com","sbcglobal.net","verizon.net","earthlink.net","mac.com","protonmail.com","cox.net",
        "windstream.net","embarqmail.com","centurylink.net","charter.net","frontier.com","netzero.net","juno.com","ymail.com","gmx.com",
        "mail.com","optonline.net","roadrunner.com","tampabay.rr.com","bellsouth.net","comcast.net","yahoo.co.uk","rocketmail.com"}
OUT = f"data/raw/school_sites/{datetime.date.today()}"
os.makedirs(OUT, exist_ok=True)

def fetch(url, timeout=20):
    time.sleep(1)
    p = subprocess.run(["curl", "-sSL", "-m", str(timeout), "-A", UA, "-w", "\n%{http_code} %{url_effective}", url],
                       capture_output=True, text=True, errors="ignore")
    body, _, tail = p.stdout.rpartition("\n")
    try: code, final = tail.split(" ", 1)
    except ValueError: code, final = "0", url
    return int(code) if code.isdigit() else 0, final.strip(), body

def robots_ok(base):
    code, _, body = fetch(base + "/robots.txt", 10)
    if code != 200 or "<html" in body[:200].lower(): return True
    ua_all = False
    for line in body.splitlines():
        l = line.strip().lower()
        if l.startswith("user-agent:"): ua_all = l.split(":", 1)[1].strip() == "*"
        elif ua_all and l.startswith("disallow:") and l.split(":", 1)[1].strip() == "/": return False
    return True

def text_of(h):
    h = re.sub(r"<(script|style).*?</\1>", " ", h, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))

LINK = re.compile(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.S | re.I)
KEY = re.compile(r"tuition|fees?\b|admission|financial aid|apply|enroll", re.I)

def tuition_snips(t):
    out = []
    for m in re.finditer(r"tuition", t, re.I):
        w = t[max(0, m.start() - 120): m.end() + 220]
        if re.search(r"\$\s?\d", w): out.append(w)
    return out

schools = list(csv.DictReader(open("data/processed/fl_directory_2026.csv")))
dom_count = collections.Counter(s["email_domain"] for s in schools)
pool = [s for s in schools if int(s["enroll_total"]) > 0 and s["email_domain"] and s["email_domain"] not in FREE
        and dom_count[s["email_domain"]] <= 3]
random.Random(SEED).shuffle(pool)
sample = pool[:N]
print(f"pool {len(pool)}; sampling {len(sample)}")

rows = []
for i, s in enumerate(sample, 1):
    rec = {k: s[k] for k in ("school_code", "district", "school_name", "religious", "enroll_total", "email_domain")}
    rec.update(site="", home_status="", robots="", tuition_pages=0, dollar_snippets=0, amounts="", best_url="", note="")
    d = s["email_domain"]
    base = None
    for cand in (f"https://www.{d}", f"https://{d}"):
        code, final, body = fetch(cand)
        if code == 200 and len(body) > 500:
            base, home = f"{urlparse(final).scheme}://{urlparse(final).netloc}", body
            rec["site"], rec["home_status"] = final, code
            break
        rec["home_status"] = code
    if not base:
        rec["note"] = "no homepage at email domain"; rows.append(rec); print(i, s["school_name"][:40], "-> no site"); continue
    if not robots_ok(base):
        rec["robots"] = "disallow"; rec["note"] = "robots.txt disallows"; rows.append(rec); print(i, "robots"); continue
    rec["robots"] = "ok"
    open(f"{OUT}/{s['school_code']}_home.html", "w").write(home)
    links = []
    for href, label in LINK.findall(home):
        lab = re.sub(r"<[^>]+>", " ", label)
        if KEY.search(lab) or KEY.search(href):
            u = urljoin(base + "/", href.strip())
            if urlparse(u).netloc.endswith(urlparse(base).netloc.replace("www.", "")) and u not in links and not u.startswith("mailto"):
                links.append(u)
    links.sort(key=lambda u: (0 if re.search("tuition", u, re.I) else 1 if re.search("fee|financial", u, re.I) else 2))
    snips, amounts = tuition_snips(text_of(home)), set()
    for u in links[:4]:
        code, final, body = fetch(u)
        if code != 200: continue
        open(f"{OUT}/{s['school_code']}_{abs(hash(u)) % 10**6}.html", "w").write(body)
        t = text_of(body)
        if re.search("tuition", t, re.I): rec["tuition_pages"] += 1
        sn = tuition_snips(t)
        if sn and not rec["best_url"]: rec["best_url"] = final
        snips += sn
    for sn in snips: amounts.update(re.findall(r"\$\s?\d[\d,]*(?:\.\d\d)?", sn))
    rec["dollar_snippets"] = len(snips)
    rec["amounts"] = " ".join(sorted(amounts, key=lambda a: int(re.sub(r"\D", "", a.split(".")[0]) or 0))[:12])
    rows.append(rec)
    print(i, s["school_name"][:40], "| pages", rec["tuition_pages"], "| snippets", rec["dollar_snippets"])

with open("data/processed/pilot_tuition.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
n = len(rows)
print(f"\nsites found {sum(1 for r in rows if r['site'])}/{n}; robots disallow {sum(1 for r in rows if r['robots']=='disallow')}; "
      f"tuition $ found {sum(1 for r in rows if r['dollar_snippets'])}/{n}")
