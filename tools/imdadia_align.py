#!/usr/bin/env python3
"""Imdadia line structure, second pass: one alignment over the whole Quran.

imdadia_lines.py reads every ruled line of the scan (build/imdadia_ocr.json).
Here the whole word stream of data/pages.js is cut into those scanned lines in
a single dynamic programme, so an Imdadia page may start or end on other words
than the QUL page with the same number. Bismillah / surah-heading lines are
recognised from what was read and never take Quran words.

Output: data/line_pattern_imdadia.csv   (one row per printed line)
        data/imdadia_lines.js           (IMD = per page: "s", "b", "x" or the
                                         number of stream items on the line)

    python tools/imdadia_align.py
"""
from __future__ import annotations

import csv
import json
import os
import sys

from rapidfuzz.distance import Levenshtein

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imdadia_lines import CACHE, OUT, ROOT, load_pages, norm  # noqa: E402

JS_OUT = os.path.join(ROOT, "data", "imdadia_lines.js")
FIRST = 3                 # pages 1-2 are the ornamental opening pages: kept as in pages.js
LAST = 610
BAND = 90                 # words the alignment may drift from the QUL position
NONTEXT = 6
BISM = norm("بسم الله الرحمن الرحيم")
HEAD_KEYS = ("اياتها", "اياتما", "سوره", "سوده", "سودت", "ركوع", "ذكوع", "مكي", "مدني")
INF = 10 ** 9


def stream(qul):
    """Global word list. Each word: [text, n_marks_after, page]; plus surah
    starts {word index: [line types of the heading, e.g. 's','b']} and the
    word index where each QUL page starts."""
    words, starts, pstart = [], {}, {}
    for k in range(1, LAST + 1):
        pstart[k] = len(words)
        for l in qul[str(k)]["lines"]:
            if "w" not in l:
                starts.setdefault(len(words), []).append(l["t"])
                continue
            for t in l["w"].split():
                if t[0] == "#":
                    words[-1][1] += 1
                elif t[0] != "@":
                    words.append([t, 0, k])
    pstart[LAST + 1] = len(words)
    return words, starts, pstart


def is_bism(o):
    return len(o) <= 26 and Levenshtein.distance(o, BISM) <= 6


def is_head(o):
    return sum(1 for k in HEAD_KEYS if k in o) >= 2


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    qul = load_pages()
    ocr = json.load(open(CACHE, encoding="utf-8"))
    words, starts, pstart = stream(qul)
    W = [norm(w[0]) for w in words]
    n = len(W)
    pre = [0]
    for w in W:
        pre.append(pre[-1] + len(w))
    sset = sorted(starts)

    # all scanned lines in order: (page, line no, raw, normalised, expected word position)
    L = []
    for k in range(FIRST, LAST + 1):
        rows = ocr[str(k)]
        a, b = pstart[k], pstart[k + 1]
        for r, raw in enumerate(rows):
            L.append((k, r + 1, raw, norm(raw), a + (b - a) * r / len(rows)))
    m = len(L)

    import bisect

    def crosses(i, j):                        # a surah start strictly inside (i, j)?
        p = bisect.bisect_right(sset, i)
        return p < len(sset) and sset[p] < j

    cur = {pstart[FIRST]: 0}
    backs = []
    for li, (k, r, raw, o, exp) in enumerate(L):
        lo, hi = int(exp) - BAND, int(exp) + BAND + 12
        nxt, back = {}, {}
        bism, head = is_bism(o), is_head(o)
        for i, c0 in cur.items():
            # not Quran text
            c = c0 + (0.5 if (bism or head) else NONTEXT + len(o) * 0.5)
            if i not in starts and i != n and (bism or head):
                c += 4                         # headings belong at a surah start
            if c < nxt.get(i, INF):
                nxt[i] = c
                back[i] = (i, "other")
            if bism or i >= n:
                continue
            for j in range(i + 1, min(n, i + 32) + 1):
                if j > hi:
                    break
                if crosses(i, j):
                    break
                ln = pre[j] - pre[i]
                if ln > len(o) * 1.9 + 10:
                    break
                if ln < len(o) * 0.4 - 5 or j < lo:
                    continue
                c = c0 + Levenshtein.distance("".join(W[i:j]), o) + (3 if head else 0)
                if c < nxt.get(j, INF):
                    nxt[j] = c
                    back[j] = (i, "text")
        if not nxt:
            print("alignment broke at page", k, "line", r)
            return
        best = min(nxt.values())                # keep only plausible states (band + beam)
        cur = {i: c for i, c in nxt.items() if c <= best + 60 and (i >= lo - 12 or i == n)}
        backs.append(back)
    if n not in cur:
        print("alignment did not reach the end; best end", max(cur), "of", n)
        return
    print("total misfit %.3f per letter" % (cur[n] / pre[n]))

    # trace back
    cuts = [None] * m
    i = n
    for li in range(m - 1, -1, -1):
        pi, kind = backs[li][i]
        cuts[li] = (pi, i, kind)
        i = pi

    def dist(li, a, b):
        return Levenshtein.distance("".join(W[a:b]), L[li][3])

    rows, js = [], {}
    # pages 1-2 straight from pages.js
    for k in range(1, FIRST):
        pg = []
        for l in qul[str(k)]["lines"]:
            if "w" not in l:
                pg.append(l["t"])
            else:
                t = [x for x in l["w"].split() if x[0] != "@"]
                pg.append(len(t))
                ws = [x for x in t if x[0] != "#"]
                rows.append([k + 1, k, len(pg), "text", ws[0], ws[-1], " ".join(ws), 99, "(opening page, from pages.js)"])
                continue
            rows.append([k + 1, k, len(pg), "other", "", "", "", "", ""])
        js[k] = pg

    # the two opening pages as printed: heading, then the bismillah line and 7 lines of text
    js[1] = ["s", 5, 5, 5, 5, 4, 4, 4, 4]
    js[2] = ["s", "b", 7, 4, 4, 4, 4, 5, 4]
    rows = []
    q = 0
    for k in (1, 2):
        for r, e in enumerate(js[k]):
            if not isinstance(e, int):
                rows.append([k + 1, k, r + 1, "other", "", "", "", "", ""])
                continue
            ws, got = [], 0
            while got < e:
                ws.append(words[q][0]); got += 1 + words[q][1]; q += 1
            rows.append([k + 1, k, r + 1, "text", ws[0], ws[-1], " ".join(ws), 99, "(opening page, set by hand from the scan)"])

    pending = {}            # surah start -> heading line types still to place
    for s in starts:
        if s >= pstart[FIRST]:
            pending[s] = list(starts[s])
    problems = []
    for li, (k, r, raw, o, exp) in enumerate(L):
        a, b, kind = cuts[li]
        pg = js.setdefault(k, [])
        if kind == "other":
            t = pending[a].pop(0) if pending.get(a) else "x"
            pg.append(t)
            rows.append([k + 1, k, r, "other", "", "", "", "", raw])
            continue
        if pending.get(a):                     # heading had no line of its own
            problems.append((k, r, "surah heading without its own line: " + ",".join(pending[a])))
            pg.extend(pending[a])
            pending[a] = []
        pg.append(sum(1 + words[q][1] for q in range(a, b)))
        mg = 99
        if li + 1 < m and cuts[li + 1][2] == "text":
            e = cuts[li + 1][1]
            base = dist(li, a, b) + dist(li + 1, b, e)
            alts = []
            if b - 1 > a:
                alts.append(dist(li, a, b - 1) + dist(li + 1, b - 1, e))
            if b + 1 < e and not crosses(a, b + 1):
                alts.append(dist(li, a, b + 1) + dist(li + 1, b + 1, e))
            if alts:
                mg = min(alts) - base
        ws = [words[q][0] for q in range(a, b)]
        rows.append([k + 1, k, r, "text", ws[0], ws[-1], " ".join(ws), mg, raw])

    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["imdadia_page", "pdf_index", "line", "type", "first_word", "last_word", "words",
                    "confidence_margin", "ocr_reading"])
        w.writerows(rows)
    flag = {}
    for r in rows:
        if r[3] == "text" and isinstance(r[7], int) and r[7] < 2:
            flag.setdefault(str(r[1]), []).append(r[2] - 1)
    first_cut = {}
    for c, l in zip(cuts, L):
        first_cut.setdefault(l[0], c[0])
    for k in range(FIRST, LAST + 1):
        if first_cut[k] != pstart[k] or "x" in js[k]:
            flag.setdefault(str(k), [])
            if 0 not in flag[str(k)]:
                flag[str(k)].insert(0, 0)
    with open(JS_OUT, "w", encoding="utf-8") as f:
        f.write("// Hafizi Imdadia (Emdadia Library, 15 lines): what stands on every printed line.\n"
                "// Per page: \"s\" surah heading, \"b\" bismillah, \"x\" empty/other, or the number of\n"
                "// stream items (words and ayah circles) on that line. Made by tools/imdadia_align.py\n"
                "var IMD = " + json.dumps({str(k): js[k] for k in sorted(js)}, separators=(",", ":")) + ";\n"
                "// lines (0-based) whose end should be checked against the scan\n"
                "var IMD_UNSURE = " + json.dumps(flag, separators=(",", ":")) + ";\n")

    text = [r for r in rows if r[3] == "text"]
    unsure = [r for r in text if isinstance(r[7], int) and r[7] < 2]
    moved = [k for k in range(FIRST, LAST + 1)
             if next(c[0] for c, l in zip(cuts, L) if l[0] == k) != pstart[k]]
    odd = [k for k in js if len(js[k]) != 15 and k >= FIRST]
    xs = [k for k in js if "x" in js[k]]
    left = [s for s, v in pending.items() if v]
    print("lines %d  text %d  unsure %d on %d pages" % (len(rows), len(text), len(unsure), len({r[1] for r in unsure})))
    print("pages starting on another word than QUL:", len(moved), moved[:80])
    print("pages not 15 lines:", odd)
    print("pages with an unexplained non-text line:", xs)
    print("problems:", problems, "headings never placed:", left)
    print("items", sum(v for pg in js.values() for v in pg if isinstance(v, int)),
          "expected", n + sum(w[1] for w in words))
    print("wrote", OUT, "and", JS_OUT)


if __name__ == "__main__":
    main()
