const POLL_MS   = 3000;   // how often to check for new photos (row 1)
const SLIDE_MS  = 15000;  // how often the slideshow advances (row 2)
const FADE_MS   = 500;    // fade transition duration
const ROW_COLS  = 3;      // photos per row

let allPhotos      = [];
let slideshowIndex = 0;  // start index for row 2
let latestKey      = ''; // fingerprint of row 1 to avoid unnecessary redraws

function makeCard(photo) {
  const col = document.createElement('div');
  col.className = 'col';
  col.innerHTML = `<a class="photo-card" href="${SHARE_SITE_URL}/?f=${encodeURIComponent(photo.filename)}" target="_blank" rel="noopener">
    <img src="${photo.r2_url}" alt="${photo.filename}">
  </a>`;
  return col;
}

function renderRow(el, photos, animate = false) {
  if (!animate) {
    el.innerHTML = '';
    photos.forEach(p => el.appendChild(makeCard(p)));
    return;
  }
  el.classList.add('row-fade-out');
  setTimeout(() => {
    el.innerHTML = '';
    photos.forEach(p => el.appendChild(makeCard(p)));
    el.classList.remove('row-fade-out');
    el.classList.add('row-fade-in');
    setTimeout(() => el.classList.remove('row-fade-in'), FADE_MS);
  }, FADE_MS);
}

function getSlice(offset, count) {
  if (!allPhotos.length) return [];
  const out = [];
  for (let i = 0; i < count; i++) {
    out.push(allPhotos[(offset + i) % allPhotos.length]);
  }
  return out;
}

async function fetchPhotos() {
  const resp = await fetch('/api/photos');
  if (!resp.ok) throw new Error('fetch failed');
  return resp.json();
}

async function init() {
  const rowLatest    = document.getElementById('row-latest');
  const rowSlideshow = document.getElementById('row-slideshow');
  const photoCount   = document.getElementById('photo-count');

  function refreshLatest() {
    const latest = allPhotos.slice(0, ROW_COLS);
    const key    = latest.map(p => p.filename).join(',');
    if (key === latestKey) return;
    latestKey = key;
    renderRow(rowLatest, latest, true);
    const n = allPhotos.length;
    photoCount.textContent = `${n} photo${n !== 1 ? 's' : ''}`;
  }

  function refreshSlideshow(animate = false) {
    renderRow(rowSlideshow, getSlice(slideshowIndex, ROW_COLS), animate);
  }

  // Initial load
  try { allPhotos = await fetchPhotos(); } catch (_) {}
  refreshLatest();
  refreshSlideshow();

  // Row 1: poll for new captures
  async function pollLatest() {
    try {
      allPhotos = await fetchPhotos();
      refreshLatest();
    } catch (_) {}
    setTimeout(pollLatest, POLL_MS);
  }
  setTimeout(pollLatest, POLL_MS);

  // Row 2: advance slideshow
  setInterval(() => {
    if (!allPhotos.length) return;
    slideshowIndex = (slideshowIndex + ROW_COLS) % allPhotos.length;
    refreshSlideshow(true);
  }, SLIDE_MS);
}

document.addEventListener('DOMContentLoaded', init);
