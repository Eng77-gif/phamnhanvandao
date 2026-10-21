/* =====================================================================
   Bộ sinh sprite sheet pixel-art cho Thế Giới 2D.
   Chạy trong trình duyệt (cần <canvas>): genAll() trả về {tên: canvas}.
   tools/sprites/build.js mở tệp này bằng Chromium và lưu ra assets/sprites/.

   Định dạng sheet giống bản xuất của PixelLab (4 hướng):
   - hero-*.png, mob-bandit.png: khung 24×32, hàng = hướng (xuống, trái, phải, lên),
     cột = đứng, đi 1..4, đánh  → 6×4 khung.
   - mob-beast/snake/spirit.png: khung 32×32, hàng 0 quay trái (lật để quay phải),
     cột = 4 khung đi; hàng 1 = 4 khung đánh.
   - tiles.png: ô 16×16, hàng = thế giới (Nhân, Linh, Tiên Giới), cột theo TILE_COLS.
   - objects.png: khung 32×40, hàng = thế giới, cột theo OBJ_COLS.
   - buildings.png, portal.png, fx.png: xem BLD/FX bên dưới.
   Muốn thay bằng tranh PixelLab: xuất cùng kích thước khung và thứ tự hàng/cột rồi ghi đè tệp.
===================================================================== */
(function(root){
const TILE_COLS = ['grass0','grass1','grass2','flower','dirt','plaza','water0','water1','sand','cliff','forest'];
const OBJ_COLS = ['tree','pine','rock','bush','banner','grassTall'];
const DIRS = ['down','left','right','up'];

function rng(seed){ let s = seed|0 || 1; return ()=>{ s ^= s<<13; s ^= s>>>17; s ^= s<<5; return ((s>>>0)%100000)/100000; }; }
function G(w, h){ return {w, h, p:new Array(w*h).fill(null)}; }
function px(g, x, y, c){ x|=0; y|=0; if(c && x>=0 && y>=0 && x<g.w && y<g.h) g.p[y*g.w+x] = c; }
function get(g, x, y){ return (x<0||y<0||x>=g.w||y>=g.h) ? null : g.p[y*g.w+x]; }
function rect(g, x, y, w, h, c){ for(let j=0;j<h;j++) for(let i=0;i<w;i++) px(g, x+i, y+j, c); }
function ell(g, cx, cy, rx, ry, c){ for(let y=Math.floor(cy-ry); y<=Math.ceil(cy+ry); y++) for(let x=Math.floor(cx-rx); x<=Math.ceil(cx+rx); x++){ const dx = (x+.5-cx)/rx, dy = (y+.5-cy)/ry; if(dx*dx+dy*dy <= 1) px(g, x, y, c); } }
function line(g, x0, y0, x1, y1, c){ const n = Math.max(Math.abs(x1-x0), Math.abs(y1-y0)) || 1; for(let k=0;k<=n;k++) px(g, Math.round(x0+(x1-x0)*k/n), Math.round(y0+(y1-y0)*k/n), c); }
function outline(g, c){ const o = g.p.slice(); for(let y=0;y<g.h;y++) for(let x=0;x<g.w;x++){ if(get(g,x,y)) continue; if(get(g,x-1,y)||get(g,x+1,y)||get(g,x,y-1)||get(g,x,y+1)) o[y*g.w+x] = c; } g.p = o; return g; }
function mirror(g){ const m = G(g.w, g.h); for(let y=0;y<g.h;y++) for(let x=0;x<g.w;x++) m.p[y*g.w+x] = g.p[y*g.w + (g.w-1-x)]; return m; }
function blit(ctx, g, ox, oy){ for(let y=0;y<g.h;y++) for(let x=0;x<g.w;x++){ const c = g.p[y*g.w+x]; if(c){ ctx.fillStyle = c; ctx.fillRect(ox+x, oy+y, 1, 1); } } }
function canvas(w, h){ const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

/* ---------- màu ---------- */
function hex2hsl(h){ const r = parseInt(h.slice(1,3),16)/255, g = parseInt(h.slice(3,5),16)/255, b = parseInt(h.slice(5,7),16)/255;
  const mx = Math.max(r,g,b), mn = Math.min(r,g,b), l = (mx+mn)/2; let s = 0, hh = 0;
  if(mx!==mn){ const d = mx-mn; s = l>.5 ? d/(2-mx-mn) : d/(mx+mn); hh = mx===r ? (g-b)/d + (g<b?6:0) : mx===g ? (b-r)/d+2 : (r-g)/d+4; hh /= 6; }
  return [hh*360, s*100, l*100]; }
function hsl(h, s, l){ return `hsl(${Math.round(h)} ${Math.round(Math.max(0,Math.min(100,s)))}% ${Math.round(Math.max(0,Math.min(100,l)))}%)`; }
function shades(hex, sat){ const [h, s] = hex2hsl(hex); const S = sat!=null ? sat : Math.min(70, s); return {dark:hsl(h, S, 22), shade:hsl(h, S, 34), main:hsl(h, S, 48), light:hsl(h, S, 64), hi:hsl(h, S-10, 80)}; }
const OUT = '#1b1420';

/* ---------- tu sĩ 24×32 ---------- */
function hero(dir, f, pal){
  const g = G(24, 32);
  const walk = f>=1 && f<=4, atk = f===5;
  const bob = (f===2 || f===4) ? -1 : 0;
  const swing = f===1 ? 1 : f===3 ? -1 : 0;
  const R = pal.robe, skin = '#f2c9a0', skinS = '#d9a47c', hair = pal.hair || '#2a2230', hairL = pal.hairL || '#4c3e5c', shoe = '#2a2026', belt = pal.belt || '#c9a24a', inner = '#ece6d6';
  const draw = dir===2 ? 1 : dir;  // vẽ hướng trái rồi lật cho hướng phải
  // chân
  if(draw===1){
    const a = swing===1 ? [8,13] : swing===-1 ? [12,10] : [10,13];
    rect(g, a[0], 28, 3, 2, shoe); rect(g, a[1], 28, 2, 2, shoe);
  } else {
    const lf = swing===1 ? 27 : 28, rf = swing===-1 ? 27 : 28;
    rect(g, 8, lf, 3, 2, shoe); rect(g, 13, rf, 3, 2, shoe);
  }
  // áo bào
  const top = 14 + bob;
  for(let y=top; y<=27; y++){
    const t = (y-top)/(27-top);
    const half = draw===1 ? 3 + Math.round(t*1.6) : 3 + Math.round(t*2.2);
    let x0 = 12 - half, x1 = 11 + half;
    if(y===27 && walk) { x0 += swing; x1 += swing; }
    for(let x=x0; x<=x1; x++){
      let c = R.main;
      if(draw===1){ if(x>=x1-1) c = R.shade; if(x===x0) c = R.light; }
      else { if(x>=x1-1) c = R.shade; if(x===x0) c = R.light; }
      if(y===27) c = R.shade;
      px(g, x, y, c);
    }
  }
  if(draw===0){
    px(g, 11, top, inner); px(g, 12, top, inner); px(g, 11, top+1, inner); px(g, 12, top+1, R.shade); px(g, 11, top+2, R.shade);
    rect(g, 8, 19+bob, 8, 1, belt); px(g, 11, 19+bob, pal.beltL || '#f0d58a');
    for(let y=21; y<=26; y++) px(g, 12, y, R.shade);
  } else if(draw===3){
    rect(g, 8, 19+bob, 8, 1, belt);
    for(let y=21; y<=26; y++) px(g, 12, y, R.shade);
  } else {
    rect(g, 9, 19+bob, 6, 1, belt);
    px(g, 9, top, inner); px(g, 9, top+1, inner);
  }
  // tay áo
  const sleeve = (sx, sy, w, h)=>{ rect(g, sx, sy, w, h, R.main); rect(g, sx, sy+h-1, w, 1, R.shade); px(g, sx, sy, R.light); };
  if(atk){
    if(draw===0){ sleeve(5, 15+bob, 3, 6); px(g, 6, 21+bob, skin); sleeve(15, 18, 4, 3); px(g, 18, 21, skin); line(g, 18, 22, 21, 30, '#d8e4ec'); line(g, 19, 22, 22, 30, '#9fb0bc'); px(g, 18, 22, belt); }
    else if(draw===3){ sleeve(5, 15+bob, 3, 6); sleeve(15, 12, 3, 4); px(g, 16, 11, skin); line(g, 17, 10, 19, 1, '#d8e4ec'); line(g, 18, 10, 20, 1, '#9fb0bc'); }
    else { sleeve(4, 17, 6, 3); px(g, 3, 18, skin); line(g, 2, 17, 0, 17, belt); line(g, 2, 18, -4, 18, '#d8e4ec'); line(g, 1, 19, -3, 19, '#9fb0bc'); rect(g, 0, 18, 3, 1, '#d8e4ec'); rect(g, 0, 19, 2, 1, '#9fb0bc'); }
  } else if(draw===1){
    const sx = 11 - swing*2;
    sleeve(sx, 15+bob, 3, 7); px(g, sx+1, 22+bob, skin);
  } else {
    sleeve(5, 15+bob + (walk?swing:0), 3, 6); px(g, 6, 21+bob+(walk?swing:0), skin);
    sleeve(16, 15+bob - (walk?swing:0), 3, 6); px(g, 17, 21+bob-(walk?swing:0), skin);
  }
  // đầu
  const hy = 6 + bob;
  ell(g, 12, hy+4, 4.2, 4.2, hair);
  if(draw===0){
    rect(g, 9, hy+3, 6, 5, skin); rect(g, 10, hy+8, 4, 1, skin); px(g, 9, hy+7, skinS); px(g, 14, hy+7, skinS);
    rect(g, 9, hy+3, 6, 1, hair); px(g, 10, hy+4, hair); px(g, 13, hy+4, hair);
    px(g, 10, hy+5, OUT); px(g, 13, hy+5, OUT); px(g, 10, hy+6, '#e8a0a0'); px(g, 13, hy+6, '#e8a0a0');
    rect(g, 8, hy+3, 1, 6, hair); rect(g, 15, hy+3, 1, 6, hair);
  } else if(draw===1){
    rect(g, 8, hy+3, 4, 5, skin); px(g, 9, hy+8, skin); px(g, 10, hy+8, skin); px(g, 7, hy+5, skin);
    rect(g, 8, hy+3, 4, 1, hair); px(g, 8, hy+4, hair);
    px(g, 9, hy+5, OUT); px(g, 10, hy+7, skinS);
    rect(g, 14, hy+8, 2, 6, hair);
  }
  if(draw===3){ rect(g, 11, hy+8, 2, 5, hair); px(g, 11, hy+9, hairL); }  // đuôi tóc sau lưng
  px(g, 11, hy+1, hairL); px(g, 12, hy+1, hairL); px(g, 10, hy+2, hairL);
  // búi tóc & trâm
  const bx = draw===1 ? 13 : 11;
  ell(g, bx+1, hy-1, 2, 1.8, hair); px(g, bx, hy-2, hairL);
  if(pal.crown){ rect(g, bx-1, hy-1, 4, 1, pal.crown); px(g, bx+1, hy-2, pal.crown); }
  else { line(g, bx-1, hy-2, bx+3, hy-1, belt); }
  if(pal.mask && draw!==3){ if(draw===0) rect(g, 9, hy+6, 6, 3, pal.mask); else rect(g, 7, hy+6, 5, 3, pal.mask); }
  outline(g, OUT);
  return dir===2 ? mirror(g) : g;
}
function heroSheet(pal){
  const c = canvas(24*6, 32*4), x = c.getContext('2d');
  for(let d=0; d<4; d++) for(let f=0; f<6; f++) blit(x, hero(d, f, pal), f*24, d*32);
  return c;
}

/* ---------- yêu thú 32×32 (quay trái) ---------- */
function beast(f, atk, P){
  const g = G(32, 32), lift = atk ? -2 : (f%2 ? -1 : 0);
  const lx = atk ? [0,0,0,0] : [[1,-1,-1,1],[0,0,0,0],[-1,1,1,-1],[0,0,0,0]][f];
  [[10,0],[13,1],[19,2],[22,3]].forEach(([x,i])=>{ const back = i===1 || i===3; rect(g, x+lx[i], 22, 2, 6, back ? P.shade : P.main); rect(g, x+lx[i]-1, 27, 3, 1, P.dark); });
  ell(g, 17, 19+lift, 9, 5.5, P.main); ell(g, 17, 21+lift, 7, 2.5, P.light);
  for(let i=0;i<5;i++) px(g, 13+i*2, 15+lift, P.shade);
  const tail = atk ? -2 : [0,-1,0,1][f];
  line(g, 25, 18+lift, 28, 13+tail+lift, P.main); line(g, 26, 18+lift, 29, 13+tail+lift, P.shade); px(g, 29, 12+tail+lift, P.light);
  const hx = atk ? 6 : 7, hy = (atk ? 14 : 15)+lift;
  ell(g, hx, hy, 4.5, 4, P.main); rect(g, hx-6, hy+1, 4, 3, P.main); rect(g, hx-6, hy+3, 4, 1, P.light);
  line(g, hx-2, hy-3, hx-1, hy-7, P.shade); line(g, hx+1, hy-3, hx+2, hy-7, P.main); px(g, hx+2, hy-6, P.light);
  px(g, hx-2, hy-1, P.eye); px(g, hx-1, hy-1, P.eye); px(g, hx-7, hy+1, P.dark);
  if(atk){ px(g, hx-5, hy+4, '#fff'); px(g, hx-3, hy+4, '#fff'); rect(g, hx-6, hy+4, 4, 1, '#7a1e1e'); }
  return outline(g, OUT);
}
function snake(f, atk, P){
  const g = G(32, 32), ph = f*Math.PI/2;
  for(let x=27; x>=8; x-=1){ const y = 22 + Math.sin(x*0.42 + ph)*2.6, r = 2.2 + (27-x)*0.05; ell(g, x, y, r, r, Math.floor(x/3)%2 ? P.main : P.shade); px(g, x, Math.round(y+r-1), P.light); }
  const hy = (atk ? 15 : 19) + Math.sin(8*0.42+ph)*1.5;
  if(atk) for(let y=Math.round(hy); y<21; y++) ell(g, 8, y, 2.4, 1, P.main);
  ell(g, 6, hy, 4, 3, P.main); ell(g, 6, hy+1, 3, 1.4, P.light);
  px(g, 5, hy-1, P.eye); px(g, 4, hy-1, OUT);
  if(f%2 || atk){ px(g, 1, hy+1, '#d23a3a'); px(g, 0, hy, '#d23a3a'); px(g, 0, hy+2, '#d23a3a'); }
  return outline(g, OUT);
}
function spirit(f, atk, P){
  const g = G(32, 32), sq = atk ? 2 : [0,1,0,-1][f];
  ell(g, 16, 22-sq/2, 9+sq, 7-sq, P.main); ell(g, 16, 24, 8+sq, 3, P.shade); ell(g, 13, 18-sq, 3, 2, P.light); px(g, 12, 17-sq, P.hi);
  rect(g, 11, 20-sq, 3, 3, '#fff'); rect(g, 18, 20-sq, 3, 3, '#fff'); px(g, 12+(atk?-1:0), 21-sq, OUT); px(g, 19+(atk?-1:0), 21-sq, OUT);
  if(atk){ rect(g, 14, 25, 4, 1, OUT); }
  [[9,12],[16,9],[23,12]].forEach(([x,y],i)=>{ if((f+i)%2===0) { px(g, x, y-sq, P.hi); px(g, x, y-1-sq, P.light); } });
  return outline(g, P.dark);
}
function mobSheet(fn, P){
  const c = canvas(32*4, 32*2), x = c.getContext('2d');
  for(let f=0; f<4; f++){ blit(x, fn(f, false, P), f*32, 0); blit(x, fn(f, true, P), f*32, 32); }
  return c;
}

/* ---------- ô nền 16×16 ---------- */
const WORLD = {
  ng:{grass:['#3f7a3a','#4b8a42','#36693a','#5c9c4c'], dirt:['#8a6a44','#7a5c3a','#9c7c52','#6a4e30'], stone:['#7c766a','#6c665c','#8e887c','#5a554c'], water:['#2c5f86','#3a77a4','#6fb0d8','#204a6c'], sand:['#c8b07a','#b89e68','#d8c48e'], cliff:['#6a6458','#575148','#837c6c','#433e36'], forest:['#2f5a2e','#386a36','#264a26'], leaf:['#2f6b38','#3f8a46','#5aa85a','#1f4a28'], flower:['#f0e070','#e88aa0','#fff']},
  lg:{grass:['#3e4a74','#485682','#343f66','#5a6a96'], dirt:['#6e6488','#5e5578','#80769a','#4c4466'], stone:['#6c6a80','#5e5c72','#807e94','#4c4a5e'], water:['#22346a','#2e4486','#6a8ad0','#18264e'], sand:['#9a90b4','#8a80a4','#aaa2c4'], cliff:['#5a5470','#48425c','#706a88','#363048'], forest:['#2e3458','#363e66','#262c4a'], leaf:['#4a4a9a','#5e60b4','#8a8ad8','#32326e'], flower:['#9ff0ff','#e9a0ff','#fff']},
  tg:{grass:['#9a7a3a','#a8883e','#8a6c32','#bc9a4c'], dirt:['#a07a4a','#8e6a3e','#b48c5a','#7a5a32'], stone:['#8a8478','#7a7468','#9e988a','#666054'], water:['#3a5a7a','#4a6e92','#9ac0e0','#2c4660'], sand:['#d8c08a','#c8ae78','#e8d29e'], cliff:['#8a6a4a','#76583c','#a07e58','#5c442e'], forest:['#7a5a2a','#8a6830','#6a4c22'], leaf:['#c46a2a','#d8823a','#f0a24a','#8a4a1e'], flower:['#fff2b0','#ffd27a','#fff']}
};
function tile(name, W, r){
  const g = G(16, 16);
  const noise = (cols, w)=>{ for(let y=0;y<16;y++) for(let x=0;x<16;x++){ const v = r(); px(g, x, y, v < w[0] ? cols[1] : v < w[1] ? cols[2] : cols[0]); } };
  if(name.startsWith('grass') || name==='flower'){
    noise(W.grass, [0.12, 0.2]);
    const n = name==='grass2' ? 7 : 3;
    for(let k=0;k<n;k++){ const x = 1+Math.floor(r()*14), y = 2+Math.floor(r()*12); px(g, x, y, W.grass[3]); px(g, x, y-1, W.grass[3]); px(g, x+1, y+1, W.grass[2]); }
    if(name==='flower') for(let k=0;k<3;k++){ const x = 2+Math.floor(r()*12), y = 2+Math.floor(r()*12), c = W.flower[k%2]; px(g, x-1, y, c); px(g, x+1, y, c); px(g, x, y-1, c); px(g, x, y+1, c); px(g, x, y, W.flower[2]); }
  } else if(name==='dirt'){
    noise(W.dirt, [0.15, 0.27]);
    for(let k=0;k<4;k++){ const x = Math.floor(r()*15), y = Math.floor(r()*15); px(g, x, y, W.dirt[2]); px(g, x+1, y+1, W.dirt[3]); }
  } else if(name==='plaza'){
    rect(g, 0, 0, 16, 16, W.stone[0]);
    for(let row=0; row<4; row++){ const y = row*4, off = row%2 ? 4 : 0; rect(g, 0, y+3, 16, 1, W.stone[3]); for(let x=off; x<16; x+=8) rect(g, x, y, 1, 3, W.stone[3]); for(let x=0;x<16;x++) if(r()<0.5) px(g, x, y, W.stone[2]); for(let k=0;k<3;k++) px(g, Math.floor(r()*16), y+1+Math.floor(r()*2), W.stone[1]); }
  } else if(name==='water0' || name==='water1'){
    noise(W.water, [0.1, 0.18]);
    const o = name==='water1' ? 4 : 0;
    [[2,3],[9,7],[4,12],[12,13]].forEach(([x,y])=>{ x = (x+o)%16; px(g, x, y, W.water[2]); px(g, x+1, y-1, W.water[2]); px(g, x+2, y-1, W.water[2]); px(g, x+3, y, W.water[1]); });
  } else if(name==='sand'){
    noise(W.sand, [0.15, 0.3]);
  } else if(name==='cliff'){
    for(let y=0;y<16;y++) for(let x=0;x<16;x++) px(g, x, y, y<3 ? W.cliff[2] : y>12 ? W.cliff[3] : (r()<0.2 ? W.cliff[1] : W.cliff[0]));
    for(let k=0;k<3;k++){ let x = 2+Math.floor(r()*12), y = 4; while(y<13){ px(g, x, y, W.cliff[3]); y++; x += r()<0.3 ? (r()<0.5?-1:1) : 0; } }
    rect(g, 0, 3, 16, 1, W.cliff[3]);
  } else if(name==='forest'){
    noise(W.forest, [0.18, 0.3]);
  }
  return g;
}
function tileSheet(){
  const c = canvas(16*TILE_COLS.length, 16*3), x = c.getContext('2d');
  ['ng','lg','tg'].forEach((w, wi)=>TILE_COLS.forEach((n, i)=>blit(x, tile(n, WORLD[w], rng(1000+i*17+wi*131)), i*16, wi*16)));
  return c;
}
/* ---------- vật trang trí 32×40 ---------- */
function obj(name, W, r){
  const g = G(32, 40), Lf = W.leaf;
  if(name==='tree'){
    rect(g, 14, 26, 4, 12, '#5a3a22'); rect(g, 14, 26, 1, 12, '#7a5232'); px(g, 13, 37, '#5a3a22'); px(g, 18, 37, '#5a3a22');
    ell(g, 16, 17, 13, 11, Lf[3]); ell(g, 15, 15, 12, 10, Lf[0]); ell(g, 13, 12, 8, 6.5, Lf[1]); ell(g, 11, 10, 4, 3, Lf[2]);
    for(let k=0;k<26;k++){ const a = r()*6.3, d = r()*10; px(g, 16+Math.cos(a)*d*1.1, 16+Math.sin(a)*d*.9, r()<0.5 ? Lf[1] : Lf[3]); }
  } else if(name==='pine'){
    rect(g, 15, 32, 3, 6, '#5a3a22');
    for(let k=0;k<4;k++){ const y = 6 + k*7, w = 5 + k*3; for(let j=0;j<9;j++){ const ww = Math.round(w*j/8); rect(g, 16-ww, y+j, ww*2+1, 1, j>6 ? Lf[3] : Lf[0]); px(g, 16-ww, y+j, Lf[1]); } }
    px(g, 16, 5, Lf[2]);
  } else if(name==='rock'){
    ell(g, 16, 33, 9, 5.5, W.cliff[0]); ell(g, 14, 31, 6, 3.5, W.cliff[2]); rect(g, 8, 36, 16, 1, W.cliff[3]); px(g, 12, 30, W.cliff[2]);
  } else if(name==='bush'){
    ell(g, 16, 33, 10, 5.5, Lf[3]); ell(g, 15, 32, 8.5, 4.5, Lf[0]); ell(g, 12, 30, 4, 2.5, Lf[1]); px(g, 11, 29, Lf[2]);
  } else if(name==='banner'){
    rect(g, 15, 4, 2, 34, '#4a3020'); rect(g, 13, 37, 6, 2, '#3a2418');
    rect(g, 17, 6, 8, 18, '#d8a830'); rect(g, 17, 6, 8, 2, '#a07818'); rect(g, 23, 6, 2, 18, '#b88a20'); px(g, 18, 24, '#d8a830'); px(g, 21, 24, '#d8a830'); px(g, 24, 24, '#b88a20');
    rect(g, 19, 11, 4, 1, '#7a1e1e'); rect(g, 20, 10, 2, 8, '#7a1e1e'); rect(g, 19, 15, 4, 1, '#7a1e1e');
    px(g, 16, 3, '#d8a830');
  } else if(name==='grassTall'){
    for(let k=0;k<9;k++){ const x = 8 + k*2 + Math.floor(r()*2), h = 4 + Math.floor(r()*6); line(g, x, 38, x + (r()<0.5?-1:1), 38-h, k%2 ? W.grass[3] : W.grass[1]); }
  }
  return outline(g, OUT);
}
function objSheet(){
  const c = canvas(32*OBJ_COLS.length, 40*3), x = c.getContext('2d');
  ['ng','lg','tg'].forEach((w, wi)=>OBJ_COLS.forEach((n, i)=>blit(x, obj(n, WORLD[w], rng(500+i*29+wi*7)), i*32, wi*40)));
  return c;
}
/* ---------- công trình ---------- */
function house(roof){
  const g = G(64, 64), R = shades(roof, 55);
  rect(g, 8, 52, 48, 6, '#7c766a'); rect(g, 8, 52, 48, 1, '#9e988a'); rect(g, 8, 57, 48, 1, '#5a554c');
  rect(g, 12, 30, 40, 22, '#e2d6b8'); rect(g, 12, 30, 40, 3, '#b8a888');
  [12, 23, 40, 51].forEach(x=>{ rect(g, x, 30, 2, 22, '#7a3a24'); px(g, x, 30, '#9a5a34'); });
  rect(g, 27, 38, 10, 14, '#4a2a18'); rect(g, 31, 38, 1, 14, '#2a160c'); px(g, 29, 45, '#d8a830'); px(g, 34, 45, '#d8a830');
  rect(g, 16, 36, 5, 5, '#3a2a1a'); rect(g, 43, 36, 5, 5, '#3a2a1a'); rect(g, 18, 36, 1, 5, '#8a6a44'); rect(g, 45, 36, 1, 5, '#8a6a44');
  for(let y=0; y<16; y++){ const w = 18 + y*1.6; const x0 = Math.round(32-w), x1 = Math.round(31+w); for(let x=x0; x<=x1; x++) px(g, x, 14+y, y%3===2 ? R.shade : (x-x0)%4===0 ? R.dark : R.main); }
  rect(g, 0, 29, 64, 2, R.dark); px(g, 0, 27, R.main); px(g, 1, 28, R.main); px(g, 63, 27, R.main); px(g, 62, 28, R.main);
  rect(g, 14, 12, 36, 3, R.light); px(g, 12, 10, R.light); px(g, 13, 11, R.light); px(g, 51, 10, R.light); px(g, 50, 11, R.light);
  rect(g, 29, 8, 6, 4, '#d8a830'); px(g, 31, 6, '#f0d58a'); px(g, 32, 6, '#f0d58a');
  rect(g, 26, 31, 12, 5, '#2a1a10'); rect(g, 27, 32, 10, 3, '#d8a830');
  return outline(g, OUT);
}
function arena(){
  const g = G(96, 72);
  rect(g, 4, 12, 88, 56, '#5a3a22');
  for(let y=14; y<64; y+=5){ rect(g, 8, y, 80, 4, '#a07a4e'); rect(g, 8, y, 80, 1, '#b88e5c'); rect(g, 8, y+4, 80, 1, '#6a4a2c'); for(let x=8+(y*7)%19; x<88; x+=19) { px(g, x, y+2, '#5a3a22'); rect(g, x+9, y, 1, 4, '#7a5636'); } }
  rect(g, 4, 64, 88, 4, '#3a2416');
  [[4,8],[86,8],[4,60],[86,60]].forEach(([x,y])=>{ rect(g, x, y, 6, 10, '#3a2416'); rect(g, x+2, y-10, 2, 12, '#2a160c'); rect(g, x+4, y-10, 8, 6, '#c1402e'); rect(g, x+4, y-10, 8, 1, '#e06a50'); px(g, x+11, y-4, '#c1402e'); });
  for(let x=10; x<86; x+=6){ px(g, x, 12, '#d8a830'); px(g, x, 67, '#d8a830'); }
  return outline(g, OUT);
}
function portal(f){
  const g = G(48, 48);
  ell(g, 24, 28, 22, 14, '#5a554c'); ell(g, 24, 27, 20, 12.5, '#7c766a'); ell(g, 24, 27, 15, 9, '#2a3a36'); ell(g, 24, 27, 12, 7, '#3f8a6a');
  ell(g, 24, 27, 8, 4.6, '#7fd4b0'); ell(g, 24, 27, 4, 2.3, '#d8fff0');
  for(let k=0;k<8;k++){ const a = k*Math.PI/4 + f*Math.PI/16; px(g, 24+Math.cos(a)*17.5, 27+Math.sin(a)*10.8, k%2===f%2 ? '#d8fff0' : '#7fd4b0'); px(g, 25+Math.cos(a)*17.5, 27+Math.sin(a)*10.8, '#57bb96'); }
  for(let k=0;k<5;k++){ const x = 16 + ((k*7 + f*3) % 17), y = 22 - ((f*4 + k*5) % 18); px(g, x, y, '#c9f7de'); }
  return outline(g, OUT);
}
function fx(){
  const c = canvas(32*4, 32 + 16), x = c.getContext('2d');
  for(let f=0; f<4; f++){
    const g = G(32, 32), r0 = 7 + f*3, a0 = -2.2 + f*0.35, a1 = a0 + 2.6;
    for(let a=a0; a<a1; a+=0.02){ const t = (a-a0)/(a1-a0), w = Math.sin(t*Math.PI)*(3.2 - f*0.6); for(let d=0; d<w; d+=0.5){ px(g, 16+Math.cos(a)*(r0+d), 16+Math.sin(a)*(r0+d), d < 1 ? '#ffffff' : f<2 ? '#bff4ff' : '#7ad0f0'); } }
    blit(x, g, f*32, 0);
    const h = G(16, 16), R = 1.5 + f*1.6;
    for(let k=0;k<8;k++){ const a = k*Math.PI/4; line(h, 8+Math.cos(a)*(R*0.4), 8+Math.sin(a)*(R*0.4), 8+Math.cos(a)*R, 8+Math.sin(a)*R, k%2 ? '#ffd27a' : '#ffffff'); }
    if(f<2) ell(h, 8, 8, 2.2-f, 2.2-f, '#fff');
    blit(x, h, f*32 + 8, 32);
  }
  return c;
}
function buildings(){
  const c = canvas(64*3 + 96, 72), x = c.getContext('2d');
  blit(x, house('#c15d4a'), 0, 8); blit(x, house('#3f9a7a'), 64, 8); blit(x, house('#6a6ac8'), 128, 8); blit(x, arena(), 192, 0);
  return c;
}
function portalSheet(){ const c = canvas(48*4, 48), x = c.getContext('2d'); for(let f=0; f<4; f++) blit(x, portal(f), f*48, 0); return c; }

const HERO_PAL = {phap:'#8c6cf0', the:'#c8823e', hon:'#3fa6d8', kiem:'#3fb88a', ma:'#b8323a', phat:'#e0a83a', yeuquy:'#b45ad0'};
function genAll(){
  const out = {};
  for(const k in HERO_PAL) out['hero-'+k] = heroSheet({robe:shades(HERO_PAL[k], 55)});
  out['mob-bandit'] = heroSheet({robe:shades('#3a3440', 12), belt:'#8a2a2a', beltL:'#c04040', mask:'#2a2428', hair:'#1a1418'});
  out['mob-beast'] = mobSheet(beast, {...shades('#7c8a9a', 18), eye:'#ffde6a'});
  out['mob-snake'] = mobSheet(snake, {...shades('#4a9a5a', 45), eye:'#ffde6a'});
  out['mob-spirit'] = mobSheet(spirit, {...shades('#8a7af0', 60), eye:'#fff'});
  out.tiles = tileSheet(); out.objects = objSheet(); out.buildings = buildings(); out.portal = portalSheet(); out.fx = fx();
  return out;
}
root.PixelGen = {genAll, TILE_COLS, OBJ_COLS, DIRS};
})(typeof window!=='undefined' ? window : globalThis);
