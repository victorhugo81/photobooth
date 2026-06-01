const fileInput   = document.getElementById('file-input');
const uploadZone  = document.getElementById('upload-zone');
const bgGrid      = document.getElementById('bg-grid');
const bgCount     = document.getElementById('bg-count');
const emptyMsg    = document.getElementById('empty-msg');
const uploadProg  = document.getElementById('upload-progress');
const progressBar = document.getElementById('progress-bar');
const progressLbl = document.getElementById('progress-label');

async function loadBackgrounds() {
  const resp = await fetch('/backgrounds');
  const list = await resp.json();
  const real = list.filter(b => b.id !== 'none');
  bgGrid.innerHTML = '';
  real.forEach(addCard);
  updateCount(real.length);
}

function updateCount(n) {
  bgCount.textContent = `${n} image${n !== 1 ? 's' : ''}`;
  emptyMsg.style.display = n === 0 ? 'block' : 'none';
}

function addCard(bg) {
  const col = document.createElement('div');
  col.className = 'col';
  col.id = `card-${bg.id}`;
  col.innerHTML = `
    <div class="bg-card">
      <img src="${bg.preview}?t=${Date.now()}" alt="${bg.name}">
      <div class="bg-card-body">
        <span class="bg-card-name" title="${bg.name}">${bg.name}</span>
        <span class="color-dot" id="dot-${bg.id}"></span>
        <button class="btn-del" onclick="deleteBackground('${bg.id}')">✕</button>
      </div>
    </div>`;
  bgGrid.appendChild(col);
  loadDot(bg.id);
}

async function loadDot(bgId) {
  try {
    const r = await fetch(`/backgrounds/${bgId}/color`);
    const d = await r.json();
    if (d.color) {
      const dot = document.getElementById(`dot-${bgId}`);
      if (dot) dot.style.background = d.color;
    }
  } catch (_) {}
}

async function deleteBackground(bgId) {
  if (!confirm(`Delete "${bgId.replace(/_/g, ' ')}"?`)) return;
  const resp = await fetch(`/backgrounds/${bgId}`, { method: 'DELETE' });
  if (resp.ok) {
    document.getElementById(`card-${bgId}`)?.remove();
    updateCount(bgGrid.querySelectorAll('.col').length);
    toast('Deleted', 'success');
  } else {
    toast('Delete failed', 'error');
  }
}

fileInput.addEventListener('change', () => uploadFiles(fileInput.files));

uploadZone.addEventListener('dragover', e => {
  e.preventDefault();
  uploadZone.classList.add('drag-over');
});
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', e => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  uploadFiles(e.dataTransfer.files);
});

async function uploadFiles(files) {
  if (!files.length) return;
  const arr = Array.from(files);
  uploadProg.style.display = 'block';
  progressBar.style.width = '0%';

  for (let i = 0; i < arr.length; i++) {
    const f = arr[i];
    progressLbl.textContent = `${f.name} (${i + 1}/${arr.length})`;
    progressBar.style.width = `${Math.round((i / arr.length) * 100)}%`;

    if (f.size > 20 * 1024 * 1024) { toast(`${f.name} exceeds 20 MB`, 'error'); continue; }

    const fd = new FormData();
    fd.append('file', f);
    try {
      const resp = await fetch('/backgrounds/upload', { method: 'POST', body: fd });
      const data = await resp.json();
      if (resp.ok) {
        document.getElementById(`card-${data.id}`)?.remove();
        addCard(data);
        updateCount(bgGrid.querySelectorAll('.col').length);
        toast(`Uploaded: ${data.name}`, 'success');
      } else {
        toast(`${f.name}: ${data.error}`, 'error');
      }
    } catch (_) { toast(`${f.name}: network error`, 'error'); }
  }

  progressBar.style.width = '100%';
  progressLbl.textContent = 'Done';
  setTimeout(() => { uploadProg.style.display = 'none'; }, 1500);
  fileInput.value = '';
}

function toast(msg, type = 'success') {
  const el = document.createElement('div');
  el.className = `toast-msg ${type}`;
  el.textContent = msg;
  document.getElementById('toast-container').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

loadBackgrounds();
loadEvent();
loadLabel();
loadQrUrl();
loadOnlineAccess();
loadDateFilter();
loadUiTheme();
loadEnv();

async function loadOnlineAccess() {
  try {
    const resp = await fetch('/api/online-access');
    const data = await resp.json();
    setOnlineAccessUI(data.enabled, data.r2_configured);
  } catch (_) {}
}

function setOnlineAccessUI(enabled, r2Configured) {
  document.getElementById('online-yes-btn').classList.toggle('active', enabled);
  document.getElementById('online-no-btn').classList.toggle('active', !enabled);
  const status = document.getElementById('online-access-status');
  if (enabled && !r2Configured) {
    status.textContent = 'R2 not configured';
    status.style.color = '#8b1a1a';
  } else {
    status.textContent = enabled ? 'Cloud upload active' : 'Local storage only';
    status.style.color = '';
  }
}

document.getElementById('online-yes-btn').addEventListener('click', async () => {
  try {
    const resp = await fetch('/api/online-access', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: true }),
    });
    const data = await resp.json();
    if (resp.ok) {
      setOnlineAccessUI(true, data.r2_configured);
      toast(data.r2_configured ? 'Online access enabled' : 'Enabled — R2 not configured in .env', data.r2_configured ? 'success' : 'error');
    } else {
      toast('Failed to save setting', 'error');
    }
  } catch (_) { toast('Network error', 'error'); }
});

document.getElementById('online-no-btn').addEventListener('click', async () => {
  try {
    const resp = await fetch('/api/online-access', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: false }),
    });
    if (resp.ok) {
      setOnlineAccessUI(false, false);
      toast('Local-only mode — no cloud uploads', 'success');
    } else {
      toast('Failed to save setting', 'error');
    }
  } catch (_) { toast('Network error', 'error'); }
});

async function loadQrUrl() {
  try {
    const resp = await fetch('/api/qr-url');
    const data = await resp.json();
    document.getElementById('qr-url-input').value = data.url || '';
  } catch (_) {}
}

document.getElementById('qr-url-save-btn').addEventListener('click', async () => {
  const url = document.getElementById('qr-url-input').value.trim();
  try {
    const resp = await fetch('/api/qr-url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    if (resp.ok) toast('QR URL saved', 'success');
    else toast('Failed to save QR URL', 'error');
  } catch (_) { toast('Network error', 'error'); }
});

async function loadDateFilter() {
  try {
    const resp = await fetch('/api/date-filter');
    const data = await resp.json();
    setDateFilterUI(data.date);
  } catch (_) {}
}

function setDateFilterUI(date) {
  const input  = document.getElementById('date-filter-input');
  const status = document.getElementById('date-filter-status');
  input.value  = date || '';
  status.textContent = date ? `Filtered: ${date}` : 'Showing all dates';
}

document.getElementById('date-filter-save-btn').addEventListener('click', async () => {
  const date = document.getElementById('date-filter-input').value;
  if (!date) { toast('Pick a date first', 'error'); return; }
  try {
    const resp = await fetch('/api/date-filter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date }),
    });
    if (resp.ok) { setDateFilterUI(date); toast(`Filter set: ${date}`, 'success'); }
    else toast('Failed to set date filter', 'error');
  } catch (_) { toast('Network error', 'error'); }
});

document.getElementById('date-filter-clear-btn').addEventListener('click', async () => {
  try {
    const resp = await fetch('/api/date-filter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date: null }),
    });
    if (resp.ok) { setDateFilterUI(null); toast('Date filter cleared', 'success'); }
    else toast('Failed to clear date filter', 'error');
  } catch (_) { toast('Network error', 'error'); }
});

async function loadLabel() {
  try {
    const resp = await fetch('/api/label');
    const data = await resp.json();
    document.getElementById('label-input').value = data.text;
  } catch (_) {}
}

document.getElementById('label-save-btn').addEventListener('click', async () => {
  const text = document.getElementById('label-input').value.trim();
  if (!text) return;
  try {
    const resp = await fetch('/api/label', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (resp.ok) toast('Label saved', 'success');
    else toast('Failed to save label', 'error');
  } catch (_) { toast('Network error', 'error'); }
});

async function loadEvent() {
  try {
    const resp = await fetch('/api/event');
    const data = await resp.json();
    setActiveEvent(data.event);
  } catch (_) {}
}

function setActiveEvent(event) {
  document.querySelectorAll('.event-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.event === event);
  });
}

async function loadUiTheme() {
  try {
    const resp = await fetch('/api/ui-theme');
    const data = await resp.json();
    setActiveUiTheme(data.theme);
  } catch (_) {}
}

function setActiveUiTheme(theme) {
  document.querySelectorAll('.theme-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.theme === theme);
  });
  document.body.className = document.body.className
    .replace(/\btheme-\S+/g, '').trim();
  document.body.classList.add(`theme-${theme}`);
}

document.querySelectorAll('.theme-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const theme = btn.dataset.theme;
    try {
      const resp = await fetch('/api/ui-theme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ theme }),
      });
      if (resp.ok) {
        setActiveUiTheme(theme);
        toast(`Theme: ${btn.querySelector('.event-label').textContent}`, 'success');
      } else {
        toast('Failed to save theme', 'error');
      }
    } catch (_) { toast('Network error', 'error'); }
  });
});

const ENV_KEYS = [
  'R2_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY',
  'R2_BUCKET_NAME', 'R2_PUBLIC_URL', 'SHARE_SITE_URL',
  'PHOTOSLIDE_URL', 'FLASK_ENV', 'FLASK_RUN_HOST', 'FLASK_RUN_PORT',
];

async function loadEnv() {
  try {
    const resp = await fetch('/api/env');
    const data = await resp.json();
    ENV_KEYS.forEach(k => {
      const el = document.getElementById(`env-${k}`);
      if (el) el.value = data[k] || '';
    });
  } catch (_) {}
}

document.getElementById('env-secret-toggle').addEventListener('click', () => {
  const el = document.getElementById('env-R2_SECRET_ACCESS_KEY');
  el.type = el.type === 'password' ? 'text' : 'password';
});

document.getElementById('env-save-btn').addEventListener('click', async () => {
  const payload = {};
  ENV_KEYS.forEach(k => {
    const el = document.getElementById(`env-${k}`);
    if (el) payload[k] = el.value;
  });
  const status = document.getElementById('env-status');
  try {
    const resp = await fetch('/api/env', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (resp.ok) {
      status.textContent = 'Saved';
      toast('Saved to .env — restart the app to apply changes', 'success');
      setTimeout(() => { status.textContent = ''; }, 3000);
    } else {
      const d = await resp.json();
      toast(d.error || 'Failed to save .env', 'error');
    }
  } catch (_) { toast('Network error', 'error'); }
});

document.querySelectorAll('.event-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const event = btn.dataset.event;
    try {
      const resp = await fetch('/api/event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event }),
      });
      if (resp.ok) {
        setActiveEvent(event);
        toast(`Event set: ${btn.querySelector('.event-label').textContent}`, 'success');
      } else {
        toast('Failed to save event', 'error');
      }
    } catch (_) { toast('Network error', 'error'); }
  });
});
