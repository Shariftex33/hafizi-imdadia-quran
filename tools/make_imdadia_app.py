#!/usr/bin/env python3
"""Build Hafizi_Imdadia_Quran.html: a separate app that shows only the
Hafizi Imdadia (Emdadia Library, 15 lines) Quran, with the look of the print.

It is generated from Tahfizul_Quran_9.html (same engine and data files) so the
two never have to be edited by hand in parallel:

    python tools/make_imdadia_app.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Tahfizul_Quran_9.html")
DST = os.path.join(ROOT, "Hafizi_Imdadia_Quran.html")

CSS = """
<style>
/* ===== Hafizi Imdadia look (black and white print) ===== */
body.imdonly{background:#e6e6e1;--page-w:min(100%, 920px, calc((100dvh - 150px) / 1.68))}
.imdonly .hint,.imdonly .credit{display:none}
/* frame as in the print: thin rule inside, heavy rule outside */
.imdonly .tahfiz .frame,.imdonly .frame{padding:0;border:.22cqw solid #111;background:#fff;box-shadow:0 0 0 .32cqw #fff, 0 0 0 1cqw #111}
/* corner scrolls: the heavy rule stops short of each corner and ends in a leaf scroll, as in the print */
.imdonly .tahfiz .orn,.imdonly .orn{display:block;width:10cqw;height:10cqw;background:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 60 60'><path d='M0 0H60V14.6H14.6V60H0Z' fill='%23fff'/><g id='a' fill='none' stroke='%23111' stroke-linecap='round'><path d='M60 11.65H51' stroke-width='4.1' stroke-linecap='butt'/><path d='M51 9.6C46 9.6 44 5.500 38.5 5.500C32.5 5.500 30 11.5 34.5 13C37.5 14 38.8 10.4 36.2 9.700' stroke-width='1.9'/><path d='M51 13.7C47.500 13.7 46 12.6 44 11' stroke-width='1.5'/><path d='M38.5 5.500C33 1.500 25 2 20.5 7.200C26.500 6.200 32.5 8.300 38.5 5.500Z' fill='%23111' stroke-width='.6'/><path d='M27 12.8C24 9.5 19.500 10.5 20.5 13.6C21.3 15.6 24 14.6 23.2 12.9' stroke-width='1.5'/></g><use href='%23a' transform='matrix(0 1 1 0 0 0)'/><path d='M4 4C8.500 12 12 15.500 20 20C15.500 12 12 8.500 4 4Z' fill='%23111'/><circle cx='16.5' cy='16.5' r='1.6' fill='%23fff' stroke='%23111' stroke-width='.9'/></svg>") no-repeat 0 0/100% 100%}
.imdonly .orn.tl{left:-2.6cqw;top:-2.6cqw}.imdonly .orn.tr{right:-2.6cqw;top:-2.6cqw}
.imdonly .orn.bl{left:-2.6cqw;bottom:-2.6cqw}.imdonly .orn.br{right:-2.6cqw;bottom:-2.6cqw}
.imdonly .book{background:#fff;--edge:9cqw}
.imdonly .head{font-family:var(--quran-font),serif;font-weight:400;font-size:3.5cqw;height:10cqw;padding-bottom:3.3cqw}
.imdonly .mtm .go{text-decoration:none}
/* juz / quarter / half / three-quarter marks beside the frame, written upright along it as in the print */
.imdq{position:absolute;white-space:nowrap;direction:rtl;font-family:var(--quran-font),serif;font-size:3.8cqw;line-height:1;color:#111;pointer-events:none;z-index:4}
.imdq.j{font-size:4cqw;-webkit-text-stroke:.5px currentColor}
#edgeR .imdq{left:3.6cqw;transform:translate(-50%,-50%) rotate(90deg)}#edgeL .imdq{right:3.6cqw;transform:translate(50%,-50%) rotate(90deg)}
.imdonly .head>span{direction:rtl}
.imdonly .head>span:nth-child(2){margin-bottom:0;font-size:3.6cqw}
.imdonly .foot{display:flex;justify-content:center;align-items:center;direction:rtl;height:4.8cqw;box-sizing:border-box;
  font-family:var(--quran-font),serif;font-size:3cqw;color:#111}
/* mutashabihat marks stay coloured as in the Tahfiz book; everything else is black like the print */
.imdonly .book.tahfiz.ruled .line,.imdonly .book.tahfiz.ruled .surahline,.imdonly .book.tahfiz.ruled .basmala,.imdonly .book.tahfiz.ruled .blank{border-bottom:1.3px solid #222}
.imdonly .tahfiz .m{border-color:#1a1a1a;color:#111;border-width:1.1px}
.imdonly .tahfiz .surahline{border-color:#111;color:#111;box-shadow:inset 0 0 0 3px #fff, inset 0 0 0 4px #111}
.imdonly .tahfiz .surahline::before,.imdonly .tahfiz .surahline::after{border-color:#111}
/* opening pages (Fatiha, start of Baqarah): heading and bismillah on top, then 7 large lines */
.imdonly .book.imdopen .head,.imdonly .book.imdopen .foot{visibility:hidden}
.imdonly .book.imdopen .frame{padding:4.4cqw;border:.5cqw solid #111;box-shadow:none;background-color:#111;background-size:4.4cqw 4.4cqw;background-repeat:round;
  background-image:url("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><rect width='24' height='24' fill='%23111'/><path d='M12 1.5C14 7 17 10 22.5 12C17 14 14 17 12 22.5C10 17 7 14 1.5 12C7 10 10 7 12 1.5Z' fill='%23fff'/><path d='M12 6.5C13 9.5 14.5 11 17.5 12C14.5 13 13 14.5 12 17.5C11 14.5 9.500 13 6.500 12C9.500 11 11 9.500 12 6.500Z' fill='%23111'/><circle cx='12' cy='12' r='1.5' fill='%23fff'/><circle cx='0' cy='0' r='3.2' fill='%23fff'/><circle cx='24' cy='0' r='3.2' fill='%23fff'/><circle cx='0' cy='24' r='3.2' fill='%23fff'/><circle cx='24' cy='24' r='3.2' fill='%23fff'/><circle cx='0' cy='0' r='1.3' fill='%23111'/><circle cx='24' cy='0' r='1.3' fill='%23111'/><circle cx='0' cy='24' r='1.3' fill='%23111'/><circle cx='24' cy='24' r='1.3' fill='%23111'/></svg>")}
.imdonly .book.imdopen .sheet{background:#fff;border:.4cqw solid #111;box-shadow:inset 0 0 0 .3cqw #fff, inset 0 0 0 .45cqw #111}
.imdonly .book.imdopen .orn{display:none}
.imdonly .book.imdopen #lines{padding-top:5cqw;box-sizing:border-box}
.imdonly .book.imdopen .blank{display:none}
.imdonly .book.imdopen .line{flex:1 1 0;height:auto}
.imdonly .book.imdopen .surahline.imdsur{flex:0 0 19%;height:auto;flex-direction:column;justify-content:center;gap:.35em;border:0;box-shadow:none;background:none;margin:0;padding:0;font-size:4.2cqw}
.imdonly .book.imdopen .imdsur::before,.imdonly .book.imdopen .imdsur::after{display:none}
.imdonly .book.imdopen .imdsur>span{border:0;background:none;padding:0;line-height:1.2}
.imdonly .book.imdopen .basmala,.imdonly .book.imdopen .line.imdbism{flex:1 1 0;height:auto;justify-content:center;border-bottom:1.3px solid #222}
/* the first line of every juz is printed heavier */
.imdonly .book .line.juzbold{-webkit-text-stroke:1.5px currentColor;paint-order:stroke fill}
.imdonly .surahline.imdsur{justify-content:space-between;margin:.1em 1cqw;padding:0 1.9em;font-size:.56em;
  background:repeating-linear-gradient(45deg,#fff 0 .22em,#e4e4e4 .22em .3em)}
.imdonly .imdsur>span{background:#fff;padding:.15em .6em;border:1px solid #111;border-radius:1em;line-height:1.5;white-space:nowrap}
.imdonly .imdsur .ic{font-size:1.18em}
.imdonly .basmala{font-size:.92em}
.imdonly .nd{font-family:"NotoNaskhLocal","Noto Naskh Arabic","Amiri","Scheherazade New",serif;font-weight:700;font-size:1.1em;line-height:1}
.imdonly .m{font-family:"NotoNaskhLocal","Noto Naskh Arabic","Scheherazade New","Amiri",serif}
</style>
"""

JS = r"""
<script>
/* ===== Hafizi Imdadia only: fixed layout, print look ===== */
(function(){
  document.body.classList.add("imdonly");
  ["ln","sz","cpara","csur","cfat","cbaq","ctf","ctj","cgl"].forEach(function(id){
    var e = $(id), l = e && e.closest("label"); if (l) l.style.display = "none";
  });
  if ($("tjk")) $("tjk").style.display = "none";
  ornateSurah = function(){ return 0; };          // the opening pages are drawn by this file, not by the Tahfiz ornament

  /* Surah Fatiha as printed: the bismillah stands alone without a number and the ayat are counted 1-7 after it */
  /* where each juz begins (Indo-Pak division), as surah:ayah of its first word */
  var JSTART = ["2:1","2:142","2:253","3:92","4:24","4:148","5:83","6:111","7:88","8:41","9:94","11:6","12:53","15:2","17:1","18:75","21:1","23:1","25:21","27:60","29:45","33:31","36:22","39:32","41:47","46:1","51:31","58:1","67:1","78:1"];
  var JMAP = {}; JSTART.forEach(function(k, i){ JMAP[k] = i + 1; });
  function juzOfLine(l){
    if (!l || l.t !== "l") return 0;
    for (var a = 0; a < l.u.length; a++) for (var b = 0; b < l.u[a].it.length; b++) {
      var it = l.u[a].it[b];
      if (it.k === "w" && it.p === 1 && JMAP[it.s + ":" + it.a]) return JMAP[it.s + ":" + it.a];
    }
    return 0;
  }
  var juzFixed = false;
  function fixJuz(){                               // the source marks the juz per page; mark it per word instead
    var cur = 1, i, k;
    for (i = 0; i < S.length; i++) {
      var t = S[i];
      if (t.k === "s") { for (k = i + 1; k < S.length && S[k].k !== "w"; k++); if (S[k] && S[k].p === 1 && JMAP[S[k].s + ":" + S[k].a] > 1) cur = JMAP[S[k].s + ":" + S[k].a]; }
      else if (t.k === "w" && t.p === 1 && JMAP[t.s + ":" + t.a] > 1) cur = JMAP[t.s + ":" + t.a];
      t.j = cur;
    }
    juzFixed = true;
  }
  var _cl = computeLayout;
  computeLayout = function(){
    if (!juzFixed) fixJuz();
    _cl();
    var f = PG[0] && PG[0].filter(function(l){ return l.t === "l"; })[0];
    if (f) f.mode = "c";
  };
  var _mi = makeItem;
  makeItem = function(it, nf){
    var s = _mi(it, nf);
    if (it.k === "m" && it.s === 1) {
      if (it.a === 1) s.style.display = "none"; else s.textContent = nf(it.a === 7 ? 7 : it.a - 1);
    }
    return s;
  };
  showCover = function(){};                       // this book has no cover page

  function surahs(P){
    var a = [];
    P.forEach(function(l){
      var x = l.t === "s" ? [l.n] : (l.t === "l" ? [l.u[0].it[0].s, l.u[l.u.length - 1].it[0].s] : []);
      x.forEach(function(s){ if (a.indexOf(s) < 0) a.push(s); });
    });
    return a;
  }
  function nd(x){ return "<span class='nd'>" + ar(x) + "</span>"; }
  function skin(){
    var n = curPage, P = PG[n - 1]; if (!P) return;
    var meta = P.meta, ss = surahs(P);
    if (ss.length > 2) ss = [ss[0], ss[ss.length - 1]];
    $("hd1").innerHTML = (typeof PARA !== "undefined" && PARA[meta.j - 1] ? PARA[meta.j - 1] + " " : "") + nd(meta.j);
    $("hd2").innerHTML = nd(n + 1);                                   // the print counts one page more
    $("hd3").innerHTML = ss.map(function(s){ return SN[s - 1] + " " + nd(s); }).join(" - ");
    $("ft").innerHTML = "<span>منزل " + nd(meta.m) + "</span>";
    /* first line of a juz: the line holding the first word of the juz (for juz 1, the first line of Baqarah) */
    P.forEach(function(l, li){ if (rowMap[li] && juzOfLine(l)) rowMap[li].classList.add("juzbold"); });
    P.forEach(function(l, li){
      var row = rowMap[li];
      if (l.t !== "s" || !row) return;
      var sm = SURMETA[l.n] || { ay:0, ru:0 };
      row.className = "surahline imdsur";
      row.innerHTML = "<span>اٰیَاتُهَا " + nd(l.n === 1 ? 7 : sm.ay) + "</span><span class='ic'>(" + nd(l.n) + ") سُوْرَةُ " + SN[l.n - 1] +
        (MEDINAN[l.n] ? " مَدَنِيَّةٌ" : " مَكِّيَّةٌ") + " (" + nd(SURAH_REV[l.n - 1]) + ")</span><span>رُكُوْعُهَا " + nd(sm.ru) + "</span>";
    });
  }
  /* opening pages: 7 large lines under the heading and bismillah */
  function openFit(){
    var open = curPage <= 2, P = PG[curPage - 1];
    book.classList.toggle("imdopen", open);
    if (!open || !P) return;
    var all = [].slice.call(root.querySelectorAll(".line"));
    if (curPage === 1 && all[0]) all.shift().classList.add("imdbism");
    if (!all.length) return;
    var W = all[0].clientWidth, H = all[0].clientHeight, mx = 0;
    P.forEach(function(l){
      if (l.t !== "l" || l.mode === "c") return;
      var nat = 0.3 * (l.u.length - 1); l.u.forEach(function(u){ nat += u.w; });
      if (nat > mx) mx = nat;
    });
    var size = Math.min(W / (mx + 0.2), H / 1.45);
    root.style.fontSize = size + "px";
    all.forEach(function(r){
      r.style.fontSize = "";
      var tries = 0, fs = size;
      while (r.scrollWidth > r.clientWidth + 0.5 && tries++ < 4) { fs = fs * r.clientWidth / r.scrollWidth * 0.995; r.style.fontSize = fs + "px"; }
    });
    placeSigns(); placeMargins();
  }
  /* the first line of a juz is also printed larger */
  function juzBig(){
    var rows = root.querySelectorAll(".line.juzbold"), base = parseFloat(root.style.fontSize) || 0, i;
    if (!rows.length || !base) return;
    for (i = 0; i < rows.length; i++) {
      var r = rows[i], fs = Math.min(base * 1.3, r.clientHeight / 1.25), tries = 0;
      r.style.fontSize = fs + "px";
      while (r.scrollWidth > r.clientWidth + 0.5 && tries++ < 5) { fs = fs * r.clientWidth / r.scrollWidth * 0.995; r.style.fontSize = fs + "px"; }
    }
    placeSigns();
  }
  /* waqf signs between words: open the gap as far as the sign needs, so it never sits on the letters */
  function signSpace(){
    var rows = root.querySelectorAll(".line"), i;
    for (i = 0; i < rows.length; i++) {
      var row = rows[i], sgs = row.querySelectorAll(".sg"), k;
      if (!sgs.length) continue;
      for (k = 0; k < sgs.length; k++) if (sgs[k].word) sgs[k].word.style.marginLeft = "";
      var fs = parseFloat(getComputedStyle(row).fontSize) || 20;
      for (k = 0; k < sgs.length; k++) {
        var sg = sgs[k], w = sg.word;
        if (!w || w.classList.contains("m")) continue;             // signs on an ayah circle sit above the circle
        var need = sg.offsetWidth + fs * 0.12, wr = w.getBoundingClientRect(), nr = sg.nx ? sg.nx.getBoundingClientRect() : null;
        var gap = nr && nr.right <= wr.left + 1 ? wr.left - nr.right : 0;
        if (gap < need) w.style.marginLeft = (need - gap) + "px";
      }
      var tries = 0, f = fs;
      while (row.scrollWidth > row.clientWidth + 0.5 && tries++ < 5) { f = f * row.clientWidth / row.scrollWidth * 0.995; row.style.fontSize = f + "px"; }
    }
    placeSigns();
  }
  /* juz, quarter, half and three-quarter marks in the margin */
  var QTXT = { r:"الربع", n:"النصف", t:"الثلثة" };
  function marks(){
    var old = document.querySelectorAll(".imdq"), i;
    for (i = 0; i < old.length; i++) old[i].remove();
    var P = PG[curPage - 1]; if (!P) return;
    var list = [], fr = document.querySelector(".frame").getBoundingClientRect(), edges = [$("edgeR"), $("edgeL")];
    P.forEach(function(l, li){ var j = juzOfLine(l); if (j) list.push({ li:li, txt:"الجزء " + ar(j), cls:" j" }); });
    ((typeof IMD_MARKS !== "undefined" && IMD_MARKS[curPage]) || []).forEach(function(m){ list.push({ li:m[0] - 1, txt:"• " + QTXT[m[1]], cls:"" }); });
    list.forEach(function(m){
      var row = rowMap[m.li]; if (!row) return;
      var rr = row.getBoundingClientRect(), mid = rr.top + rr.height / 2, el = document.createElement("div");
      var cq = book.clientWidth / 100, top = Math.max(13 * cq, Math.min(fr.height - 13 * cq, mid - fr.top));   // keep clear of the corner scrolls
      el.className = "imdq" + m.cls; el.textContent = m.txt; el.style.top = top + "px";
      var pick = null;
      edges.forEach(function(edge){                 // the side where nothing else stands at this height
        if (pick) return;
        edge.appendChild(el);
        var er = el.getBoundingClientRect(), clash = false, c = edge.children, k;
        for (k = 0; k < c.length; k++) { if (c[k] === el) continue; var q = c[k].getBoundingClientRect(); if (q.bottom > er.top - 2 && q.top < er.bottom + 2) { clash = true; break; } }
        if (!clash) pick = edge; else edge.removeChild(el);
      });
      if (!pick) edges[0].appendChild(el);
    });
  }
  var _fit = fit;
  fit = function(){ _fit(); openFit(); juzBig(); signSpace(); marks(); };
  var _lp = loadPage;
  loadPage = function(n){ _lp(n); skin(); openFit(); juzBig(); signSpace(); marks(); };
})();
</script>
"""


def rep(s, a, b, count=1):
    assert s.count(a) == count, (a[:60], s.count(a))
    return s.replace(a, b)


def main():
    s = open(SRC, encoding="utf-8").read()
    s = re.sub(r"<title>.*?</title>", "<title>Hafizi Imdadia Quran – 15 line</title>", s, count=1)
    s, k = re.subn(r'(<div class="cover" id="cover" hidden><img alt=")[^"]*(" src=")[^"]*(")', r"\1\2\3", s, count=1)
    assert k == 1
    # own settings, always the fixed Imdadia layout in black and white
    s = s.replace("nuraniCfg4", "imdadiaCfg2").replace("nuraniAnchor", "imdadiaAnchor")
    s = rep(s, "var FONT_OPTIONS = [", """var FONT_OPTIONS = [
  { id:"alqalam4", label:"Al Qalam Quran Majeed 4", family:"AlQalam4",
    files:["fonts/Al%20Qalam%20Quran%20Majeed%204.ttf"], stack:"'AlQalam4','IndoPak','Amiri',serif" },""")
    s = rep(s, 'size:"normal", font:"indopak",', 'size:"normal", font:"alqalam4",')
    s = rep(s, 'load("nuraniBnNum2") !== "0"', 'load("imdadiaBnNum") === "1"')
    s = s.replace("nuraniBnNum2", "imdadiaBnNum")
    s = rep(s, "function saveCfg(){",
            "CFG.hafezi = true; CFG.imd = true; CFG.tahfiz = true; CFG.tj = false; CFG.glyphMark = false;\nfunction saveCfg(){")
    s = rep(s, '<script src="data/imdadia_lines.js"></script>',
            '<script src="data/imdadia_lines.js"></script><script src="data/imdadia_marks.js"></script>')
    # Bangla translation of this book: Muhiuddin Khan (no footnotes), not the Tahfiz book's one
    s = rep(s, '<script src="data/tr_bn.js"></script>', '<script src="data/tr_bn_khan.js"></script>')
    s = rep(s, "function ensureFN(lang){", 'function ensureFN(lang){ if (lang === "bn") return;')
    s = s.replace("Bangla – Dr. Abu Bakr Muhammad Zakaria, from", "Bangla – Maulana Muhiuddin Khan (Tanzil.net); English from")
    s = rep(s, 'if (en) { h += line("Ayah – English", "", TR.en[key]) + fnBlock("en", key); ensureFN("en"); }',
            'if (en) { h += line("Ayah – English", "", TR.en[key]) + fnBlock("en", key); ensureFN("en"); }'
            ' if (bn2) h += line("আয়াত – বাংলা", "bn", TR.bn[key]);')
    s = rep(s, "</head>", CSS + "</head>")
    i = s.rindex("</body>")
    s = s[:i] + JS + s[i:]
    open(DST, "w", encoding="utf-8", newline="").write(s)
    print("wrote", DST, round(len(s) / 1024), "KB")


if __name__ == "__main__":
    main()
