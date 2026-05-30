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
