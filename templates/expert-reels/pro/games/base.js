// ümumi köməkçilər + səs hadisələri
const cl=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
const eo=x=>1-Math.pow(1-cl(x),3);
const eio=x=>{x=cl(x);return x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2};
const back=x=>{x=cl(x);const c=1.7;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
const $=id=>document.getElementById(id);
function inn(el,t,t0,dy=40,d=.5){const p=eo((t-t0)/d);el.style.opacity=p;el.style.transform=`translateY(${(1-p)*dy}px)`}
function out(el,t,t0,d=.3){if(t>=t0){el.style.opacity=Math.min(+el.style.opacity||1,1-cl((t-t0)/d))}}
window.EVENTS=[];const ev=(t,type,v=0)=>EVENTS.push({t:+t.toFixed(3),type,v});
const THEMES={
 dark:{bg:"radial-gradient(120% 70% at 85% 0%,#1D6A50 0%,#0E3A2B 45%,#05170F 100%)",dot:"rgba(255,255,255,.06)",txt:"#F2F6EF",mut:"#97B1A3",acc:"#6CC57E",onacc:"#0B2A20",mk:"linear-gradient(90deg,#3E9E57 0%,#6CC57E 50%,#B5E9CF 100%)",onmk:"#0B2A20",em:"#6CC57E",glass:"rgba(255,255,255,.07)",gb:"rgba(255,255,255,.16)",tile:"rgba(255,255,255,.08)"},
 light:{bg:"radial-gradient(120% 70% at 85% 0%,#E3F2E7 0%,#F7FAF8 45%,#FFFFFF 100%)",dot:"rgba(15,59,44,.07)",txt:"#0F3B2C",mut:"#5E7266",acc:"#0F3B2C",onacc:"#B5E9CF",mk:"linear-gradient(90deg,#3E9E57 0%,#6CC57E 50%,#B5E9CF 100%)",onmk:"#0B2A20",em:"#2F7D40",glass:"#F2F7F3",gb:"rgba(15,59,44,.14)",tile:"#F2F7F3"},
 green:{bg:"radial-gradient(120% 70% at 85% 0%,#A5DDB1 0%,#7CCB8C 38%,#62BC75 100%)",dot:"rgba(11,42,32,.09)",txt:"#0B2A20",mut:"#2F5A3A",acc:"#0B2A20",onacc:"#7FD08F",mk:"#0B2A20",onmk:"#7FD08F",em:"#0B2A20",glass:"rgba(255,255,255,.5)",gb:"rgba(11,42,32,.25)",tile:"rgba(255,255,255,.45)"}};
function theme(n){const T=THEMES[n];const r=document.documentElement.style;for(const k in T)r.setProperty('--'+k,T[k]);$('bg').style.background=T.bg;$('dots').style.backgroundImage=`radial-gradient(${T.dot} 2px,transparent 2.5px)`}
const CHAT='<svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';
// ekspert adı: ?name=... (default səhifədəki ad)
(function(){const q=new URLSearchParams(location.search);const n=q.get('name');const c=document.getElementById('chip');if(n&&c){c.innerHTML='<i></i>'+n.replace(/[<>&]/g,'')}})();
