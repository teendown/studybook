'use strict';
const $ = id => document.getElementById(id);
const WIDTH = 1000;
let questions = [], byId = new Map(), deck = [], index = 0, review = new Set();
let db, dbFailed = false, pendingWrite = Promise.resolve(), sessionTimer, toastTimer;
let strokes = [], redoStack = [], active = null, pointer = null, tool = 'pen', color = '#233b50';
let height = 1400, frame = 0, busy = false, imageReady = false;
const memory = new Map();
const canvas = $('ink'), ctx = canvas.getContext('2d');

function toast(message) {
  $('toast').textContent = message; $('toast').hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').hidden = true, 3500);
}
function navToDashboard(e) {
  if (e) e.preventDefault();
  if (window.location.protocol === 'file:' || !window.location.host) {
    if (confirm('독립형 오프라인 파일로 실행 중입니다. 온라인 웹 대시보드(studybook)를 여시겠습니까?')) {
      window.open('https://teendown.github.io/studybook/', '_blank');
    }
    return;
  }
  const path = window.location.pathname;
  const match = path.match(/^(.*\/)(?:science|social)(?:\/.*)?$/i);
  if (match && match[1]) {
    window.location.href = match[1];
    return;
  }
  const matchNoSlash = path.match(/^(.*)\/(?:science|social)$/i);
  if (matchNoSlash && matchNoSlash[1]) {
    window.location.href = matchNoSlash[1] + '/';
    return;
  }
  window.location.href = '../';
}
function warn(message) { $('warning').textContent = message; $('warning').hidden = false; }
function storageFailure() {
  dbFailed = true;
  $('save-status').textContent = '로컬 보관 중';
}
function openDB() {
  return new Promise((resolve, reject) => {
    if (!window.indexedDB) { reject(new Error('IndexedDB unsupported')); return; }
    const request = indexedDB.open('society-pencil-v1', 1);
    request.onupgradeneeded = () => request.result.createObjectStore('records');
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    request.onblocked = () => reject(new Error('Storage blocked'));
  });
}
async function read(key) {
  if (memory.has(key)) return memory.get(key);
  if (!db) {
    try {
      const val = localStorage.getItem('society-pencil:' + key);
      if (val) return JSON.parse(val);
    } catch {}
    return undefined;
  }
  return new Promise((resolve, reject) => {
    const request = db.transaction('records').objectStore('records').get(key);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
function write(key, value) {
  const snapshot = structuredClone(value);
  memory.set(key, snapshot);
  $('save-status').textContent = '저장 중…';
  if (!db) {
    try {
      localStorage.setItem('society-pencil:' + key, JSON.stringify(snapshot));
      $('save-status').textContent = '이 기기에 저장됨';
    } catch {
      $('save-status').textContent = '메모리에 보관 중';
    }
    return Promise.resolve();
  }
  pendingWrite = pendingWrite.then(() => new Promise((resolve, reject) => {
    const tx = db.transaction('records', 'readwrite');
    tx.objectStore('records').put(snapshot, key);
    tx.oncomplete = resolve; tx.onerror = () => reject(tx.error); tx.onabort = () => reject(tx.error);
  })).then(() => { if (!dbFailed) $('save-status').textContent = '이 기기에 저장됨'; }).catch(storageFailure);
  return pendingWrite;
}
async function allRecords() {
  await pendingWrite;
  const result = {};
  if (db) await new Promise((resolve, reject) => {
    const request = db.transaction('records').objectStore('records').openCursor();
    request.onsuccess = () => { const cursor = request.result; if (!cursor) return resolve(); result[cursor.key] = cursor.value; cursor.continue(); };
    request.onerror = () => reject(request.error);
  }).catch(() => {});
  try {
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (k && k.startsWith('society-pencil:')) {
        const pureKey = k.slice('society-pencil:'.length);
        if (!result[pureKey]) result[pureKey] = JSON.parse(localStorage.getItem(k));
      }
    }
  } catch {}
  for (const [key, value] of memory) result[key] = value;
  return result;
}
function question() { return byId.get(deck[index]); }
function noteKey() { return `note:${question().id}`; }
function saveInk() { updateUndo(); if (question()) write(noteKey(), {strokes}); }
function saveSession() {
  clearTimeout(sessionTimer);
  if (!questions.length) return;
  const session = {deck, index, review:[...review], start:$('start').value, end:$('end').value,
    reviewOnly:$('review-only').checked, pencilOnly:$('pencil-only').checked};
  // Small synchronous checkpoint survives a reload before an IndexedDB write settles.
  try { localStorage.setItem('society-pencil-session', JSON.stringify(session)); } catch { /* IndexedDB remains the primary store. */ }
  return write('session', session);
}
function shuffle(items) {
  const result = [...items];
  for (let i = result.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [result[i], result[j]] = [result[j], result[i]]; }
  return result;
}
function updateBookmark() {
  const marked = review.has(question()?.id);
  $('bookmark').textContent = marked ? '★ 다시 풀기' : '☆ 다시 풀기';
  $('bookmark').setAttribute('aria-pressed', String(marked));
  $('review-count').textContent = review.size;
}
function updateUndo() { $('undo').disabled = !strokes.length; $('redo').disabled = !redoStack.length; $('clear').disabled = !strokes.length; }
function setTool(next) {
  finishStroke(); tool = next; canvas.classList.toggle('moving', next === 'move');
  document.querySelectorAll('[data-tool]').forEach(button => { const selected = button.dataset.tool === next; button.classList.toggle('selected', selected); button.setAttribute('aria-pressed', String(selected)); });
  $('mode-hint').textContent = next === 'move' ? '손가락으로 스크롤·확대하세요. 쓰려면 펜을 선택하세요.' : $('pencil-only').checked ? '필기 중 손 터치는 무시해요. 스크롤은 ‘이동’ 도구로.' : '손가락·펜슬 모두 쓸 수 있어요. 스크롤은 ‘이동’ 도구로.';
}
function resizeCanvas() {
  const size = $('paper').getBoundingClientRect();
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.max(1, Math.round(size.width * ratio));
  canvas.height = Math.max(1, Math.round(size.height * ratio));
  redraw();
}
function renderStroke(target, stroke) {
  const points = stroke.points;
  if (!points.length) return;
  target.save();
  target.globalCompositeOperation = stroke.tool === 'eraser' ? 'destination-out' : 'source-over';
  target.strokeStyle = stroke.color; target.fillStyle = stroke.color;
  target.lineCap = 'round'; target.lineJoin = 'round';
  if (stroke.tool === 'marker' || stroke.tool === 'eraser') {
    target.globalAlpha = stroke.tool === 'marker' ? .25 : 1;
    target.lineWidth = stroke.size;
    target.beginPath(); target.moveTo(points[0].x, points[0].y);
    for (const p of points.slice(1)) target.lineTo(p.x, p.y);
    if (points.length === 1) target.lineTo(points[0].x + .01, points[0].y);
    target.stroke();
  } else {
    for (let i = 0; i < points.length; i++) {
      const p = points[i], previous = points[Math.max(0, i - 1)];
      target.lineWidth = stroke.size * (.4 + .9 * p.p);
      target.beginPath(); target.moveTo(previous.x, previous.y); target.lineTo(p.x + (i === 0 ? .01 : 0), p.y); target.stroke();
    }
  }
  target.restore();
}
function redraw() {
  frame = 0;
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.setTransform(canvas.width / WIDTH, 0, 0, canvas.height / height, 0, 0);
  for (const stroke of strokes) renderStroke(ctx, stroke);
  if (active) renderStroke(ctx, active);
}
function scheduleDraw() { if (!frame) frame = requestAnimationFrame(redraw); }
function point(event) {
  const rect = canvas.getBoundingClientRect();
  return {x:Math.max(0, Math.min(WIDTH, (event.clientX - rect.left) / rect.width * WIDTH)),
    y:Math.max(0, Math.min(height, (event.clientY - rect.top) / rect.height * height)),
    p:event.pointerType === 'pen' && event.pressure > 0 ? event.pressure : .5};
}
canvas.addEventListener('pointerdown', event => {
  if (busy || !imageReady || tool === 'move' || active || (event.pointerType === 'touch' && $('pencil-only').checked) || (event.pointerType === 'mouse' && event.button !== 0)) return;
  event.preventDefault(); pointer = event.pointerId;
  try { canvas.setPointerCapture(pointer); } catch { /* Synthetic input has no capture. */ }
  const size = +$('pen-size').value;
  active = {tool, color, size:tool === 'eraser' ? size * 9 : tool === 'marker' ? size * 7 : size * 1.4, points:[point(event)]};
  scheduleDraw();
});
canvas.addEventListener('pointermove', event => {
  if (!active || event.pointerId !== pointer) return;
  event.preventDefault();
  const events = event.getCoalescedEvents?.() || [];
  for (const sample of events.length ? events : [event]) active.points.push(point(sample));
  scheduleDraw();
});
function finishStroke(event) {
  if (!active || (event && event.pointerId !== pointer)) return;
  if (event?.type === 'pointerup') active.points.push(point(event));
  const oldPointer = pointer; strokes.push(active); active = null; pointer = null; redoStack = [];
  if (canvas.hasPointerCapture(oldPointer)) canvas.releasePointerCapture(oldPointer);
  saveInk(); scheduleDraw();
}
canvas.addEventListener('pointerup', finishStroke);
canvas.addEventListener('pointercancel', finishStroke);
canvas.addEventListener('lostpointercapture', finishStroke);
canvas.addEventListener('contextmenu', event => event.preventDefault());

async function showQuestion(scroll = true) {
  const q = question(); if (!q) return;
  imageReady = false; active = null; pointer = null; redoStack = [];
  const note = await read(`note:${q.id}`).catch(() => { storageFailure(); return null; });
  strokes = note?.strokes || [];
  height = Math.max(1100, q.height / q.width * WIDTH + 520);
  $('paper').style.aspectRatio = `${WIDTH} / ${height}`;
  $('question-page').textContent = `책 ${q.page}쪽 · ${q.id}`;
  $('question-title').textContent = `문제 ${String(q.number).padStart(3, '0')}`;
  $('question-image').alt = `책 ${q.page}쪽, 문제 ${q.id}`;
  $('question-image').style.aspectRatio = `${q.width} / ${q.height}`;
  const image = $('question-image');
  image.onload = () => { imageReady = true; };
  image.onerror = () => { imageReady = false; toast('문제 이미지를 불러오지 못했습니다. 인터넷 연결 후 다시 열어 주세요.'); };
  image.src = q.image;
  if (image.complete && image.naturalWidth) imageReady = true;
  $('position').textContent = `${index + 1} / ${deck.length}`;
  $('progress-text').textContent = `${index + 1} / ${deck.length}`;
  $('progress').max = deck.length; $('progress').value = index + 1;
  $('previous').disabled = index === 0;
  $('next').textContent = index === deck.length - 1 ? '한 바퀴 완료 ↻' : '다음 문제 →';
  updateBookmark(); updateUndo(); resizeCanvas(); saveSession();
  if (scroll) { $('paper-scroll').scrollTop = 0; document.querySelector('.question-heading').scrollIntoView({block:'start'}); }
}
async function guarded(action) {
  if (busy || !questions.length) return;
  busy = true;
  try { finishStroke(); await pendingWrite; await action(); }
  catch (error) { console.error(error); toast('처리하지 못했습니다. 다시 시도해 주세요.'); }
  finally { busy = false; }
}
async function newDeck(scroll = true) {
  const start = Number($('start').value), end = Number($('end').value);
  if (!Number.isInteger(start) || !Number.isInteger(end) || start < 1 || end > 176 || start > end) { toast('시작·끝 쪽수를 1~176 사이로 입력해 주세요.'); return; }
  const eligible = questions.filter(q => q.page >= start && q.page <= end && (!$('review-only').checked || review.has(q.id)));
  if (!eligible.length) { toast('이 범위에 문제가 없어요. 범위를 넓히거나 별표 필터를 꺼 주세요.'); return; }
  deck = shuffle(eligible.map(q => q.id)); index = 0; await showQuestion(scroll);
}
$('filters').addEventListener('submit', event => { event.preventDefault(); guarded(() => newDeck()); });
$('next').onclick = () => guarded(async () => {
  if (index + 1 < deck.length) { index++; await showQuestion(); }
  else if (confirm('선택한 문제를 모두 보았어요. 다시 섞어서 시작할까요?')) await newDeck();
});
$('previous').onclick = () => guarded(async () => { if (index > 0) { index--; await showQuestion(); } });
$('bookmark').onclick = () => {
  if (!question() || busy) return;
  const id = question().id; if (review.has(id)) review.delete(id); else review.add(id);
  updateBookmark(); saveSession();
};
document.querySelectorAll('[data-tool]').forEach(button => button.onclick = () => setTool(button.dataset.tool));
document.querySelectorAll('[data-color]').forEach(button => button.onclick = () => {
  color = button.dataset.color;
  document.querySelectorAll('[data-color]').forEach(b => { b.classList.toggle('selected', b === button); b.setAttribute('aria-pressed', String(b === button)); });
});
$('pencil-only').onchange = () => { setTool(tool); saveSession(); };
$('undo').onclick = () => { if (busy) return; finishStroke(); if (strokes.length) { redoStack.push(strokes.pop()); saveInk(); scheduleDraw(); } };
$('redo').onclick = () => { if (busy) return; finishStroke(); if (redoStack.length) { strokes.push(redoStack.pop()); saveInk(); scheduleDraw(); } };
$('clear').onclick = () => { if (!busy && strokes.length && confirm('현재 문제의 필기를 모두 지울까요? 백업한 파일은 유지됩니다.')) { finishStroke(); strokes = []; redoStack = []; saveInk(); scheduleDraw(); } };
document.querySelectorAll('[data-close]').forEach(button => button.onclick = () => $(button.dataset.close).close());
$('help').onclick = () => $('help-dialog').showModal();
$('source').onclick = () => { if (!question()) return; $('source-title').textContent = `책 ${question().page}쪽 · 원본`; $('source-image').src = question().source; $('source-dialog').showModal(); };
function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob), a = document.createElement('a');
  a.href = url; a.download = filename; document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}
$('export').onclick = () => guarded(async () => {
  saveSession(); const records = await allRecords();
  downloadBlob(new Blob([JSON.stringify({format:'science-pencil', version:1, created:new Date().toISOString(), records})], {type:'application/json'}), `과학필기-${new Date().toISOString().slice(0,10)}.json`);
  toast('백업 파일을 저장하세요. Safari의 다운로드에서 확인할 수 있어요.');
});
function validStroke(s) {
  return s && ['pen','marker','eraser'].includes(s.tool) && /^#[0-9a-f]{6}$/i.test(s.color) && Number.isFinite(s.size) && s.size > 0 && s.size <= 100 && Array.isArray(s.points) && s.points.length <= 100000 && s.points.every(p => p && Number.isFinite(p.x) && p.x >= 0 && p.x <= WIDTH && Number.isFinite(p.y) && p.y >= 0 && p.y <= 10000 && Number.isFinite(p.p) && p.p >= 0 && p.p <= 1);
}
function validateBackup(data) {
  if (data?.format !== 'science-pencil' || data.version !== 1 || !data.records || typeof data.records !== 'object' || Array.isArray(data.records)) throw new Error('올바른 펜슬 문제집 백업 파일이 아닙니다.');
  for (const [key, value] of Object.entries(data.records)) {
    if (key === 'session') { if (!Array.isArray(value?.review) || !value.review.every(id => byId.has(id))) throw new Error('복습 목록 형식이 올바르지 않습니다.'); }
    else if (!key.startsWith('note:') || !byId.has(key.slice(5)) || !Array.isArray(value?.strokes) || value.strokes.length > 20000 || !value.strokes.every(validStroke)) throw new Error('필기 데이터 형식이 올바르지 않습니다.');
  }
  return data.records;
}
$('import').onclick = () => $('backup-file').click();
$('backup-file').onchange = event => guarded(async () => {
  const file = event.target.files[0]; event.target.value = ''; if (!file) return;
  try {
    if (file.size > 80 * 1024 * 1024) throw new Error('백업 파일이 너무 큽니다. 80MB 이하 파일을 선택해 주세요.');
    const records = validateBackup(JSON.parse(await file.text()));
    if (!confirm('백업에 들어 있는 문제의 필기를 불러올까요? 해당 문제의 현재 필기는 백업 내용으로 바뀝니다. 다른 문제의 필기는 유지됩니다.')) return;
    const notes = Object.entries(records).filter(([key]) => key.startsWith('note:'));
    if (!db || dbFailed) throw new Error('저장 공간을 사용할 수 없어 복원할 수 없습니다. 먼저 현재 필기를 백업해 주세요.');
    const mergedReview = [...new Set([...review, ...(records.session?.review || [])])];
    // One transaction makes restore all-or-nothing if storage becomes full.
    const session = {...await read('session'), review:mergedReview};
    await new Promise((resolve, reject) => {
      const tx = db.transaction('records', 'readwrite'), store = tx.objectStore('records');
      for (const [key, value] of notes) store.put(value, key);
      store.put(session, 'session');
      tx.oncomplete = resolve; tx.onerror = () => reject(tx.error); tx.onabort = () => reject(tx.error);
    });
    for (const [key, value] of notes) memory.set(key, value);
    memory.set('session', session); review = new Set(mergedReview);
    await showQuestion(false); toast(`${notes.length}문제의 필기를 불러왔습니다.`);
  } catch (error) { toast(error.message || '백업을 불러오지 못했습니다.'); }
});
$('download').onclick = () => guarded(async () => {
  if (!imageReady) { toast('문제 이미지가 로딩된 뒤 다시 눌러 주세요.'); return; }
  const output = document.createElement('canvas'); output.width = WIDTH; output.height = Math.ceil(height);
  const target = output.getContext('2d'); target.fillStyle = '#fff'; target.fillRect(0,0,WIDTH,height);
  target.drawImage($('question-image'),0,0,WIDTH,question().height / question().width * WIDTH);
  // Render ink separately so eraser strokes do not erase the source question.
  const ink = document.createElement('canvas'); ink.width = WIDTH; ink.height = output.height;
  for (const stroke of strokes) renderStroke(ink.getContext('2d'), stroke);
  target.drawImage(ink,0,0);
  output.toBlob(blob => { if (blob) downloadBlob(blob, `${question().id}-풀이.png`); else toast('이미지를 만들지 못했습니다.'); }, 'image/png');
});
$('offline').onclick = async () => {
  if (!('serviceWorker' in navigator) || !window.isSecureContext) { toast('오프라인 저장은 HTTPS로 접속한 앱에서 사용할 수 있습니다.'); return; }
  $('offline').disabled = true;
  try {
    const registration = await navigator.serviceWorker.ready;
    const channel = new MessageChannel();
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('저장 시간이 초과되었습니다. 연결을 확인하고 다시 시도하세요.')), 300000);
      channel.port1.onmessage = event => {
        const data = event.data;
        if (data.error) { clearTimeout(timer); reject(new Error(data.error)); }
        else if (data.done) { clearTimeout(timer); resolve(); }
        else $('offline-status').textContent = `${data.current} / ${data.total} 파일 저장 중…`;
      };
      registration.active.postMessage({type:'cache-all', urls:[...new Set(questions.flatMap(q => [q.image,q.source]))]}, [channel.port2]);
    });
    $('offline-status').textContent = '365문제와 원본 페이지를 저장했습니다. 오프라인에서도 이 주소로 열어 보세요.';
    if (navigator.storage?.persist) navigator.storage.persist().catch(() => {});
  } catch (error) { $('offline-status').textContent = error.message; }
  finally { $('offline').disabled = false; }
};
document.addEventListener('visibilitychange', () => { if (document.hidden) { finishStroke(); saveSession(); } });
window.addEventListener('pagehide', () => { finishStroke(); saveSession(); });
window.addEventListener('keydown', event => {
  if (event.target.matches('input,textarea,select') || document.querySelector('dialog[open]')) return;
  if (event.key === 'ArrowRight') $('next').click();
  if (event.key === 'ArrowLeft') $('previous').click();
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') { event.preventDefault(); $(event.shiftKey ? 'redo' : 'undo').click(); }
});
new ResizeObserver(resizeCanvas).observe($('paper'));
async function boot() {
  busy = true;
  try {
    try { db = await openDB(); } catch { storageFailure(); }
    const response = await fetch('questions.json'); if (!response.ok) throw new Error('문제 목록을 불러올 수 없습니다.');
    questions = await response.json(); byId = new Map(questions.map(q => [q.id,q]));
    let saved = await read('session').catch(() => { storageFailure(); return null; });
    try { const checkpoint = JSON.parse(localStorage.getItem('society-pencil-session')); if (checkpoint) saved = checkpoint; } catch { /* Fall back to IndexedDB. */ }
    if (saved) {
      review = new Set((saved.review || []).filter(id => byId.has(id)));
      $('start').value = saved.start || '12'; $('end').value = saved.end || '169';
      $('review-only').checked = !!saved.reviewOnly; $('pencil-only').checked = saved.pencilOnly !== false;
    }
    if (saved && Array.isArray(saved.deck) && saved.deck.length && saved.deck.every(id => byId.has(id)) && new Set(saved.deck).size === saved.deck.length && Number.isInteger(saved.index) && saved.index >= 0 && saved.index < saved.deck.length) {
      deck = saved.deck; index = saved.index; await showQuestion(false);
    } else { $('review-only').checked = false; $('start').value = '12'; $('end').value = '169'; await newDeck(false); }
    setTool('pen');
    if ('serviceWorker' in navigator && window.isSecureContext) navigator.serviceWorker.register('sw.js').catch(() => { $('offline-status').textContent = '오프라인 기능을 준비하지 못했습니다. 온라인 학습은 가능합니다.'; });
  } catch (error) { warn(`${error.message} 인터넷 연결을 확인한 뒤 새로고침해 주세요.`); $('save-status').textContent = '시작 실패'; }
  finally { busy = false; }
}
boot();
