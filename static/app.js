/* jshint esversion: 9 */
'use strict';

let selFiles = new Set(), uploadFiles = [], topK = 5, busy = false;

// ── Init ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const saved = localStorage.getItem('theme') || 'light';
  applyTheme(saved);
  loadDataFiles();
  refreshStatus();
  setupDZ();
  setupSlider();
  setupInput();
});

// ── Theme ─────────────────────────────────────────────────────────
function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme');
  applyTheme(cur === 'dark' ? 'light' : 'dark');
}
function applyTheme(t) {
  document.documentElement.setAttribute('data-theme', t);
  const btn = document.getElementById('themeBtn');
  if (btn) btn.textContent = t === 'dark' ? '☀️' : '🌙';
  localStorage.setItem('theme', t);
}

// ── Data files ────────────────────────────────────────────────────
async function loadDataFiles() {
  const d = await fetch('/api/files').then(r => r.json()).catch(() => ({ files: [] }));
  const el = document.getElementById('dataList');
  if (!d.files || !d.files.length) {
    el.innerHTML = '<p class="file-empty">No files in data/ folder</p>';
    return;
  }
  el.innerHTML = d.files.map((f, i) => {
    const ico = f.endsWith('.pdf') ? '📕' : (f.endsWith('.md') || f.endsWith('.markdown')) ? '📝' : '📄';
    return `<div class="file-item" id="fi${i}" onclick="toggleFile(${i},'${esc(f)}')">
      <input type="checkbox" id="cb${i}" onclick="event.stopPropagation();toggleFile(${i},'${esc(f)}')">
      <span class="file-ico">${ico}</span>
      <span class="file-name" title="${f}">${f}</span>
    </div>`;
  }).join('');
}

function esc(s) { return s.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"'); }

function toggleFile(i, name) {
  const el = document.getElementById('fi' + i);
  const cb = document.getElementById('cb' + i);
  if (selFiles.has(name)) { selFiles.delete(name); el.classList.remove('sel'); cb.checked = false; }
  else { selFiles.add(name); el.classList.add('sel'); cb.checked = true; }
}

// ── Drag & Drop ───────────────────────────────────────────────────
function setupDZ() {
  const dz = document.getElementById('dz');
  const fi = document.getElementById('fileInput');
  if (!dz || !fi) return;
  dz.addEventListener('click', () => fi.click());
  fi.addEventListener('change', e => { uploadFiles = [...e.target.files]; updateDZ(); });
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('over'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('over'));
  dz.addEventListener('drop', e => {
    e.preventDefault(); dz.classList.remove('over');
    uploadFiles = [...e.dataTransfer.files]; updateDZ();
  });
}
function updateDZ() {
  const dz = document.getElementById('dz');
  dz.innerHTML = `
    <span class="dz-ico">✅</span>
    <p><strong>${uploadFiles.length} file${uploadFiles.length > 1 ? 's' : ''} ready</strong></p>
    <p style="font-size:10.5px;margin-top:2px">${uploadFiles.map(f => f.name).slice(0, 3).join(', ')}${uploadFiles.length > 3 ? '…' : ''}</p>`;
}

// ── Ingest ────────────────────────────────────────────────────────
async function ingestSelected() {
  const srcs = [...selFiles].map(n => ({ type: 'df', name: n }))
    .concat(uploadFiles.map(f => ({ type: 'f', file: f })));
  if (!srcs.length) { toast('Select or upload files first', 'err'); return; }

  const btn = document.getElementById('ingestBtn');
  const pg = document.getElementById('prog');
  btn.disabled = true; pg.innerHTML = ''; pg.style.display = 'block';

  let total = 0;
  for (const s of srcs) {
    const name = s.type === 'f' ? s.file.name : s.name;
    const id = 'pi_' + Math.random().toString(36).slice(2);
    pg.insertAdjacentHTML('beforeend',
      `<div class="pi spin" id="${id}">
        <span class="pi-ico">⏳</span>
        <span class="pi-name">${name}</span>
        <span class="pi-st">Processing…</span>
      </div>`);
    try {
      let res;
      if (s.type === 'df') {
        res = await fetch('/api/ingest/datafile', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filename: s.name })
        });
      } else {
        const fd = new FormData(); fd.append('file', s.file);
        res = await fetch('/api/ingest/file', { method: 'POST', body: fd });
      }
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed');
      total += data.chunks;
      const pi = document.getElementById(id);
      pi.className = 'pi';
      pi.querySelector('.pi-ico').textContent = '✅';
      pi.querySelector('.pi-st').textContent = data.chunks + ' chunks';
    } catch (e) {
      const pi = document.getElementById(id);
      pi.className = 'pi';
      pi.querySelector('.pi-ico').textContent = '❌';
      pi.querySelector('.pi-st').textContent = e.message;
    }
  }
  btn.disabled = false;
  toast('✅ ' + total + ' chunks indexed', 'ok');
  refreshStatus();
}

async function ingestURL() {
  const url = document.getElementById('urlIn').value.trim();
  if (!url) { toast('Enter a URL first', 'err'); return; }
  toast('Fetching URL…', 'inf');
  try {
    const res = await fetch('/api/ingest/url', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const d = await res.json();
    if (!res.ok) throw new Error(d.detail);
    toast('✅ ' + d.chunks + ' chunks indexed from URL', 'ok');
    document.getElementById('urlIn').value = '';
    refreshStatus();
  } catch (e) { toast('Error: ' + e.message, 'err'); }
}

async function clearAll() {
  if (!confirm('Clear all indexed documents and chat history?')) return;
  await fetch('/api/clear', { method: 'POST' });
  document.getElementById('msgs').innerHTML = '';
  addEmptyState();
  refreshStatus();
  toast('All data cleared', 'inf');
}

async function refreshStatus() {
  const d = await fetch('/api/status').then(r => r.json()).catch(() => ({ chunk_count: 0 }));
  const count = d.chunk_count || 0;
  const el = document.getElementById('chunkCount');
  const pill = document.getElementById('hdrChunks');
  if (el) el.textContent = count;
  if (pill) pill.textContent = count + ' chunks';
}

// ── Slider ────────────────────────────────────────────────────────
function setupSlider() {
  const sl = document.getElementById('tkSlider');
  if (!sl) return;
  sl.addEventListener('input', () => {
    topK = +sl.value;
    document.getElementById('tkVal').textContent = topK;
  });
}

// ── Input ─────────────────────────────────────────────────────────
function setupInput() {
  const ta = document.getElementById('msgIn');
  if (!ta) return;
  ta.addEventListener('input', () => {
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
    updateSend();
  });
  ta.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  });
}
function updateSend() {
  const has = document.getElementById('msgIn').value.trim().length > 0;
  document.getElementById('sendBtn').disabled = !has || busy;
}

// ── Chat ──────────────────────────────────────────────────────────
async function send() {
  const ta = document.getElementById('msgIn');
  const txt = ta.value.trim();
  if (!txt || busy) return;
  ta.value = ''; ta.style.height = 'auto'; busy = true; updateSend();

  const es = document.getElementById('emptyState');
  if (es) es.remove();

  addMsg('user', txt);
  setTyping(true);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: txt, top_k: topK })
    });
    const d = await res.json();
    if (!res.ok) throw new Error(d.detail || 'Server error');
    setTyping(false); busy = false; updateSend();
    addMsg('assistant', d.answer, d.sources || [], d.chunks || []);
  } catch (e) {
    setTyping(false); busy = false; updateSend();
    addMsg('assistant', '⚠️ ' + e.message);
  }
}

function chipSend(t) {
  document.getElementById('msgIn').value = t;
  updateSend();
  send();
}

function addMsg(role, content, sources = [], chunks = []) {
  const msgs = document.getElementById('msgs');
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const id = 'msg' + Date.now();
  const isUser = role === 'user';

  const srcHtml = (!isUser && sources.length) ? `
    <button class="src-toggle" onclick="toggleSrc('${id}')">
      📚 ${sources.length} source${sources.length > 1 ? 's' : ''} · ${chunks.length} chunk${chunks.length !== 1 ? 's' : ''}
    </button>
    <div class="src-panel" id="sp${id}">
      <p class="sp-lbl">Citations</p>
      ${sources.map(s => `
        <div class="src-item">
          <div class="src-num">${s.index}</div>
          <div class="src-info">
            <div class="src-name">${s.source}</div>
            <div class="src-sub">${s.page ? 'Page ' + s.page : ''}${s.score ? (s.page ? ' · ' : '') + (s.score * 100).toFixed(0) + '% match' : ''}</div>
          </div>
        </div>`).join('')}
      ${chunks.length ? `
        <p class="sp-lbl" style="margin-top:12px">Retrieved Chunks</p>
        ${chunks.map((c, i) => `
          <div class="chunk-card">
            <div class="ck-hdr">
              <span class="ck-num">#${i + 1}</span>
              <span class="ck-src">${c.source}${c.page ? ' · p.' + c.page : ''}</span>
              <span class="ck-score">${c.score ? (c.score * 100).toFixed(0) + '%' : ''}</span>
            </div>
            <div class="ck-txt">${c.text}</div>
          </div>`).join('')}` : ''}
    </div>` : '';

  const html = `
<div class="mrow ${isUser ? 'user' : 'bot'}" id="${id}">
  ${!isUser ? '<div class="m-av bot-av">✨</div>' : ''}
  <div class="m-col">
    <div class="bbl ${isUser ? 'user-bbl' : 'bot-bbl'}">${fmt(content)}</div>
    ${srcHtml}
    <div class="m-meta">
      <span>${now}</span>
      ${isUser ? '<span class="ticks">✓✓</span>' : ''}
    </div>
  </div>
  ${isUser ? '<div class="m-av user-av">👤</div>' : ''}
</div>`;

  msgs.insertAdjacentHTML('beforeend', html);
  scrollBottom();
}

function addEmptyState() {
  document.getElementById('msgs').innerHTML = `
    <div class="empty" id="emptyState">
      <div class="empty-icon">✨</div>
      <h2>Ask Me Anything</h2>
      <p>Upload your documents on the left, then ask questions. I answer with citations and remember our conversation.</p>
      <div class="chips">
        <button class="chip" onclick="chipSend('What topics are covered in the documents?')">📋 What topics are covered?</button>
        <button class="chip" onclick="chipSend('Give me a summary of the key points')">📝 Summarise key points</button>
        <button class="chip" onclick="chipSend('Explain the main concepts')">💡 Explain concepts</button>
        <button class="chip" onclick="chipSend('What are the key takeaways?')">🔍 Key takeaways</button>
      </div>
    </div>`;
}

function toggleSrc(id) { document.getElementById('sp' + id).classList.toggle('open'); }

function setTyping(v) {
  document.getElementById('typingWrap').style.display = v ? 'block' : 'none';
  if (v) scrollBottom();
}

function scrollBottom() {
  const m = document.getElementById('msgs');
  setTimeout(() => { m.scrollTop = m.scrollHeight; }, 40);
}

// ── Markdown formatter ────────────────────────────────────────────
function fmt(t) {
  return t
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\[(\d+)\]/g, '<span class="cite">$1</span>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h3>$1</h3>')
    .replace(/^- (.+)$/gm, '• $1')
    .replace(/\n/g, '<br>');
}

// ── Toast ─────────────────────────────────────────────────────────
function toast(msg, type = 'inf') {
  const c = document.getElementById('toasts');
  const el = document.createElement('div');
  const icons = { ok: '✅', err: '❌', inf: 'ℹ️' };
  el.className = 'toast ' + type;
  el.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
  c.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}
