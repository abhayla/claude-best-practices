/* whatsapp-flow-map engine — drop the whole file inline in ONE <script> tag.
 * Five modules, each activating only when its markup exists:
 *   1. WIRING   — <div class="stage"><svg class="wires" data-edges="a>b:live,b>c:design"></svg> + nodes with id
 *   2. PHONE    — stamps every .node (except .ext) with WhatsApp phone chrome (header + wallpaper)
 *   3. NAV      — every edge `from` element becomes a tap: click → scroll target to center + receive-pulse
 *   4. AUDIT    — flags .qr .b buttons with no id / no outgoing edge; sticky audit pill (#wfaudit auto-created)
 *   5. ZOOM/DRAG— controls #zin/#zout/#zreset/#zlab/#lreset + #viewport/#zoomable wrappers
 * Honors prefers-reduced-motion (static wires, no packets, no pulse animation — still scrolls).
 *
 * Required CSS hooks the page must define (see SKILL.md / worked example):
 *   .wires path.flowing/.live/.build/.design  .wires circle.pkt
 *   .ph .ph-head .ph-body (phone chrome)  .tap (clickable affordance)
 *   .rx (receive animation on target .node)  .b.unwired::after (badge)
 *   #wfaudit (sticky pill)  .node.dragging  #zoomable{transform-origin:0 0}  .viewport{overflow:auto}
 */
(function(){
  var RM = window.matchMedia && matchMedia("(prefers-reduced-motion:reduce)").matches;

  /* ---------- 1. WIRING (unchanged lineage: modern-data-pipeline-diagram) ---------- */
  function anchor(a,b,cb){
    var acx=a.left+a.width/2-cb.left, acy=a.top+a.height/2-cb.top;
    var bcx=b.left+b.width/2-cb.left, bcy=b.top+b.height/2-cb.top;
    var dx=bcx-acx, dy=bcy-acy, p1,p2;
    if(Math.abs(dx)>=Math.abs(dy)){
      p1=[a.left+(dx>=0?a.width:0)-cb.left, acy];
      p2=[b.left+(dx>=0?0:b.width)-cb.left, bcy];
    }else{
      p1=[acx, a.top+(dy>=0?a.height:0)-cb.top];
      p2=[bcx, b.top+(dy>=0?0:b.height)-cb.top];
    }
    return [p1,p2,Math.abs(dx)>=Math.abs(dy)];
  }
  function wire(stage){
    var svg=stage.querySelector("svg.wires"); if(!svg) return;
    var spec=(svg.getAttribute("data-edges")||"").split(",").map(function(s){return s.trim()}).filter(Boolean);
    var cb=stage.getBoundingClientRect();
    while(svg.firstChild) svg.removeChild(svg.firstChild);
    svg.setAttribute("viewBox","0 0 "+cb.width+" "+cb.height);
    spec.forEach(function(e,i){
      var m=e.match(/^([\w-]+)>([\w-]+)(?::(\w+))?$/); if(!m) return;
      var A=stage.querySelector("#"+m[1]), B=stage.querySelector("#"+m[2]); if(!A||!B) return;
      /* filtered-out / version-hidden endpoints draw no wire */
      if((A.offsetWidth===0&&A.offsetHeight===0)||(B.offsetWidth===0&&B.offsetHeight===0)) return;
      var kind=m[3]||"live";
      var pts=anchor(A.getBoundingClientRect(),B.getBoundingClientRect(),cb), p1=pts[0],p2=pts[1],horiz=pts[2];
      var mx=(p1[0]+p2[0])/2, my=(p1[1]+p2[1])/2, c1,c2;
      if(horiz){ c1=[mx,p1[1]]; c2=[mx,p2[1]]; } else { c1=[p1[0],my]; c2=[p2[0],my]; }
      var d="M "+p1[0]+" "+p1[1]+" C "+c1[0]+" "+c1[1]+" "+c2[0]+" "+c2[1]+" "+p2[0]+" "+p2[1];
      var id="pth-"+(stage.dataset.k||"")+i+"-"+Math.floor(mx);
      var path=document.createElementNS("http://www.w3.org/2000/svg","path");
      path.setAttribute("d",d); path.setAttribute("id",id); path.setAttribute("class","flowing "+kind);
      svg.appendChild(path);
      if(!RM){
        var pkt=document.createElementNS("http://www.w3.org/2000/svg","circle");
        pkt.setAttribute("r","3.4"); pkt.setAttribute("class","pkt"+(kind==="build"?" build":kind==="design"?" design":""));
        var am=document.createElementNS("http://www.w3.org/2000/svg","animateMotion");
        am.setAttribute("dur",(2.6+(i%4)*0.5)+"s"); am.setAttribute("repeatCount","indefinite");
        am.setAttribute("begin",(i*0.35)+"s"); am.setAttribute("rotate","auto");
        var mp=document.createElementNS("http://www.w3.org/2000/svg","mpath");
        mp.setAttributeNS("http://www.w3.org/1999/xlink","href","#"+id); mp.setAttribute("href","#"+id);
        am.appendChild(mp); pkt.appendChild(am); svg.appendChild(pkt);
      }
    });
  }
  var stages=[].slice.call(document.querySelectorAll(".stage"));
  stages.forEach(function(s,i){ s.dataset.k=i; });
  function wireAll(){ stages.forEach(wire); }
  window.wireAll=wireAll;
  var t; function reflow(){ clearTimeout(t); t=setTimeout(wireAll,120); }
  window.addEventListener("resize",reflow);
  if(document.fonts&&document.fonts.ready) document.fonts.ready.then(wireAll);
  window.addEventListener("load",wireAll);
  setTimeout(wireAll,240); setTimeout(wireAll,700);

  /* ---------- shared: edge registry (from -> [{to,kind}]) ---------- */
  var REG={};
  stages.forEach(function(stage){
    var svg=stage.querySelector("svg.wires"); if(!svg) return;
    (svg.getAttribute("data-edges")||"").split(",").forEach(function(e){
      var m=e.trim().match(/^([\w-]+)>([\w-]+)(?::(\w+))?$/); if(!m) return;
      (REG[m[1]]=REG[m[1]]||[]).push({to:m[2],kind:m[3]||"live"});
    });
  });
  window.WF_EDGES=REG;

  /* ---------- 2. PHONE-STAMPER — chrome derived from node classes, never hand-written ---------- */
  function phoneStamp(){
    document.querySelectorAll(".node").forEach(function(node){
      if(node.classList.contains("ext") || node.querySelector(".ph")) return;
      var bub=node.querySelector(".bub"); if(!bub) return;
      var who, sub, cls;
      if(node.classList.contains("out")){ who="You"; sub="to PIFS · +91 70806 42020"; cls="me"; }
      else if(node.classList.contains("int")){ who="Staff phone"; sub="internal alert"; cls="staff"; }
      else if(node.classList.contains("kw")){ who="Wati flow"; sub="dashboard capture"; cls="bot"; }
      else { who="PIFS · Zerodha AP"; sub="online"; cls="biz"; }
      var ph=document.createElement("div"); ph.className="ph "+cls;
      var head=document.createElement("div"); head.className="ph-head";
      head.innerHTML='<span class="ph-av">'+(cls==="me"?"Y":cls==="staff"?"S":cls==="bot"?"W":"P")+
        '</span><span class="ph-who"><b></b><i></i></span><span class="ph-ic">&#128222;&nbsp;&#8942;</span>';
      head.querySelector("b").textContent=who; head.querySelector("i").textContent=sub;
      var body=document.createElement("div"); body.className="ph-body";
      node.insertBefore(ph, bub); ph.appendChild(head); ph.appendChild(body); body.appendChild(bub);
      var fix=node.querySelector(":scope > .fixnote"); if(fix) body.appendChild(fix);
    });
  }

  /* ---------- 3. NAV — tap any wired element, land on its reply ---------- */
  var suppressTap=false;                    /* set by drag module when pointer moved */
  window.WF_setSuppress=function(v){ suppressTap=v; };
  function nodeOf(id){ var el=document.getElementById(id); return el ? (el.closest(".node")||el) : null; }
  var rxTimer=null;
  function navigate(fromId){
    var outs=REG[fromId]; if(!outs||!outs.length) return;
    document.querySelectorAll(".node.rx").forEach(function(n){ n.classList.remove("rx"); });
    var first=null;
    outs.forEach(function(o){
      var n=nodeOf(o.to); if(!n) return;
      if(!first) first=n;
      void n.offsetWidth;                   /* restart the css animation */
      n.classList.add("rx");
    });
    if(first) first.scrollIntoView({behavior: RM?"auto":"smooth", block:"center", inline:"center"});
    clearTimeout(rxTimer);
    rxTimer=setTimeout(function(){ document.querySelectorAll(".node.rx").forEach(function(n){ n.classList.remove("rx"); }); }, 4000);
  }
  /* Per-element click listeners break under pointer capture: when the drag module captures
   * the pointer, the browser retargets the derived click at the CARD, so a listener on the
   * button never fires (real taps only — programmatic .click() hides this). Delegate at the
   * document instead, resolving the tap from the element the pointer actually went DOWN on. */
  var lastDown=null;
  document.addEventListener("pointerdown",function(e){ lastDown=e.target; },true);
  function navWire(){
    Object.keys(REG).forEach(function(fromId){
      var el=document.getElementById(fromId); if(el) el.classList.add("tap");
    });
    document.addEventListener("click",function(e){
      if(suppressTap) return;
      var src=(lastDown && document.contains(lastDown)) ? lastDown : e.target;
      if(!src || !src.closest) return;
      var el=src.closest(".tap");
      if(el && el.id && REG[el.id]) navigate(el.id);
    },true);
  }

  /* ---------- 4. AUDIT — every tap must be wired; gaps get badges + the pill ---------- */
  function audit(){
    var missing=[], broken=[];
    document.querySelectorAll(".qr .b").forEach(function(b){
      var id=b.getAttribute("id");
      if(!id || !REG[id]){ b.classList.add("unwired"); missing.push(b); }
    });
    Object.keys(REG).forEach(function(f){
      if(!document.getElementById(f)) broken.push(f+" (from missing)");
      REG[f].forEach(function(o){ if(!document.getElementById(o.to)) broken.push(f+">"+o.to+" (target missing)"); });
    });
    var pill=document.getElementById("wfaudit");
    if(!pill){ pill=document.createElement("div"); pill.id="wfaudit"; document.body.appendChild(pill); }
    var n=missing.length, bad=broken.length, idx=-1;
    if(n===0 && bad===0){ pill.className="ok"; pill.textContent="all taps wired ✓"; }
    else{
      pill.className="bad";
      pill.textContent="⚠ "+n+" unwired tap"+(n===1?"":"s")+(bad?" · "+bad+" broken wire"+(bad===1?"":"s"):"")+" — click to step";
      pill.addEventListener("click",function(){
        if(!missing.length) return;
        idx=(idx+1)%missing.length;
        var b=missing[idx], node=b.closest(".node")||b;
        node.scrollIntoView({behavior: RM?"auto":"smooth", block:"center", inline:"center"});
        document.querySelectorAll(".node.rx").forEach(function(x){ x.classList.remove("rx"); });
        void node.offsetWidth; node.classList.add("rx");
        pill.textContent="⚠ unwired "+(idx+1)+"/"+missing.length+": ["+b.textContent.trim()+"]";
      });
    }
    if(bad && window.console) console.warn("whatsapp-flow-map broken wires:", broken);
  }

  /* ---------- 6. STATE FILTER + VERSION SWITCH ----------
   * Markup: <div id="wffilter"> <span class="fc" data-state="live|build|design|review|retire|info">…</span>…
   *         <span class="fv" data-ver="current">Current</span><span class="fv" data-ver="previous">Previous</span> </div>
   * Node state = its .bstat class (design counts as pending); no .bstat → "info".
   * Chips multi-select (class "on"); retire ships OFF by default (set in markup).
   * Version: cards tagged data-ver="current"/"previous" are a rewrite pair — the switch shows
   * one side; untagged cards always show. Any change refires wireAll(). */
  function applyFilter(){
    var bar=document.getElementById("wffilter"); if(!bar) return;
    var on={}; bar.querySelectorAll(".fc").forEach(function(c){ on[c.dataset.state]=c.classList.contains("on"); });
    var verEl=bar.querySelector(".fv.on"), ver=verEl?verEl.dataset.ver:"current";
    document.querySelectorAll(".node").forEach(function(n){
      var st="info", b=n.querySelector(".bstat");
      if(b){ ["live","build","design","review","retire"].forEach(function(k){ if(b.classList.contains(k)) st=k; }); }
      var v=n.getAttribute("data-ver");
      /* a version-paired card obeys ONLY the version switch — previous versions are
       * naturally retire-tagged, and the state chips must not double-hide them */
      if(v){ n.style.display=(v===ver)?"":"none"; }
      else { n.style.display=(on[st]!==false)?"":"none"; }
    });
    window.wireAll&&window.wireAll();
  }
  function filterWire(){
    var bar=document.getElementById("wffilter"); if(!bar) return;
    bar.querySelectorAll(".fc").forEach(function(c){
      c.addEventListener("click",function(){ c.classList.toggle("on"); applyFilter(); });
    });
    bar.querySelectorAll(".fv").forEach(function(c){
      c.addEventListener("click",function(){
        bar.querySelectorAll(".fv").forEach(function(x){ x.classList.remove("on"); });
        c.classList.add("on"); applyFilter();
      });
    });
    applyFilter();
  }

  /* ---------- 7. LIVE VARIABLES ----------
   * Bodies carry <span class="wfvar" data-var="client_id"></span>; a shared bar has
   * <input data-var-input="client_id" value="RJ4521">. Typing updates every chip at once;
   * empty value → the chip shows {{var_name}}. */
  function varFill(name,val){
    document.querySelectorAll('.wfvar[data-var="'+name+'"]').forEach(function(s){
      if(val){ s.textContent=val; s.classList.remove("empty"); }
      else{ s.textContent="{{"+name+"}}"; s.classList.add("empty"); }
      s.title="{{"+name+"}}";
    });
  }
  function varWire(){
    document.querySelectorAll("[data-var-input]").forEach(function(inp){
      var name=inp.getAttribute("data-var-input");
      varFill(name, inp.value);
      inp.addEventListener("input",function(){ varFill(name, inp.value); });
    });
  }

  function boot(){ phoneStamp(); navWire(); audit(); varWire(); filterWire(); wireAll(); }
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",boot); else boot();
})();

/* ---------- 5. ZOOM + DRAG (lineage module, unchanged contract) ----------
 * Markup: .controls with #zout #zlab #zin #zreset #lreset; wrappers #viewport > #zoomable.
 * Drag offsets go to left/top so animations' transforms are untouched; a drag that moves
 * >4px suppresses the tap-navigation click that follows it. */
(function(){
  var Z=1, ZMIN=.5, ZMAX=2;
  var zoomable=document.getElementById("zoomable"), vp=document.getElementById("viewport"),
      zlab=document.getElementById("zlab");
  if(!zoomable||!vp) return;
  var lastWire=0;
  function wireNow(){ var n=Date.now(); if(n-lastWire>16){ lastWire=n; window.wireAll&&window.wireAll(); } }
  function applyZoom(nz){
    Z=Math.min(ZMAX,Math.max(ZMIN,Math.round(nz*100)/100));
    zoomable.style.transform= Z===1 ? "" : "scale("+Z+")";
    vp.style.height= Z===1 ? "" : (zoomable.offsetHeight*Z)+"px";
    if(zlab) zlab.textContent=Math.round(Z*100)+"%";
    window.wireAll&&window.wireAll();
  }
  var zin=document.getElementById("zin"), zout=document.getElementById("zout"), zreset=document.getElementById("zreset");
  if(zin) zin.addEventListener("click",function(){applyZoom(Z+.15)});
  if(zout) zout.addEventListener("click",function(){applyZoom(Z-.15)});
  if(zreset) zreset.addEventListener("click",function(){applyZoom(1)});
  vp.addEventListener("wheel",function(e){
    if(!e.ctrlKey) return; e.preventDefault();
    applyZoom(Z + (e.deltaY<0 ? .1 : -.1));
  },{passive:false});

  var drag=null;
  document.querySelectorAll(".node").forEach(function(node){
    node.addEventListener("pointerdown",function(e){
      if(e.button!==undefined && e.button!==0) return;
      drag={node:node, sx:e.clientX, sy:e.clientY, moved:false, pid:e.pointerId,
            ox:parseFloat(node.dataset.ox||0), oy:parseFloat(node.dataset.oy||0)};
      /* NO pointer capture here — capturing on press retargets the tap's click at the
       * card and kills button navigation. Capture only once a drag actually starts. */
    });
    node.addEventListener("pointermove",function(e){
      if(!drag||drag.node!==node) return;
      var dx=e.clientX-drag.sx, dy=e.clientY-drag.sy;
      if(!drag.moved && dx*dx+dy*dy<16) return;      /* 4px dead zone keeps taps clickable */
      if(!drag.moved){
        drag.moved=true; node.classList.add("dragging");
        try{ node.setPointerCapture&&node.setPointerCapture(drag.pid); }catch(_){}
        window.WF_setSuppress&&window.WF_setSuppress(true);
      }
      var nx=drag.ox+dx/Z, ny=drag.oy+dy/Z;
      node.dataset.ox=nx; node.dataset.oy=ny;
      node.style.left=nx+"px"; node.style.top=ny+"px";
      wireNow();
    });
    function end(){
      if(!drag||drag.node!==node) return;
      var moved=drag.moved;
      node.classList.remove("dragging"); drag=null;
      window.wireAll&&window.wireAll();
      if(moved) setTimeout(function(){ window.WF_setSuppress&&window.WF_setSuppress(false); },0);
    }
    node.addEventListener("pointerup",end);
    node.addEventListener("pointercancel",end);
  });
  var lreset=document.getElementById("lreset");
  if(lreset) lreset.addEventListener("click",function(){
    document.querySelectorAll(".node").forEach(function(n){
      n.style.left=""; n.style.top=""; delete n.dataset.ox; delete n.dataset.oy;
    });
    window.wireAll&&window.wireAll();
  });
})();
