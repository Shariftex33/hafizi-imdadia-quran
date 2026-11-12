#!/usr/bin/env python3
"""Read the line structure of the Emdadia (Imdadia) 15-line Hafezi Quran.

Input : Hafezi-Quran-Emdadia-Library-IslamBangla.Com.pdf (page scans, no text)
        data/pages.js (QUL Indo-Pak text; its 15-line pages start and end on
        the same words as the Emdadia pages: PDF page index == QUL page number)
Output: data/line_pattern_imdadia.csv  (page, line, first/last word, words,
        confidence) and build/imdadia_ocr.json (cached raw OCR per line).

How: each page's ruled line boxes are found, every box is read with EasyOCR
(rough, ~80 % of letters right), and the known words of that page are split
into the lines by dynamic programming so that every line's text is as close
as possible to what was read there. Only the split points are taken from
the scan; the text itself always comes from pages.js.

    python tools/imdadia_lines.py 20 21 22        # some PDF page indexes
    python tools/imdadia_lines.py --all
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys

import cv2
import fitz
import numpy as np
from rapidfuzz.distance import Levenshtein

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "Hafezi-Quran-Emdadia-Library-IslamBangla.Com.pdf")
PAGES_JS = os.path.join(ROOT, "data", "pages.js")
CACHE = os.path.join(ROOT, "build", "imdadia_ocr.json")
OUT = os.path.join(ROOT, "data", "line_pattern_imdadia.csv")
DPI = 200
NONTEXT_COST = 6          # cost of calling a scanned line "not Quran text" (header / bismillah box)

_MAP = str.maketrans({"آ": "ا", "أ": "ا", "إ": "ا", "ٱ": "ا", "ى": "ي", "ی": "ي", "ئ": "ي", "ؤ": "و",
                      "ة": "ه", "ک": "ك", "ہ": "ه", "ھ": "ه", "ۃ": "ه", "ے": "ي"})
_LETTERS = set("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")


def norm(s: str) -> str:
    return "".join(c for c in s.translate(_MAP) if c in _LETTERS)


def load_pages():
    s = open(PAGES_JS, encoding="utf-8").read()
    j, _ = json.JSONDecoder().raw_decode(s[s.index("{"):])
    return j


def page_words(pg):
    """[(word, ayah_end_or_None)], and the QUL line types for reference."""
    words = []
    page_words.starts = set()          # word indexes where a new surah begins
    for l in pg["lines"]:
        if "w" not in l:
            if l.get("t") == "s":
                page_words.starts.add(len(words))
            continue
        for t in l["w"].split():
            if t[0] == "#":
                if words:
                    words[-1] = (words[-1][0], t[1:])
            elif t[0] != "@":
                words.append((t, None))
    return words


def page_img(doc, i):
    pm = doc[i].get_pixmap(dpi=DPI, colorspace=fitz.csGRAY)
    return np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width).copy()


def line_boxes(g):
    b = (g < 128).astype(np.uint8)
    H, W = b.shape
    hor = cv2.morphologyEx(b, cv2.MORPH_OPEN, np.ones((1, W // 3), np.uint8))
    ys = np.where(hor.sum(1) > W * 0.45)[0]
    groups = []
    for y in ys:
        if groups and y - groups[-1][-1] <= 3:
            groups[-1].append(y)
        else:
            groups.append([y])
    rules = [(q[0], q[-1]) for q in groups]
    ver = cv2.morphologyEx(b, cv2.MORPH_OPEN, np.ones((H // 3, 1), np.uint8))
    cols = np.where(ver.sum(0) > H * 0.45)[0]
    x0, x1 = (int(cols.min()), int(cols.max())) if len(cols) else (0, W)
    boxes = []
    for a, c in zip(rules, rules[1:]):
        y0, y1 = a[1] + 1, c[0]
        if y1 - y0 >= 45:                     # skip header strip / double frame rules
            boxes.append((y0, y1, x0 + 6, x1 - 6))
    # a missed rule or a surah-heading panel gives a box 2 (or 3) lines tall:
    # cut it into equal line slots so every page has its 15 slots
    if boxes:
        h = float(np.median([b[1] - b[0] for b in boxes]))
        out = []
        for y0, y1, xa, xb in boxes:
            k = max(1, int(round((y1 - y0) / h)))
            for q in range(k):
                out.append((int(y0 + (y1 - y0) * q / k), int(y0 + (y1 - y0) * (q + 1) / k), xa, xb))
        boxes = out
    return boxes


_reader = None


def ocr_page(doc, i):
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(["ar"], gpu=False, verbose=False)
    g = page_img(doc, i)
    out = []
    for y0, y1, x0, x1 in line_boxes(g):
        res = _reader.readtext(g[y0:y1, x0:x1], detail=1, paragraph=False)
        res.sort(key=lambda r: -max(p[0] for p in r[0]))        # right to left
        out.append(" ".join(r[1] for r in res))
    return out


def split_lines(words, ocr, starts=()):
    """DP: assign consecutive word runs to scanned lines. Returns (breaks, cost,
    kinds) where kinds[k] is 'text' or 'other' (a box with no Quran words)."""
    W = [norm(w) for w, _ in words]
    O = [norm(o) for o in ocr]
    n, m = len(W), len(O)
    pre = [0]
    for w in W:
        pre.append(pre[-1] + len(w))
    INF = 10 ** 9
    cost = [[INF] * (n + 1) for _ in range(m + 1)]
    back = [[None] * (n + 1) for _ in range(m + 1)]
    cost[0][0] = 0
    for k in range(m):
        ok = O[k]
        for i in range(n + 1):
            c0 = cost[k][i]
            if c0 >= INF:
                continue
            # this scanned line holds no Quran words (surah header etc.)
            c = c0 + NONTEXT_COST + len(ok) * 0.5
            if c < cost[k + 1][i]:
                cost[k + 1][i] = c
                back[k + 1][i] = (i, "other")
            for jx in range(i + 1, min(n, i + 30) + 1):
                if any(i < b < jx for b in starts):
                    break                      # a line never runs across a surah heading
                ln = pre[jx] - pre[i]
                if ln > len(ok) * 2 + 12:
                    break
                d = Levenshtein.distance("".join(W[i:jx]), ok)
                c = c0 + d
                if c < cost[k + 1][jx]:
                    cost[k + 1][jx] = c
                    back[k + 1][jx] = (i, "text")
    breaks, kinds = [n], []
    i = n
    for k in range(m, 0, -1):
        if back[k][i] is None:
            return None, INF, None
        pi, kind = back[k][i]
        kinds.append(kind)
        breaks.append(pi)
        i = pi
    breaks.reverse()
    kinds.reverse()
    return breaks, cost[m][n], kinds


def margins(words, ocr, breaks, kinds):
    """For each line end: how much worse the fit gets if the break moves one
    word either way (small = unsure)."""
    W = [norm(w) for w, _ in words]
    O = [norm(o) for o in ocr]

    def c(k, i, j):
        return Levenshtein.distance("".join(W[i:j]), O[k])

    out = []
    for k in range(len(O) - 1):
        a, b, e = breaks[k], breaks[k + 1], breaks[k + 2]
        if kinds[k] != "text" or kinds[k + 1] != "text":
            out.append(99)
            continue
        base = c(k, a, b) + c(k + 1, b, e)
        alts = []
        if b - 1 > a:
            alts.append(c(k, a, b - 1) + c(k + 1, b - 1, e))
        if b + 1 < e:
            alts.append(c(k, a, b + 1) + c(k + 1, b + 1, e))
        out.append(min(alts) - base if alts else 99)
    out.append(99)
    return out


def w_split(words, ocr, breaks, k):
    """Emdadia often leaves a leading 'wa' at the end of the previous line."""
    b = breaks[k + 1]
    if b >= len(words):
        return False
    nxt = norm(words[b][0])
    if not nxt.startswith("و") or len(nxt) < 3:
        return False
    return norm(ocr[k]).endswith("و") and not norm("".join(w for w, _ in words[breaks[k]:b])).endswith("و")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="*", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--range", nargs=2, type=int, help="OCR only: PDF page indexes a..b into --cache")
    ap.add_argument("--cache", default=CACHE)
    args = ap.parse_args()
    doc = fitz.open(PDF)
    qul = load_pages()
    CACHE_F = args.cache
    cache = json.load(open(CACHE_F, encoding="utf-8")) if os.path.exists(CACHE_F) else {}
    if args.range:
        import torch
        torch.set_num_threads(2)
        for i in range(args.range[0], args.range[1] + 1):
            if str(i) not in cache:
                cache[str(i)] = ocr_page(doc, i)
                with open(CACHE_F + ".tmp", "w", encoding="utf-8") as fh:   # write whole file, then swap
                    json.dump(cache, fh, ensure_ascii=False)
                os.replace(CACHE_F + ".tmp", CACHE_F)
                print("ocr", i, flush=True)
        print("RANGE DONE", flush=True)
        return
    todo = list(range(1, 611)) if args.all else args.pages
    rows, report = [], []
    for n_done, i in enumerate(todo):
        key = str(i)
        if key not in cache:
            cache[key] = ocr_page(doc, i)
            if n_done % 5 == 0:
                json.dump(cache, open(CACHE_F, "w", encoding="utf-8"), ensure_ascii=False)
        ocr = cache[key]
        words = page_words(qul[key])
        breaks, cost, kinds = split_lines(words, ocr, page_words.starts)
        if breaks is None:
            report.append((i, "FAILED", len(ocr)))
            continue
        mg = margins(words, ocr, breaks, kinds)
        nchar = sum(len(norm(w)) for w, _ in words) or 1
        report.append((i, "ok", len(ocr), round(cost / nchar, 2), sum(1 for x in mg if x < 2)))
        ln = 0
        for k in range(len(ocr)):
            ws = words[breaks[k]:breaks[k + 1]]
            ln += 1
            if kinds[k] != "text" or not ws:
                rows.append([i + 1, i, ln, "other", "", "", "", "", "", ocr[k]])
                continue
            rows.append([i + 1, i, ln, "text", ws[0][0], ws[-1][0],
                         " ".join(w for w, _ in ws), int(w_split(words, ocr, breaks, k)), mg[k], ocr[k]])
            if args.show:
                print("%3d %2d  m=%-3s %s  %s … %s" % (i, ln, mg[k], "w+" if rows[-1][7] else "  ", ws[0][0], ws[-1][0]))
    json.dump(cache, open(CACHE_F, "w", encoding="utf-8"), ensure_ascii=False)
    out = OUT if args.all else OUT.replace(".csv", "_test.csv")
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["imdadia_page", "pdf_index", "line", "type", "first_word", "last_word", "words",
                    "wa_left_on_this_line", "confidence_margin", "ocr_reading"])
        w.writerows(rows)
    for r in report:
        print("page idx %s: %s  lines=%s  misfit=%s  unsure_line_ends=%s" % (r + ("", ""))[:5] if len(r) < 5 else
              "page idx %s: %s  lines=%s  misfit=%s  unsure_line_ends=%s" % r)
    print("wrote", out)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
