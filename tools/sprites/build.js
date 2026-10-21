/* Sinh lại sprite sheet: node tools/sprites/build.js
   Cần Playwright + Chromium. Ghi PNG vào assets/sprites/ và một bảng xem trước preview.png (phóng to 4 lần). */
const path = require('path'), fs = require('fs');
let chromium; try{ ({chromium} = require('playwright')); }catch(e){ ({chromium} = require('/opt/node-tools/node_modules/playwright')); }
(async()=>{
  const out = path.join(__dirname, '..', '..', 'assets', 'sprites'); fs.mkdirSync(out, {recursive:true});
  const b = await chromium.launch(fs.existsSync('/opt/pw-browsers/chromium-1194/chrome-linux/chrome') ? {executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'} : {});
  const p = await b.newPage();
  await p.setContent('<html><body></body></html>');
  await p.addScriptTag({path:path.join(__dirname, 'pixel-gen.js')});
  const res = await p.evaluate(()=>{
    const all = PixelGen.genAll(), o = {};
    for(const k in all) o[k] = all[k].toDataURL('image/png');
    // bảng xem trước
    const names = Object.keys(all), S = 4, pad = 8;
    let W = 0, H = pad; names.forEach(n=>{ W = Math.max(W, all[n].width*S + pad*2); H += all[n].height*S + pad; });
    const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d'); x.imageSmoothingEnabled = false;
    x.fillStyle = '#20262a'; x.fillRect(0, 0, W, H); let y = pad;
    names.forEach(n=>{ x.drawImage(all[n], pad, y, all[n].width*S, all[n].height*S); y += all[n].height*S + pad; });
    o.__preview = c.toDataURL('image/png');
    return o;
  });
  for(const k in res){ const f = k==='__preview' ? path.join(__dirname, 'preview.png') : path.join(out, k + '.png'); fs.writeFileSync(f, Buffer.from(res[k].split(',')[1], 'base64')); console.log('wrote', path.relative(process.cwd(), f)); }
  await b.close();
})();
