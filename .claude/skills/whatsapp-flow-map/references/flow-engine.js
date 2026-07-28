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
        '</span><span class="ph-who"><b></b><i></i></span><span class="ph-link" title="copy link to this card">&#128279;</span>';
      head.querySelector("b").textContent=who; head.querySelector("i").textContent=sub;
      head.querySelector(".ph-link").addEventListener("click",function(e){
        e.stopPropagation();
        var base=(document.getElementById("wffilter")||document.body).getAttribute("data-canonical")||"";
        var url=base+"#"+node.id;
        try{ navigator.clipboard.writeText(url).then(function(){ e.target.textContent="✓"; setTimeout(function(){e.target.innerHTML="&#128279;";},900); }); }
        catch(_){ window.prompt("Copy link:",url); }
      });
      if(node.getAttribute("data-upd")){
        var d=new Date(node.getAttribute("data-upd"));
        var chip=document.createElement("span"); chip.className="updchip";
        chip.textContent=d.getDate()+" "+["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][d.getMonth()];
        var eye=node.querySelector(".eye"); if(eye) eye.appendChild(chip);
      }
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
      var show;
      if(v){ show=(v===ver); }
      else { show=(on[st]!==false); }
      /* recent-7d chip narrows whatever is otherwise visible */
      var rc=bar.querySelector('.fc[data-age].on');
      if(show && rc){
        var u=n.getAttribute("data-upd");
        show=!!u && (Date.now()-Date.parse(u))<=7*86400000;
      }
      n.style.display=show?"":"none";
    });
    window.wireAll&&window.wireAll();
    window.__lintRun&&window.__lintRun();
  }
  function filterWire(){
    var bar=document.getElementById("wffilter"); if(!bar) return;
    bar.querySelectorAll(".fc").forEach(function(c){
      c.addEventListener("click",function(){ c.classList.toggle("on"); applyFilter(); });
    });
    bar.querySelectorAll(".flang").forEach(function(c){
      c.addEventListener("click",function(){
        bar.querySelectorAll(".flang").forEach(function(x){ x.classList.remove("on"); });
        c.classList.add("on");
        var hi=c.dataset.lang==="hi";
        document.body.classList.toggle("himode",hi);
        document.querySelectorAll(".node").forEach(function(n){
          if(n.classList.contains("ext")) return;
          var has=n.querySelector('[data-lang="hi"]');
          n.classList.toggle("hi-missing", hi && !has && !!n.querySelector(".btxt"));
        });
        window.__lintRun&&window.__lintRun();
      });
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

  /* ---------- 8. SEARCH — #wfsearch input in the filter bar ---------- */
  function searchWire(){
    var inp=document.getElementById("wfsearch"); if(!inp) return;
    var hits=[], idx=-1;
    function clearHits(){ hits.forEach(function(n){ n.classList.remove("hit"); }); hits=[]; idx=-1; }
    function focusHit(){
      var n=hits[idx]; if(!n) return;
      n.scrollIntoView({behavior:RM?"auto":"smooth", block:"center", inline:"center"});
      document.querySelectorAll(".node.rx").forEach(function(x){ x.classList.remove("rx"); });
      void n.offsetWidth; n.classList.add("rx");
    }
    function run(){
      clearHits();
      var q=inp.value.trim().toLowerCase(); if(q.length<2) return;
      document.querySelectorAll(".node").forEach(function(n){
        if(n.offsetWidth===0) return;
        if(n.textContent.toLowerCase().indexOf(q)>=0 || (n.id||"").toLowerCase().indexOf(q)>=0){
          n.classList.add("hit"); hits.push(n);
        }
      });
      if(hits.length){ idx=0; focusHit(); }
    }
    var t; inp.addEventListener("input",function(){ clearTimeout(t); t=setTimeout(run,250); });
    inp.addEventListener("keydown",function(e){
      if(e.key==="Enter" && hits.length){ idx=(idx+1)%hits.length; focusHit(); }
      if(e.key==="Escape"){ inp.value=""; clearHits(); }
    });
  }

  /* ---------- 9. DEEP LINKS — #card-id opens centered+pulsed; filters auto-enable ---------- */
  function deepLink(){
    var id=(location.hash||"").replace(/^#/,""); if(!id) return;
    var el=document.getElementById(id); if(!el) return;
    var n=el.closest(".node")||el;
    var bar=document.getElementById("wffilter");
    if(bar && n.offsetWidth===0){
      var v=n.getAttribute("data-ver");
      if(v) bar.querySelectorAll(".fv").forEach(function(x){ x.classList.toggle("on",x.dataset.ver===v); });
      var b=n.querySelector(".bstat"), st="info";
      if(b) ["live","build","design","review","retire"].forEach(function(k){ if(b.classList.contains(k)) st=k; });
      var chip=bar.querySelector('.fc[data-state="'+st+'"]'); if(chip) chip.classList.add("on");
      applyFilter();
    }
    setTimeout(function(){
      n.scrollIntoView({behavior:RM?"auto":"smooth", block:"center", inline:"center"});
      n.classList.add("rx");
      setTimeout(function(){ n.classList.remove("rx"); },4000);
    },400);
  }

  /* ---------- 10. CATEGORY-COST LENS — #wflens toggle + #wflenscount ---------- */
  function lensWire(){
    document.querySelectorAll(".node").forEach(function(n){
      var c=n.querySelector(".eye .cat"), cat="session";
      if(n.classList.contains("out")) cat="customer";
      else if(n.classList.contains("ext")) cat="external";
      else if(c){
        if(c.classList.contains("mkt")) cat="mkt";
        else if(c.classList.contains("util")) cat="util";
        else if(c.classList.contains("int")) cat="internal";
      }
      n.dataset.cat=cat;
    });
    var btn=document.getElementById("wflens"), lab=document.getElementById("wflenscount");
    if(!btn) return;
    btn.addEventListener("click",function(){
      var on=document.body.classList.toggle("catlens");
      btn.classList.toggle("on",on);
      if(lab){
        if(on){
          var ct={};
          document.querySelectorAll(".node").forEach(function(n){ if(n.offsetWidth>0) ct[n.dataset.cat]=(ct[n.dataset.cat]||0)+1; });
          lab.textContent=(ct.mkt||0)+" MKT · "+(ct.util||0)+" UTILITY · "+(ct.session||0)+" session · "+(ct.internal||0)+" internal";
        } else lab.textContent="";
      }
    });
  }

  /* ---------- 11. INVARIANT LINT — #wflint pill (auto-created, bottom-left) ---------- */
  function lintWire(){
    var pill=document.createElement("div"); pill.id="wflint"; document.body.appendChild(pill);
    var flags=[], idx=-1;
    window.__lintRun=function(){
      flags=[]; idx=-1;
      document.querySelectorAll(".node").forEach(function(n){
        if(n.style.display==="none") return;
        if(n.getAttribute("data-ver")==="previous") return;
        var st=n.querySelector(".bstat");
        if(st && st.classList.contains("retire")) return;
        var body=n.querySelector(".btxt"); if(!body) return;
        var txt=body.textContent, msgs=[];
        var isCust=!n.classList.contains("int") && !n.classList.contains("ext") && !n.classList.contains("out") && !n.classList.contains("kw");
        var btns=n.querySelectorAll(".qr .b");
        if(isCust && !n.hasAttribute("data-terminal") && btns.length===0) msgs.push(["amber","ends bare — no next-action buttons"]);
        if(btns.length>3) msgs.push(["amber",btns.length+" buttons > 3 (use a list message)"]);
        if(isCust && /\bAshok\b/.test(txt)) msgs.push(["red","staff name in customer copy"]);
        if(isCust && /credited|₹\s?\d/.test(txt)) msgs.push(["red","reward amount / credited claim"]);
        if(isCust && /(10% brokerage|reward points)/i.test(txt) && txt.indexOf("gorefer.in/d/pifs")<0) msgs.push(["red","referral terms without disclosure link"]);
        btns.forEach(function(b){
          var lbl=b.textContent.replace(/UNWIRED$/,"").trim().replace(/^[^A-Za-z0-9ऀ-ॿ(]+\s*/,"");
          if(lbl.length>20) msgs.push(["amber",'label "'+lbl+'" '+lbl.length+">20 chars"]);
        });
        if(document.body.classList.contains("himode") && n.classList.contains("hi-missing")) msgs.push(["grey","HI twin not recorded"]);
        if(msgs.length) flags.push({n:n,msgs:msgs});
      });
      var red=0,amber=0,grey=0;
      flags.forEach(function(f){ f.msgs.forEach(function(m){ if(m[0]==="red")red++; else if(m[0]==="amber")amber++; else grey++; }); });
      if(!flags.length){ pill.className="ok"; pill.textContent="rules clean ✓"; }
      else { pill.className="bad"; pill.textContent="⚠ rules: "+red+" red · "+amber+" amber"+(grey?" · "+grey+" grey":"")+" — click to step"; }
    };
    pill.addEventListener("click",function(){
      if(!flags.length) return;
      idx=(idx+1)%flags.length;
      var f=flags[idx];
      f.n.scrollIntoView({behavior:RM?"auto":"smooth", block:"center", inline:"center"});
      document.querySelectorAll(".node.rx").forEach(function(x){ x.classList.remove("rx"); });
      void f.n.offsetWidth; f.n.classList.add("rx");
      pill.textContent="rule "+(idx+1)+"/"+flags.length+": "+f.msgs.map(function(m){ return m[1]; }).join(" · ");
    });
    window.__lintRun();
  }

  /* ---------- 12. CONVERSATION SIMULATOR — ▶ on data-entry cards + free-text composer ----------
   * Free text routes through #wfroutes — the LIVE-VERIFIED keyword registry (rules with
   * literal keywords, exact/contains, on/off, per-keyword target card) + the verified
   * default behavior. Faithful mode: what production does. Design hints (clearly marked)
   * come from the map's typed-intent cards. An open question/collector card (data-question)
   * consumes typed input BEFORE keyword routing — the live trap class, modeled honestly. */
  var ROUTES=null;
  try{ var rEl=document.getElementById("wfroutes"); if(rEl) ROUTES=JSON.parse(rEl.textContent); }catch(_){ ROUTES=null; }
  var simPane=null, simThread=null, simCrumbs=null, simStack=[], simLastCard=null;
  function simClose(){ if(simPane){ simPane.remove(); simPane=null; simStack=[]; } }
  function simPulse(n){
    document.querySelectorAll(".node.simhl").forEach(function(x){ x.classList.remove("simhl"); });
    n.classList.add("simhl");
  }
  function crumbLabel(n){
    var eye=n.querySelector(".eye"), t=n.id;
    if(eye){
      var cl=eye.cloneNode(true);
      cl.querySelectorAll(".updchip,.cat").forEach(function(x){ x.remove(); });
      t=cl.textContent.trim();
    }
    return (t||n.id).slice(0,34);
  }
  function simAppendGroup(els){ simStack.push(els); }
  function simMsg(node){
    var bub=node.querySelector(".bub"); if(!bub) return;
    var cl=bub.cloneNode(true);
    var bs=cl.querySelector(".bstat"); if(bs) bs.remove();
    var fx=cl.querySelector(".fixnote"); if(fx) fx.remove();
    var wrap=document.createElement("div");
    wrap.className="sim-msg "+(node.classList.contains("out")?"sim-out":"sim-in");
    wrap.appendChild(cl);
    /* rewire cloned buttons to sim taps */
    cl.querySelectorAll(".qr .b").forEach(function(b){
      var id=b.getAttribute("id"); b.removeAttribute("id");
      b.classList.remove("unwired");
      b.addEventListener("click",function(e){
        e.stopPropagation();
        simTap(id, b.textContent.replace(/UNWIRED$/,"").trim());
      });
    });
    simThread.appendChild(wrap);
    simThread.scrollTop=simThread.scrollHeight;
    simCrumbs.textContent+=(simCrumbs.textContent?" → ":"")+crumbLabel(node);
    simPulse(node);
    simLastCard=node;
    return wrap;
  }
  function simNote(cls,text){
    var d=document.createElement("div"); d.className=cls; d.textContent=text;
    simThread.appendChild(d); simThread.scrollTop=simThread.scrollHeight;
    return d;
  }
  function intentHint(text,group){
    /* design-intent bank = the map's typed-intent cards wired to guardrails (NOT live routing) */
    var bank=[]; (ROUTES&&ROUTES.intents||[]).forEach(function(i){ bank.push(i); });
    var words=text.toLowerCase().split(/[^a-zऀ-ॿ0-9]+/).filter(function(w){return w.length>3;});
    var best=null,bestScore=0;
    bank.forEach(function(i){
      var s=0; words.forEach(function(w){ if(i.text.toLowerCase().indexOf(w)>=0) s++; });
      if(s>bestScore){ bestScore=s; best=i; }
    });
    if(!best) return;
    var d=document.createElement("div"); d.className="sim-hint";
    d.appendChild(document.createTextNode("design intent (NOT live behavior): similar to “"+best.text+"” → "));
    var b=document.createElement("span"); b.className="sim-pick"; b.textContent="show intended reply";
    b.addEventListener("click",function(){
      var n=nodeOf(best.target); if(!n) return;
      d.remove();
      var w=simMsg(n); if(w){ group.push(w); }
      var tag=simNote("sim-hint","↑ design card — this reply is NOT wired live yet");
      group.push(tag);
    });
    d.appendChild(b);
    simThread.appendChild(d); simThread.scrollTop=simThread.scrollHeight;
    group.push(d);
  }
  function simType(text){
    text=text.trim(); if(!text) return;
    var group=[];
    var tap=document.createElement("div"); tap.className="sim-msg sim-out";
    tap.innerHTML='<div class="sim-tap"></div>'; tap.querySelector(".sim-tap").textContent=text;
    simThread.appendChild(tap); group.push(tap);
    var firstMsg=!simLastCard;
    /* 1. an open question/collector card consumes input before any keyword routing */
    if(simLastCard && simLastCard.hasAttribute("data-question")){
      group.push(simNote("sim-sys","✉ captured by the open collector/question ("+crumbLabel(simLastCard)+") — validators apply; keyword routing is SUSPENDED until it completes or 3 failed answers (live-verified behavior)"));
      simAppendGroup(group); return;
    }
    /* 2. live keyword rules (literal, case-sensitive as enumerated live) */
    var hit=null, disabledHit=null;
    (ROUTES&&ROUTES.routes||[]).forEach(function(r){
      if(hit) return;
      var m=(r.m==="exact") ? (r.k===text) : (text.indexOf(r.k)>=0);
      if(m){ if(r.on) hit=r; else if(!disabledHit) disabledHit=r; }
    });
    if(hit){
      var n=nodeOf(hit.t);
      if(n){ var w=simMsg(n); if(w) group.push(w); }
      simAppendGroup(group); return;
    }
    if(disabledHit){
      group.push(simNote("sim-dead","⚠ matches rule “"+disabledHit.name+"” — but that rule is DISABLED live (verified "+(ROUTES.verified||"")+") → falls through to default"));
    }
    /* 3. default behavior (live-verified) */
    if(firstMsg && ROUTES && ROUTES.dflt && ROUTES.dflt.welcome){
      var wn=nodeOf(ROUTES.dflt.welcome);
      group.push(simNote("sim-sys","new conversation → welcome flow fires (verified: welcome ON, once per new chat)"));
      if(wn){ var w2=simMsg(wn); if(w2) group.push(w2); }
    } else {
      group.push(simNote("sim-sys","no keyword rule matches → LIVE DEFAULT: no bot reply (fallback slot OFF, verified "+(ROUTES?ROUTES.verified:"")+"). In working hours an agent is expected (R2 nudge after ~3 min, once); off-hours → R1 auto-reply (once per session)."));
      intentHint(text,group);
    }
    simAppendGroup(group);
  }
  function simTap(id,label){
    var group=[];
    var tap=document.createElement("div"); tap.className="sim-msg sim-out";
    tap.innerHTML='<div class="sim-tap"></div>'; tap.querySelector(".sim-tap").textContent=label;
    simThread.appendChild(tap); group.push(tap);
    var outs=id?REG[id]:null;
    if(!outs||!outs.length){
      var d=document.createElement("div"); d.className="sim-dead";
      d.textContent="⚠ dead end — this tap is not wired to any reply";
      simThread.appendChild(d); group.push(d);
      simThread.scrollTop=simThread.scrollHeight;
      simAppendGroup(group); return;
    }
    var seen={}, targets=[];
    outs.forEach(function(o){ var n=nodeOf(o.to); if(n && !seen[n.id]){ seen[n.id]=1; targets.push(n); } });
    if(targets.length===1){ var w=simMsg(targets[0]); if(w) group.push(w); }
    else{
      var ch=document.createElement("div"); ch.className="sim-choice";
      ch.appendChild(document.createTextNode(targets.length+" possible replies — pick one: "));
      targets.forEach(function(t){
        var b=document.createElement("span"); b.className="sim-pick"; b.textContent=crumbLabel(t);
        b.addEventListener("click",function(){ ch.remove(); var w=simMsg(t); if(w) simStack[simStack.length-1].push(w); });
        ch.appendChild(b);
      });
      simThread.appendChild(ch); group.push(ch);
    }
    simThread.scrollTop=simThread.scrollHeight;
    simAppendGroup(group);
  }
  function simStart(entry){
    simClose();
    simPane=document.createElement("div"); simPane.id="wfsim";
    simPane.innerHTML='<div class="sim-head"><span class="ph-av">P</span><b>Simulator</b>'+
      '<span class="sim-ctl" data-a="undo" title="undo last tap">&#8617;</span>'+
      '<span class="sim-ctl" data-a="restart" title="restart">&#10226;</span>'+
      '<span class="sim-ctl" data-a="close" title="close">&#10005;</span></div>'+
      '<div class="sim-crumbs"></div><div class="sim-thread"></div>'+
      '<div class="sim-compose"><input type="text" placeholder="Type a message as the customer…"><span class="sim-send">➤</span></div>';
    document.body.appendChild(simPane);
    simThread=simPane.querySelector(".sim-thread");
    simCrumbs=simPane.querySelector(".sim-crumbs");
    simLastCard=null;
    var cin=simPane.querySelector(".sim-compose input");
    function sendTyped(){ var v=cin.value; cin.value=""; simType(v); }
    cin.addEventListener("keydown",function(e){ if(e.key==="Enter") sendTyped(); });
    simPane.querySelector(".sim-send").addEventListener("click",sendTyped);
    simPane.querySelectorAll(".sim-ctl").forEach(function(c){
      c.addEventListener("click",function(){
        var a=c.dataset.a;
        if(a==="close") simClose();
        else if(a==="restart"){ simThread.innerHTML=""; simCrumbs.textContent=""; simStack=[]; simLastCard=null; if(entry){ simMsg(entry); if(entry.classList.contains("out")&&entry.id&&REG[entry.id]) simFollow(entry.id); } }
        else if(a==="undo"){
          var g=simStack.pop();
          if(g) g.forEach(function(el){ el.remove(); });
          var parts=simCrumbs.textContent.split(" → "); parts.pop(); simCrumbs.textContent=parts.join(" → ");
        }
      });
    });
    if(entry){
      simMsg(entry);
      if(entry.classList.contains("out") && entry.id && REG[entry.id]) simFollow(entry.id);
    } else {
      simNote("sim-sys","new empty chat — type the customer's first message below");
    }
  }
  function simFollow(id){
    var outs=REG[id]||[], seen={}, group=[];
    outs.forEach(function(o){ var n=nodeOf(o.to); if(n && !seen[n.id]){ seen[n.id]=1; var w=simMsg(n); if(w) group.push(w); } });
    if(group.length) simAppendGroup(group);
  }
  function simWire(){
    document.querySelectorAll(".node[data-entry]").forEach(function(n){
      var head=n.querySelector(".ph-head"); if(!head) return;
      var b=document.createElement("span"); b.className="ph-play"; b.title="Play this conversation"; b.textContent="▶";
      b.addEventListener("click",function(e){ e.stopPropagation(); simStart(n); });
      head.insertBefore(b, head.querySelector(".ph-link"));
    });
    var nc=document.getElementById("wfnewchat");
    if(nc) nc.addEventListener("click",function(){ simStart(null); });
  }

  function boot(){
    phoneStamp(); navWire(); audit(); varWire(); filterWire();
    searchWire(); lensWire(); lintWire(); simWire(); deepLink(); wireAll();
  }
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
