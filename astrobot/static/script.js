const $ = id => document.getElementById(id);
const box = $('messages'), input = $('input');
const FALLBACK = "Hmm 🤔 I didn't catch that. Try one of the suggested questions!";
var rows = [];

// Local matcher (same idea as the Python code) - used when no server is running
function similarity(a, b) {
  const A = new Set(a.split(/\W+/)), B = new Set(b.split(/\W+/));
  return [...A].filter(w => B.has(w)).length / Math.max(A.size, B.size);
}
function localReply(msg) {
  msg = msg.toLowerCase().trim();
  const scored = rows.map(r => [r.keywords.filter(k => new RegExp('\\b' + k + '\\b').test(msg)).length, r]);
  const best = scored.reduce((a, b) => (b[0] > a[0] ? b : a), [0, null]);
  if (best[0] > 0) return best[1].answer;
  const fuzzy = rows.map(r => [similarity(msg, r.question), r]).sort((a, b) => b[0] - a[0])[0];
  return fuzzy && fuzzy[0] >= 0.5 ? fuzzy[1].answer : FALLBACK;
}
async function getReply(msg) {
  try {
    const res = await fetch('/api/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: msg})});
    if (!res.ok) throw 0;
    return (await res.json()).reply;
  } catch { return localReply(msg); }
}
function add(text, who) {
  const d = document.createElement('div');
  d.className = 'msg ' + who; d.textContent = text;
  box.appendChild(d); box.scrollTop = box.scrollHeight; return d;
}
async function send(text) {
  text = text.trim(); if (!text) return;
  add(text, 'user'); input.value = '';
  const t = document.createElement('div');
  t.className = 'msg bot typing'; t.innerHTML = '<i></i><i></i><i></i>';
  box.appendChild(t); box.scrollTop = box.scrollHeight;
  const [reply] = await Promise.all([getReply(text), new Promise(r => setTimeout(r, 700))]);
  t.remove(); add(reply, 'bot');
}
function buildSuggestions() {
  const wrap = $('suggestions'); wrap.innerHTML = ''; let last = '';
  rows.filter(r => r.category !== 'Basics').forEach(r => {
    if (r.category !== last) { const c = document.createElement('div'); c.className = 'cat'; c.textContent = r.category; wrap.appendChild(c); last = r.category; }
    const b = document.createElement('button'); b.className = 'chip'; b.textContent = r.question.charAt(0).toUpperCase() + r.question.slice(1) + '?';
    b.onclick = () => send(r.question); wrap.appendChild(b);
  });
}
// Screens
let greeted = false;
function showChat() {
  $('welcome').hidden = true; $('chatScreen').hidden = false;
  if (!greeted) { add("Hello! 🚀 I am AstroBot. Ask me anything about space, or tap a suggested question!", 'bot'); greeted = true; }
  input.focus({preventScroll: true});
}
function showHome() { $('chatScreen').hidden = true; $('welcome').hidden = false; }
const openGuide = () => { $('guide').hidden = false; $('gotIt').focus(); };
const closeGuide = () => { $('guide').hidden = true; };
async function init() {
  try { const res = await fetch('/api/data'); if (!res.ok) throw 0; rows = await res.json(); }
  catch { rows = window.EMBEDDED || []; }
  buildSuggestions();
}
$('startBtn').onclick = showChat;
$('homeBtn').onclick = showHome;
$('guideBtn').onclick = $('guideBtn2').onclick = openGuide;
$('closeGuide').onclick = $('gotIt').onclick = closeGuide;
$('guide').addEventListener('click', e => { if (e.target.id === 'guide') closeGuide(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeGuide(); });
$('form').addEventListener('submit', e => { e.preventDefault(); send(input.value); });
init();
