const captureBtn      = document.getElementById('capture-btn');
const countdownEl     = document.getElementById('countdown-overlay');
const countdownNum    = document.getElementById('countdown-number');
const qrOverlay       = document.getElementById('qr-overlay');
const qrImg           = document.getElementById('qr-img');
const qrTimer         = document.getElementById('qr-timer');
const qrCloseBtn      = document.getElementById('qr-close-btn');
const loadingMsg      = document.getElementById('loading-msg');
const errorMsg        = document.getElementById('error-msg');
const bgSelectedLabel = document.getElementById('bg-selected-label');

let qrResetInterval  = null;
let selectedBackground = 'none';
let removalMode        = 'greenscreen';

// ── Removal mode toggle ──────────────────────────────────────────────────
document.querySelectorAll('.removal-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.removal-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    removalMode = btn.dataset.mode;
  });
});

// ── Background picker ────────────────────────────────────────────────────
async function loadBackgrounds() {
  try {
    const [bgResp, capResp] = await Promise.all([
      fetch('/backgrounds'),
      fetch('/capabilities'),
    ]);
    const list = await bgResp.json();
    const caps = await capResp.json();
    const grid = document.getElementById('bg-grid');

    if (list.length > 1) {
      document.getElementById('removal-toggle').style.removeProperty('display');
    }

    if (caps.rembg) {
      const aiBtn = document.getElementById('ai-btn');
      document.querySelectorAll('.removal-btn').forEach(b => b.classList.remove('active'));
      aiBtn.classList.add('active');
      removalMode = 'ai';
    } else {
      const aiBtn = document.getElementById('ai-btn');
      aiBtn.disabled = true;
      aiBtn.title = 'rembg not installed — run: uv add rembg[cpu]';
    }

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

  loadingMsg.style.display = 'block';

  try {
    const resp = await fetch('/capture', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ background: selectedBackground, removal: removalMode }),
    });
    const data = await resp.json();
    loadingMsg.style.display = 'none';

    if (!resp.ok) {
      showError(data.error || 'Capture failed — please try again.');
      return;
    }

    showQR(data.qr_url);
  } catch (err) {
    loadingMsg.style.display = 'none';
    showError('Network error — please try again.');
  }
}

function showQR(qrUrl) {
  qrImg.src = qrUrl + '?t=' + Date.now();
  qrOverlay.style.display = 'flex';

  let remaining = 20;
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
  qrTimer.textContent = 'Returning in 20s…';
  captureBtn.disabled = false;
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.style.display = 'block';
  captureBtn.disabled = false;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
