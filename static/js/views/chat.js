import { state, api, $, $$, h, esc, icon, md, toast, toastError, hm, mins } from "../lib.js";
import { openQuiz } from "./quiz.js";

const COMMANDS = [
  ["/mindmap", "Mind map from your latest notes"],
  ["/roadmap", "Plan every topic until the exam"],
  ["/crisis 4", "Exam close? High-yield plan for 4 hours"],
  ["/quiz", "Quiz your weakest topic"],
  ["/progress", "Readiness snapshot"],
  ["/help", "All commands"],
];

let pending = null; // message typed on the home screen, sent once the chat view mounts

export function render(view, [chatId], ctx) {
  return chatId ? renderThread(view, +chatId, ctx) : renderHome(view, ctx);
}

// ------------------------------------------------------------------ home
function renderHome(view, ctx) {
  const name = (state.student.name || "").split(" ")[0];
  view.innerHTML = `
    <div class="home">
      <section class="hero">
        <h1>Study smarter,<br><span class="soft">not later.</span></h1>
        <p>Hi ${esc(name)} — ask anything about your notes, or let me turn them into a mind map and a calm plan to exam day.</p>
        <div class="suggestions">
          <button class="suggestion" data-cmd="/mindmap"><span class="ico">${icon("mindmap")}</span>Generate mind map</button>
          <button class="suggestion" data-cmd="/roadmap"><span class="ico">${icon("route")}</span>Plan till my exam</button>
          <button class="suggestion hot" data-crisis><span class="ico">${icon("zap")}</span>Exam tomorrow?</button>
          <button class="suggestion" data-cmd="/quiz"><span class="ico">${icon("quiz")}</span>Quiz my weakest topic</button>
        </div>
        <div class="today-strip" id="today-strip"></div>
      </section>
      ${composer()}
    </div>`;
  wireComposer(view, async (text) => {
    const chat = await api("/chats", { method: "POST" });
    pending = text;
    location.hash = `#/chat/${chat.id}`;
  });
  $$("[data-cmd]", view).forEach(b => b.onclick = () => send(view, b.dataset.cmd));
  $("[data-crisis]", view).onclick = () => { location.hash = "#/planner/crisis"; };
  loadToday(view);
}

function send(view, text) {
  const ta = $("textarea", view);
  ta.value = text;
  $("[data-send]", view).click();
}

async function loadToday(view) {
  const strip = $("#today-strip", view);
  try {
    const [assess, roadmap] = await Promise.all([api("/plan/assess"), api("/plan/roadmap")]);
    const next = roadmap?.events?.find(e => e.status === "planned" && new Date(e.end_at) > new Date() && e.kind !== "exam");
    const items = [];
    if (assess.days_left !== null) items.push(`<div class="mini">${icon("calendar")}<span><b>${assess.days_left}</b> days to exam</span></div>`);
    if (next) items.push(`<button class="mini" onclick="location.hash='#/planner'"><i class="dot"></i><span>Next: <b>${esc(next.title)}</b> · ${new Date(next.start_at).toDateString() === new Date().toDateString() ? "today" : new Date(next.start_at).toLocaleDateString(undefined, { weekday: "short" })} ${hm(next.start_at)}</span></button>`);
    if (assess.recommend_crisis && assess.topics) items.push(`<button class="mini" style="border-color:#F6C9CB;background:var(--bad-bg);color:#8E1C20" onclick="location.hash='#/planner/crisis'">${icon("alert")}<span>${esc(assess.reason)}</span></button>`);
    else if (!assess.topics) items.push(`<button class="mini" onclick="location.hash='#/library'">${icon("upload")}<span>Start by uploading your notes in <b>Library</b></span></button>`);
    strip.innerHTML = items.join("");
  } catch { /* first run */ }
}

// ------------------------------------------------------------------ composer
function composer() {
  return `
    <div class="composer-wrap">
      <div class="slash-menu hidden"></div>
      <div class="composer">
        <textarea rows="1" placeholder="Type / for command, or ask about your notes"></textarea>
        <div class="composer-row">
          <button class="tool" data-attach title="Upload notes (PDF, .md, .txt)">${icon("paperclip")}</button>
          <button class="tool" data-tools>${icon("tools")}Tools</button>
          <button class="tool" data-search>${icon("globe")}Search</button>
          <span class="spacer"></span>
          <button class="send" data-send disabled aria-label="Send">${icon("arrowUp")}</button>
        </div>
        <input type="file" accept=".pdf,.md,.markdown,.txt" hidden>
      </div>
      <div class="disclaimer">Prepwise may make mistakes. Check important facts against your syllabus.</div>
    </div>`;
}

function wireComposer(view, onSend, ctx) {
  const ta = $(".composer textarea", view);
  const sendBtn = $("[data-send]", view);
  const menu = $(".slash-menu", view);
  let sel = 0;
  const grow = () => { ta.style.height = "auto"; ta.style.height = Math.min(200, ta.scrollHeight) + "px"; sendBtn.disabled = !ta.value.trim(); };
  const showMenu = () => {
    const q = ta.value.trim();
    const list = q.startsWith("/") && !q.includes(" ") ? COMMANDS.filter(c => c[0].startsWith(q.split(" ")[0])) : [];
    menu.classList.toggle("hidden", !list.length);
    sel = Math.min(sel, Math.max(0, list.length - 1));
    menu.innerHTML = list.map((c, i) => `<button class="${i === sel ? "sel" : ""}" data-c="${c[0]}"><code>${c[0]}</code><span>${c[1]}</span></button>`).join("");
    $$("[data-c]", menu).forEach(b => b.onmousedown = (e) => { e.preventDefault(); ta.value = b.dataset.c + " "; grow(); menu.classList.add("hidden"); ta.focus(); });
  };
  ta.oninput = () => { grow(); showMenu(); };
  ta.onkeydown = (e) => {
    const open = !menu.classList.contains("hidden");
    if (open && (e.key === "ArrowDown" || e.key === "ArrowUp")) {
      e.preventDefault(); const n = $$("[data-c]", menu).length;
      sel = (sel + (e.key === "ArrowDown" ? 1 : n - 1)) % n; showMenu(); return;
    }
    if (open && (e.key === "Tab" || e.key === "Enter")) {
      e.preventDefault(); const b = $$("[data-c]", menu)[sel];
      if (b) { ta.value = b.dataset.c + " "; grow(); menu.classList.add("hidden"); } return;
    }
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendBtn.click(); }
  };
  sendBtn.onclick = async () => {
    const text = ta.value.trim();
    if (!text) return;
    ta.value = ""; grow(); menu.classList.add("hidden");
    try { await onSend(text); } catch (e) { toastError(e); }
  };
  $("[data-tools]", view).onclick = () => { ta.value = "/"; grow(); showMenu(); ta.focus(); };
  $("[data-search]", view).onclick = () => document.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true }));
  const file = $("input[type=file]", view);
  $("[data-attach]", view).onclick = () => file.click();
  file.onchange = async () => {
    if (!file.files[0]) return;
    const form = new FormData(); form.append("file", file.files[0]);
    const close = toast("Uploading notes…", { timeout: 0 });
    try {
      const doc = await api("/documents", { method: "POST", form });
      close();
      toast(`Added “${doc.title}”`, { body: `${doc.chunks} passages indexed for answers.`, actions: [
        { label: "Make mind map", run: () => send(view, "/mindmap") },
      ] });
    } catch (e) { close(); toastError(e); }
    file.value = "";
  };
  setTimeout(() => ta.focus(), 30);
}

// ------------------------------------------------------------------ thread
function renderThread(view, chatId, ctx) {
  view.innerHTML = `<div class="chat"><div class="chat-scroll"><div class="thread" id="thread"></div></div>${composer()}</div>`;
  const thread = $("#thread", view);
  const scroll = $(".chat-scroll", view);
  const toBottom = () => { scroll.scrollTop = scroll.scrollHeight; };

  const addUser = (text) => thread.appendChild(h(`<div class="msg-user">${esc(text)}</div>`));
  const addBot = (m) => {
    const meta = m.meta || {};
    const el = h(`<div class="msg-bot"><div class="bot-ico">${icon("logo")}</div><div class="msg-body"><div class="md">${md(m.content)}</div></div></div>`);
    const body = $(".msg-body", el);
    if (meta.sources?.length) {
      body.appendChild(h(`<div class="sources">${meta.sources.map(s => `<span class="source" title="${esc(s.snippet)}"><b>${s.n}</b><span>${esc(s.heading || s.document)}</span></span>`).join("")}</div>`));
    }
    const card = actionCard(meta);
    if (card) body.appendChild(card);
    thread.appendChild(el);
  };

  async function sendText(text) {
    addUser(text);
    const typing = h(`<div class="msg-bot"><div class="bot-ico">${icon("logo")}</div><div class="typing"><i></i><i></i><i></i></div></div>`);
    thread.appendChild(typing); toBottom();
    try {
      const res = await api(`/chats/${chatId}/messages`, { method: "POST", body: { content: text } });
      typing.remove(); addBot(res.assistant); toBottom();
      ctx.refreshSidebar();
    } catch (e) { typing.remove(); toastError(e); }
  }

  wireComposer(view, sendText, ctx);
  (async () => {
    try {
      const chat = await api(`/chats/${chatId}`);
      chat.messages.forEach(m => (m.role === "user" ? addUser(m.content) : addBot(m)));
      toBottom();
      if (pending) { const p = pending; pending = null; sendText(p); }
    } catch (e) { toastError(e); location.hash = "#/"; }
  })();
}

function actionCard(meta) {
  const map = {
    mindmap: ["mindmap", "Open mind map", () => { location.hash = `#/mindmaps/${meta.id}`; }],
    planner: ["calendar", "Open planner", () => { location.hash = "#/planner/roadmap"; }],
    quiz: ["quiz", "Start quiz", () => openQuiz(meta.id)],
    progress: ["chart", "Open progress report", () => { location.hash = "#/progress"; }],
    library: ["upload", "Go to Library", () => { location.hash = "#/library"; }],
  };
  const a = map[meta.action];
  if (!a) return null;
  const el = h(`<div class="action-card"><span class="ico">${icon(a[0])}</span><div>${a[1]}</div><button class="btn sm primary">Open</button></div>`);
  $("button", el).onclick = a[2];
  return el;
}
