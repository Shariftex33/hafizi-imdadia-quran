/* ===== Hafizi Imdadia: optional two-page view (like the open book) with a page-turn animation =====
   The live page (the one that answers taps) is #book; the facing page is a snapshot of it taken
   one step earlier. Clicking the facing page makes it the live one.
   Right-hand page = odd page of the app (Fatiha), left-hand page = the even page that follows. */
(function(){
  var wrap = document.createElement("div");
  wrap.id = "imdSpread";
  book.parentNode.insertBefore(wrap, book);
  wrap.appendChild(book);

  var optSpread = load("imdSpreadOn") !== "0", optAnim = load("imdAnim") !== "0";
  var snap = null, busy = false, animating = false;

  function active(){ return optSpread && !document.body.classList.contains("imdchk"); }
  function dropSnap(){ if (snap) { snap.remove(); snap = null; } }
  function takeSnap(pageNo){
    dropSnap();
    snap = book.cloneNode(true);
    snap.id = "bookSnap"; snap.classList.add("snap");
    var p = snap.querySelector(".pop"); if (p) p.hidden = true;
    snap.title = "Click to work on this page";
    snap.onclick = function(){ loadPage(pageNo); };
    wrap.appendChild(snap);                       // after the live book, so the live ids are found first
  }
  function rightOf(n){ return n % 2 ? n : n - 1; }

  var _full = loadPage;
  loadPage = function(n){
    var on = active();
    if (document.body.classList.contains("imdspread") !== on) {
      document.body.classList.toggle("imdspread", on);
      if (!on) { dropSnap(); book.style.order = ""; }
    }
    if (!on || busy) { _full(n); return; }
    busy = true;
    try {
      n = Math.max(1, Math.min(PG.length, n));
      var r = rightOf(n), other = n === r ? r + 1 : r;
      if (other >= 1 && other <= PG.length) { _full(other); takeSnap(other); } else dropSnap();
      _full(n);
      book.style.order = n === r ? 2 : 1;
      if (snap) snap.style.order = n === r ? 1 : 2;
    } finally { busy = false; }
  };

  /* ---- turning to the next / previous opening ---- */
  function slot(order){                            // the page element standing on the left (1) or right (2)
    if (+book.style.order === order) return book;
    return snap && +snap.style.order === order ? snap : null;
  }
  function overlay(el, z){
    var o = el.cloneNode(true);
    o.id = ""; o.classList.add("imdflip"); o.onclick = null;
    o.style.left = el.offsetLeft + "px"; o.style.top = el.offsetTop + "px";
    o.style.width = el.offsetWidth + "px"; o.style.height = el.offsetHeight + "px";
    o.style.zIndex = z; o.style.order = "";
    return o;
  }
  function turn(target, dir){                      // dir +1: next opening, -1: previous opening
    target = Math.max(1, Math.min(PG.length, target));
    if (!active() || !optAnim || animating || !book.animate || rightOf(target) === rightOf(curPage)) { loadPage(target); return; }
    var movingSide = dir > 0 ? 1 : 2, stillSide = dir > 0 ? 2 : 1;      // next: the left leaf turns over to the right
    var oldMove = slot(movingSide), oldStill = slot(stillSide);
    var a = oldMove ? overlay(oldMove, 6) : null, b = oldStill ? overlay(oldStill, 5) : null;
    animating = true;
    loadPage(target);
    if (a) wrap.appendChild(a);
    if (b) wrap.appendChild(b);
    var newStill = slot(stillSide), c = newStill ? overlay(newStill, 7) : null;
    var half = 330, deg = dir > 0 ? 90 : -90;
    var done = function(){ [a, b, c].forEach(function(e){ if (e) e.remove(); }); animating = false; };
    var second = function(){
      if (a) a.remove();
      if (!c) { done(); return; }
      c.style.transformOrigin = dir > 0 ? "left center" : "right center";
      wrap.appendChild(c);
      c.animate([{ transform:"rotateY(" + (-deg) + "deg)", filter:"brightness(.78)" }, { transform:"rotateY(0deg)", filter:"brightness(1)" }],
                { duration:half, easing:"ease-out", fill:"forwards" }).onfinish = done;
    };
    if (!a) { second(); return; }
    a.style.transformOrigin = dir > 0 ? "right center" : "left center";
    a.animate([{ transform:"rotateY(0deg)", filter:"brightness(1)" }, { transform:"rotateY(" + deg + "deg)", filter:"brightness(.78)" }],
              { duration:half, easing:"ease-in", fill:"forwards" }).onfinish = second;
    setTimeout(function(){ if (animating) done(); }, half * 2 + 600);   // safety net
  }

  var _next = nextPage, _prev = prevPage;
  nextPage = function(){ if (active()) turn(rightOf(curPage) + 2, 1); else _next(); };
  prevPage = function(){ if (active()) turn(rightOf(curPage) - 2, -1); else _prev(); };
  [["nx", 1], ["pv", -1], ["imdNavL", 1], ["imdNavR", -1]].forEach(function(x){
    var e = $(x[0]); if (e) e.onclick = function(){ if (x[1] > 0) nextPage(); else prevPage(); };
  });

  /* ---- the option, in the settings panel ---- */
  var bar = document.querySelector(".bar"), row = document.createElement("div");
  row.innerHTML = "<label>View <select id='imdView'><option value='0'>One page</option><option value='1'>Two pages (open book)</option></select></label>" +
                  "<label><input type='checkbox' id='imdAnimBox'> Page-turn animation</label>";
  row.innerHTML += "<label>Text size <select id='imdFillSel'><option value='1'>Largest (fill each line)</option><option value='0'>Even (same size on the page)</option></select></label>" +
                   "<label>Weight <select id='imdBoldSel'><option value='0'>Light</option><option value='.5'>Normal</option><option value='.8'>Bold</option><option value='1.2'>Extra bold</option><option value='1.6'>Heaviest</option></select></label>";
  bar.insertBefore(row, bar.children[1] || null);
  var boldV = load("imdBold") || ".8";
  function setBold(){ document.body.style.setProperty("--imdbold", boldV + "px"); }
  setBold();
  $("imdBoldSel").value = boldV; $("imdFillSel").value = window.IMD_OPT.fill ? "1" : "0";
  $("imdBoldSel").onchange = function(){ boldV = this.value; store("imdBold", boldV); setBold(); };
  $("imdFillSel").onchange = function(){ window.IMD_OPT.fill = this.value === "1"; store("imdFill", this.value); refresh(); };
  $("imdView").value = optSpread ? "1" : "0"; $("imdAnimBox").checked = optAnim;
  function refresh(){ var cp = curPage; anchorTok = null; loadPage(cp); relayout(); if (curPage !== cp) loadPage(cp); }
  $("imdView").onchange = function(){ optSpread = this.value === "1"; store("imdSpreadOn", optSpread ? "1" : "0"); refresh(); };
  $("imdAnimBox").onchange = function(){ optAnim = this.checked; store("imdAnim", optAnim ? "1" : "0"); };
  try { if (new URLSearchParams(location.search).get("view") === "2") optSpread = true; } catch(e){}
})();
