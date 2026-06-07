const captureBtn      = document.getElementById('capture-btn');
const countdownEl     = document.getElementById('countdown-overlay');
const countdownNum    = document.getElementById('countdown-number');
const qrOverlay       = document.getElementById('qr-overlay');
const qrImg           = document.getElementById('qr-img');
const qrProcessing    = document.getElementById('qr-processing');
const qrTimer         = document.getElementById('qr-timer');
const qrCloseBtn      = document.getElementById('qr-close-btn');
const loadingMsg      = document.getElementById('loading-msg');
const errorMsg        = document.getElementById('error-msg');
const bgSelectedLabel = document.getElementById('bg-selected-label');

let qrResetInterval    = null;
let selectedBackground = 'none';

// ── Background picker ────────────────────────────────────────────────────
async function loadBackgrounds() {
  try {
    const resp = await fetch('/backgrounds');
    const list = await resp.json();
    const grid = document.getElementById('bg-grid');

    list.forEach((bg, i) => {
      const btn = document.createElement('button');
      btn.className = 'picker-btn' + (i === 0 ? ' active' : '');
      btn.dataset.bg = bg.id;

      const thumb = bg.preview
        ? `<img src="${bg.preview}" class="bg-thumb" alt="${bg.name}">`
        : `<div class="bg-thumb-none"></div>`;

      btn.innerHTML = `${thumb}<span>${bg.name}</span>`;
      btn.addEventListener('click', () => {
        grid.querySelectorAll('.picker-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        selectedBackground = bg.id;
        bgSelectedLabel.textContent = bg.id === 'none' ? 'None selected' : `Selected: ${bg.name}`;
        bootstrap.Modal.getInstance(document.getElementById('bg-modal'))?.hide();
      });

      grid.appendChild(btn);
    });
  } catch (e) {
    console.warn('Could not load backgrounds', e);
  }
}

loadBackgrounds();

captureBtn.addEventListener('click', startCapture);
qrCloseBtn.addEventListener('click', resetToPreview);

async function startCapture() {
  captureBtn.disabled = true;
  errorMsg.style.display = 'none';

  countdownEl.style.display = 'flex';
  for (let i = 3; i >= 1; i--) {
    countdownNum.textContent = i;
    countdownNum.style.animation = 'none';
    countdownNum.offsetHeight;
    countdownNum.style.animation = '';
    await sleep(1000);
  }
  countdownEl.style.display = 'none';

  showProcessing();

  try {
    const resp = await fetch('/capture', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ background: selectedBackground }),
    });
    const data = await resp.json();

    if (!resp.ok) {
      resetToPreview();
      showError(data.error || 'Capture failed — please try again.');
      return;
    }

    if (data.upload_error) {
      showError(`Upload failed: ${data.upload_error}`);
    }

    showResult(data);
  } catch (err) {
    resetToPreview();
    showError('Network error — please try again.');
  }
}

function showProcessing() {
  const heading = document.getElementById('qr-overlay-heading');
  heading.textContent = 'Scan to get your photo!';
  qrImg.src = '/qr-image?t=' + Date.now();
  qrImg.classList.remove('photo-mode');
  qrProcessing.style.display = 'block';
  qrTimer.style.display = 'none';
  qrCloseBtn.style.display = 'none';
  qrOverlay.style.display = 'flex';
}

function showResult(data) {
  const heading = document.getElementById('qr-overlay-heading');
  if (data.qr_url) {
    heading.textContent = 'Scan to get your photo!';
    qrImg.src = data.qr_url + '?t=' + Date.now();
    qrImg.classList.remove('photo-mode');
  } else if (data.r2_url) {
    heading.textContent = 'Photo saved!';
    qrImg.src = data.r2_url + '?t=' + Date.now();
    qrImg.classList.add('photo-mode');
  }

  qrProcessing.style.display = 'none';
  qrTimer.style.display = 'block';
  qrCloseBtn.style.display = 'inline-block';

  let remaining = 10;
  qrTimer.textContent = `Returning in ${remaining}s…`;

  qrResetInterval = setInterval(() => {
    remaining--;
    qrTimer.textContent = `Returning in ${remaining}s…`;
    if (remaining <= 0) resetToPreview();
  }, 1000);
}

function resetToPreview() {
  if (qrResetInterval) { clearInterval(qrResetInterval); qrResetInterval = null; }
  qrOverlay.style.display = 'none';
  qrImg.src = '';
  qrImg.classList.remove('photo-mode');
  qrProcessing.style.display = 'none';
  qrTimer.style.display = 'block';
  qrTimer.textContent = 'Returning in 10s…';
  qrCloseBtn.style.display = 'inline-block';
  captureBtn.disabled = false;
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.style.display = 'block';
  captureBtn.disabled = false;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
