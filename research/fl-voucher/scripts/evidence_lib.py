"""Helpers for reading saved school pages and coding tuition."""
import glob, json, re

RAWS = ["data/raw/school_sites/run2", "data/raw/school_sites/run1"]  # run2 (websites found by name) takes precedence
EVIDS = ["data/processed/tuition_evidence.jsonl", "data/processed/tuition_evidence2.jsonl"]  # later files override earlier ones

def load_evidence():
    import json, os
    out = {}
    for f in EVIDS:
        if os.path.exists(f):
            for l in open(f):
                r = json.loads(l); out[r["school_code"]] = r
    return list(out.values())
CUE = re.compile(r"tuition|annual|per year|/year|yearly|grade|kinder|\bK\b|\bk-|elementary|middle|high school|month|semester|quarter|full[- ]?day|pre-?k", re.I)
AMT = re.compile(r"\$\s?\d")

def load_pages(code):
    pages = []
    files = []
    for raw in RAWS:
        files = glob.glob(f"{raw}/{code}/*.txt")
        if files: break
    for f in sorted(files, key=lambda p: int(p.rsplit("/", 1)[1].split(".")[0])):
        txt = open(f, errors="ignore").read()
        url, _, body = txt.partition("\n\n")
        pages.append((url.replace("URL: ", "", 1), body))
    return pages

def page_score(body):
    lines = body.split("\n")
    return sum(1 for i, l in enumerate(lines) if AMT.search(l) and re.search("tuition", " ".join(lines[max(0, i - 2): i + 2]), re.I))

def best_page(code):
    pages = load_pages(code)
    pages = [(page_score(b), u, b) for u, b in pages]
    pages.sort(key=lambda x: -x[0])
    return pages[0] if pages and pages[0][0] > 0 else (0, "", "")

def dollar_lines(body, maxlines=18, width=170):
    raw = [re.sub(r"\s+", " ", l).strip() for l in body.split("\n")]
    lines = [l for l in raw if l]
    keep, seen = [], set()
    for i, l in enumerate(lines):
        near = " ".join(lines[max(0, i - 3): i + 2])
        if AMT.search(l) and CUE.search(near):
            s = l
            if len(s) < 28:  # bare amount: attach the label lines above it
                lab = [x for x in lines[max(0, i - 2): i] if not AMT.fullmatch(x) and len(x) < 90]
                s = " / ".join(lab + [l])
            if len(s) > width:
                m = AMT.search(s); a = max(0, m.start() - width // 2); s = ("…" if a else "") + s[a:a + width]
            if s not in seen: seen.add(s); keep.append(s)
        if len(keep) >= maxlines: break
    return keep

def years_in(body):
    import collections
    c = collections.Counter(re.sub(r"\s", "", y) for y in re.findall(r"20\d\d\s*[-–/]\s*(?:20)?\d\d", body))
    return [y for y, _ in c.most_common(3)]
