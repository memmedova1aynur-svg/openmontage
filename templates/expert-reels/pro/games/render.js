// İstifadə: node render.js <səhifə.html> <kadr_qovluğu> [query] [test_saniyələri]
const { chromium } = require('playwright'); const fs=require('fs'); const path=require('path');
const [PAGE,OUTD,Q='',ONLY]=process.argv.slice(2); const FPS=30;
(async()=>{const b=await chromium.launch();const pg=await b.newPage({viewport:{width:1080,height:1920}});
 const errs=[];pg.on('pageerror',e=>errs.push(String(e)));
 await pg.goto('file://'+path.resolve(PAGE)+(Q?'?'+Q:''));await pg.waitForLoadState('networkidle');
 await pg.evaluate(async()=>{for(const w of [500,700,800,900])await document.fonts.load(w+' 60px Montserrat');await document.fonts.load('italic 600 40px Lora');await document.fonts.load('700 40px "JetBrains Mono"');await document.fonts.load('60px "Noto Color Emoji"');await document.fonts.ready});
 if(errs.length){console.error('SƏHİFƏ XƏTASI:',errs.join(' | '));process.exit(2)}
 fs.mkdirSync(OUTD,{recursive:true});
 const T=await pg.evaluate(()=>window.TIMES); const N=Math.round(T.TOTAL*FPS);
 if(ONLY){for(const s of ONLY.split(',')){await pg.evaluate(t=>renderFrame(t),+s);await pg.screenshot({path:path.join(OUTD,`test_${s}.jpg`),type:'jpeg',quality:80});}await b.close();return}
 for(let i=0;i<N;i++){await pg.evaluate(t=>renderFrame(t),i/FPS);await pg.screenshot({path:path.join(OUTD,String(i).padStart(5,'0')+'.jpg'),type:'jpeg',quality:95});}
 fs.writeFileSync(path.join(OUTD,'events.json'),JSON.stringify({T,E:await pg.evaluate(()=>window.EVENTS)}));console.log('kadr',N,'müddət',T.TOTAL);await b.close()})();
