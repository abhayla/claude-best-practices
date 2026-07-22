/* Modern-data-pipeline-diagram wiring engine — drop inline in a <script> tag.
 * Requires: each panel is <div class="stage"><svg class="wires" data-edges="a>b:live,b>c:build"></svg> ... nodes with id ... </div>
 * Semantic edge kinds (live/build/design) map to CSS classes on the <path>. Exposes wireAll().
 * Honors prefers-reduced-motion (static wires, no packets, no ambient field). */
(function(){
  var RM = window.matchMedia && matchMedia("(prefers-reduced-motion:reduce)").matches;

  function anchor(a,b,cb){
    var acx=a.left+a.width/2-cb.left, acy=a.top+a.height/2-cb.top;
    var bcx=b.left+b.width/2-cb.left, bcy=b.top+b.height/2-cb.top;
    var dx=bcx-acx, dy=bcy-acy, p1,p2;
    if(Math.abs(dx)>=Math.abs(dy)){                       // horizontal: right <-> left edges
      p1=[a.left+(dx>=0?a.width:0)-cb.left, acy];
      p2=[b.left+(dx>=0?0:b.width)-cb.left, bcy];
    }else{                                                // vertical: bottom <-> top edges
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
      var kind=m[3]||"live";
      var pts=anchor(A.getBoundingClientRect(),B.getBoundingClientRect(),cb), p1=pts[0],p2=pts[1],horiz=pts[2];
      var mx=(p1[0]+p2[0])/2, my=(p1[1]+p2[1])/2, c1,c2;
      if(horiz){ c1=[mx,p1[1]]; c2=[mx,p2[1]]; } else { c1=[p1[0],my]; c2=[p2[0],my]; }
      var d="M "+p1[0]+" "+p1[1]+" C "+c1[0]+" "+c1[1]+" "+c2[0]+" "+c2[1]+" "+p2[0]+" "+p2[1];
      var id="pth-"+(stage.dataset.k||"")+i+"-"+Math.floor(mx);
      var path=document.createElementNS("http://www.w3.org/2000/svg","path");
      path.setAttribute("d",d); path.setAttribute("id",id); path.setAttribute("class","flowing "+kind);
      svg.appendChild(path);
      if(!RM){                                            // travelling packet along the wire
        var pkt=document.createElementNS("http://www.w3.org/2000/svg","circle");
        pkt.setAttribute("r","3.4"); pkt.setAttribute("class","pkt"+(kind==="build"?" build":""));
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

  if("IntersectionObserver" in window && !RM){
    var io=new IntersectionObserver(function(en){en.forEach(function(x){
      if(x.isIntersecting){ x.target.classList.add("in"); io.unobserve(x.target); setTimeout(wireAll,60);} })},{threshold:.12});
    document.querySelectorAll(".reveal").forEach(function(el){io.observe(el)});
    /* Failsafe: IO callbacks never run in a hidden/embedded tab — content must still show. */
    setTimeout(function(){ document.querySelectorAll(".reveal:not(.in)").forEach(function(el){el.classList.add("in")}); wireAll(); },1500);
  } else document.querySelectorAll(".reveal").forEach(function(el){el.classList.add("in")});

  /* Optional ambient signal field — attach to <canvas id="spark"> in a hero. */
  var cv=document.getElementById("spark");
  if(cv && !RM){
    var ctx=cv.getContext("2d"), W,H,pts,DPR=window.devicePixelRatio||1;
    function size(){ var r=cv.parentElement.getBoundingClientRect(); W=cv.width=r.width*DPR; H=cv.height=r.height*DPR; }
    function seed(){ pts=[]; var n=Math.min(46,Math.floor(W/38)); for(var i=0;i<n;i++) pts.push({x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-.5)*.28*DPR,vy:(Math.random()-.5)*.28*DPR}); }
    function tick(){
      ctx.clearRect(0,0,W,H);
      for(var i=0;i<pts.length;i++){ var p=pts[i]; p.x+=p.vx; p.y+=p.vy;
        if(p.x<0||p.x>W)p.vx*=-1; if(p.y<0||p.y>H)p.vy*=-1;
        for(var j=i+1;j<pts.length;j++){ var q=pts[j],dx=p.x-q.x,dy=p.y-q.y,dd=dx*dx+dy*dy,mx=(150*DPR)*(150*DPR);
          if(dd<mx){ var a=(1-dd/mx)*.4; ctx.strokeStyle="rgba(79,209,197,"+a+")"; ctx.lineWidth=DPR*.6; ctx.beginPath(); ctx.moveTo(p.x,p.y); ctx.lineTo(q.x,q.y); ctx.stroke(); } } }
      for(var k=0;k<pts.length;k++){ ctx.fillStyle="rgba(52,229,164,.7)"; ctx.beginPath(); ctx.arc(pts[k].x,pts[k].y,DPR*1.3,0,7); ctx.fill(); }
      requestAnimationFrame(tick);
    }
    function boot(){ size(); seed(); } boot(); tick();
    var rt; window.addEventListener("resize",function(){ clearTimeout(rt); rt=setTimeout(boot,150); });
  }
})();
