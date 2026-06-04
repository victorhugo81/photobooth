const POLL_MS  = 3000;   // how often to check for a new capture (slot 0)
const SLIDE_MS = 15000;  // how often slots 1–5 cycle
const FADE_MS  = 1200;   // fade duration — must match CSS transition

// When the page is opened via a QR link (e.g. /live-show?date=2026-06-04)
// restrict the gallery to photos from that date only.
const URL_DATE = new URLSearchParams(window.location.search).get('date');

let allPhotos  = [];
let cycleIndex = 0;   // start index for cycling slots 1–5
let latestKey  = '';  // filename of photo in slot 0

function makeCard(photo) {
  const col = document.createElement('div');
  col.className = 'col';
  col.innerHTML = `<a class="photo-card" href="${SHARE_SITE_URL}/?f=${encodeURIComponent(photo.filename)}" target="_blank" rel="noopener">
    <img src="${photo.r2_url}" alt="${photo.filename}">
  </a>`;
  return col;
}

// Fade a slot out, swap its content, fade back in
function setSlot(slotEl, photo, animate = false) {
  if (!animate) {
    slotEl.innerHTML = photo ? makeCard(photo).innerHTML : '';
    return;
  }
  slotEl.classList.add('col-fade-out');
  setTimeout(() => {
    slotEl.innerHTML = photo ? makeCard(photo).innerHTML : '';
    slotEl.classList.remove('col-fade-out');
  }, FADE_MS);
}

async function fetchPhotos() {
  const url = URL_DATE ? `/api/photos?date=${encodeURIComponent(URL_DATE)}` : '/api/photos';
  const resp = await fetch(url);
  if (!resp.ok) throw new Error('fetch failed');
  return resp.json();
}

async function init() {
  const slots      = Array.from({ length: 6 }, (_, i) => document.getElementById(`slot-${i}`));
  const photoCount = document.getElementById('photo-count');

  function updateCount() {
    const n = allPhotos.length;
    if (photoCount) photoCount.textContent = `${n} photo${n !== 1 ? 's' : ''}`;
  }

  // Slot 0: always the most recent photo; only redraws on a new capture
  function refreshLatest(animate = false) {
    const latest = allPhotos[0] ?? null;
    const key    = latest?.filename ?? '';
    if (key === latestKey) return;
    latestKey = key;
    setSlot(slots[0], latest, animate);
    updateCount();
  }

  // Slots 1–5: cycle through all photos
  function refreshCycle(animate = false) {
    if (!allPhotos.length) return;
    for (let i = 0; i < 5; i++) {
      const photo = allPhotos[(cycleIndex + i) % allPhotos.length];
      setSlot(slots[i + 1], photo, animate);
    }
  }

  // Initial fill — no animation on first render
  try { allPhotos = await fetchPhotos(); } catch (_) {}
  refreshLatest();
  cycleIndex = Math.min(1, allPhotos.length - 1);
  refreshCycle();

  // Poll for new captures (slot 0 only)
  async function pollLatest() {
    try {
      allPhotos = await fetchPhotos();
      refreshLatest(true);
    } catch (_) {}
    setTimeout(pollLatest, POLL_MS);
  }
  setTimeout(pollLatest, POLL_MS);

  // Advance slideshow every 15 s (slots 1–5)
  setInterval(() => {
    if (!allPhotos.length) return;
    cycleIndex = (cycleIndex + 5) % allPhotos.length;
    refreshCycle(true);
  }, SLIDE_MS);
}

document.addEventListener('DOMContentLoaded', init);
