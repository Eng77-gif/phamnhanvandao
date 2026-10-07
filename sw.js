/* Service worker tối giản cho Phàm Nhân Vấn Đạo — cho phép cài thành ứng dụng.
   Game cần mạng để lưu lên máy chủ, nên chỉ lưu tạm trang chính để mở nhanh hơn. */
const CACHE = 'van-dao-v2';
self.addEventListener('install', e => { self.skipWaiting(); });
self.addEventListener('activate', e => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', e => {
  const req = e.request;
  const u = new URL(req.url);
  if (req.method !== 'GET' || u.origin !== location.origin) return;
  if (/\.apk$/i.test(u.pathname)) return;   // tệp cài Android: tải thẳng, không lưu tạm
  e.respondWith(fetch(req).then(res => {
    const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)).catch(()=>{});
    return res;
  }).catch(() => caches.match(req)));
});
