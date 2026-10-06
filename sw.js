/* Service worker tối giản cho Phàm Nhân Vấn Đạo — cho phép cài thành ứng dụng.
   Game cần mạng để lưu lên máy chủ, nên chỉ lưu tạm trang chính để mở nhanh hơn. */
const CACHE = 'van-dao-v1';
self.addEventListener('install', e => { self.skipWaiting(); });
self.addEventListener('activate', e => { e.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  e.respondWith(fetch(req).then(res => {
    const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)).catch(()=>{});
    return res;
  }).catch(() => caches.match(req)));
});
