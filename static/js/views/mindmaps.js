import { api, $, $$, esc, icon, toast, toastError, confirmDialog, relDay, modal } from "../lib.js";
import { mindmapModal } from "./library.js";

const NS = "http://www.w3.org/2000/svg";
let ctxMeasure;

export function render(view, [id]) {
  view.style.overflow = "hidden";
  view.innerHTML = `
    <div class="mm-layout">
      <aside class="mm-side">
        <button class="btn primary" id="mm-new" style="width:100%;justify-content:center;margin-bottom:12px">${icon("sparkle")} New mind map</button>
        <div class="tree-label">Your maps</div><div id="mm-list"></div>
      </aside>
      <section class="mm-stage" id="stage"></section>
    </div>`;
  $("#mm-new", view).onclick = newMap;
  loadList(id ? +id : null);
  return () => { view.style.overflow = ""; };
}

async function newMap() {
  const docs = await api("/documents");
  if (!docs.length) { toast("Upload notes first", { body: "Mind maps are generated from your Library." }); location.hash = "#/library"; return; }
  if (docs.length === 1) return mindmapModal(docs[0].id);
  modal({ title: "Choose a document", body: `<div class="field"><label>Document</label><select class="select" name="d">${docs.map(d => `<option value="${d.id}">${esc(d.title)}</option>`).join("")}</select></div>`,
    actions: [{ label: "Cancel" }, { label: "Continue", kind: "primary", run: (b) => { setTimeout(() => mindmapModal(+b.querySelector("select").value), 0); } }] });
}

async function loadList(openId) {
  let maps;
  try { maps = await api("/mindmaps"); } catch (e) { return toastError(e); }
  const list = $("#mm-list");
  if (!list) return;
  list.innerHTML = maps.map(m => `<div class="tree-item ${m.id === openId ? "active" : ""}" data-id="${m.id}" style="padding:6px 8px">
      <span class="emoji">${icon("mindmap")}</span><span class="t" title="${esc(m.title)}">${esc(m.title)}</span><span class="muted" style="font-size:10.5px">${relDay(m.created_at)}</span></div>`).join("")
    || `<div class="muted" style="padding:6px 8px;font-size:12px">No mind maps yet.</div>`;
  $$("[data-id]", list).forEach(el => el.onclick = () => { location.hash = `#/mindmaps/${el.dataset.id}`; });
  const target = openId || maps[0]?.id;
  if (target) show(target);
  else $("#stage").innerHTML = `<div style="display:grid;place-items:center;height:100%"><div class="empty" style="max-width:420px;background:#fff"><div class="big-ico">${icon("mindmap")}</div>
    <h3>Turn notes into a map</h3><p>Upload a chapter and Prepwise lays out its concepts so you see the whole topic at a glance.</p>
    <button class="btn primary" onclick="location.hash='#/library'">${icon("upload")} Go to Library</button></div></div>`;
}

async function show(id) {
  let m;
  try { m = await api(`/mindmaps/${id}`); } catch (e) { return toastError(e); }
  $$("#mm-list [data-id]").forEach(el => el.classList.toggle("active", +el.dataset.id === id));
  const stage = $("#stage");
  stage.innerHTML = `
    <div class="mm-toolbar"><h2>${esc(m.title)}</h2><span class="spacer"></span>
      <button class="btn sm" id="mm-note">${icon("notes")} Save as note</button>
      <button class="btn sm" id="mm-expand">${icon("list")} Expand all</button>
      <button class="icon-btn" id="mm-del" title="Delete" style="background:#fff;border:1px solid var(--border)">${icon("trash")}</button></div>
    <svg class="mm"><g class="vp"></g></svg>
    <div class="mm-zoom"><button data-z="in" title="Zoom in">${icon("zoomIn")}</button><button data-z="out" title="Zoom out">${icon("zoomOut")}</button><button data-z="fit" title="Fit">${icon("fit")}</button></div>
    <div class="mm-tip hidden"></div>`;
  $("#mm-note").onclick = async () => {
    const n = await api(`/mindmaps/${id}/to-note`, { method: "POST" });
    toast("Saved to Notes", { actions: [{ label: "Open", run: () => { location.hash = `#/notes/${n.id}`; } }] });
  };
  $("#mm-del").onclick = async () => {
    if (!(await confirmDialog("Delete mind map?", m.title))) return;
    await api(`/mindmaps/${id}`, { method: "DELETE" }); location.hash = "#/mindmaps"; loadList(null);
  };
  const root = { title: m.data.title || m.title, note: "", children: m.data.nodes || [], depth: 0 };
  const collapsed = new Set();
  // start with deep branches collapsed on big maps so the first view is readable
  const count = (n) => 1 + (n.children || []).reduce((a, c) => a + count(c), 0);
  if (count(root) > 40) (root.children || []).forEach((c, i) => collapsed.add(`0.${i}`));
  $("#mm-expand").onclick = () => { collapsed.clear(); draw(true); };
  const view = { x: 0, y: 0, k: 1 };
  const svg = $("svg.mm", stage), vp = $("g.vp", stage), tip = $(".mm-tip", stage);
  const apply = () => vp.setAttribute("transform", `translate(${view.x},${view.y}) scale(${view.k})`);
  let bounds = null;

  function draw(fit) {
    vp.innerHTML = "";
    bounds = layoutAndPaint(vp, root, collapsed, (node, key, isLeaf, parent) => {
      if (!isLeaf) { collapsed.has(key) ? collapsed.delete(key) : collapsed.add(key); draw(false); return; }
      askAbout(node, parent);
    }, tip, stage);
    if (fit) fitView();
  }
  function fitView() {
    const r = svg.getBoundingClientRect();
    const w = bounds.maxX - bounds.minX + 120, hgt = bounds.maxY - bounds.minY + 140;
    view.k = Math.min(1.25, Math.max(0.35, Math.min(r.width / w, r.height / hgt)));
    view.x = r.width / 2 - ((bounds.minX + bounds.maxX) / 2) * view.k;
    view.y = r.height / 2 + 20 - ((bounds.minY + bounds.maxY) / 2) * view.k;
    apply();
  }
  const zoom = (f, cx, cy) => {
    const r = svg.getBoundingClientRect();
    cx ??= r.width / 2; cy ??= r.height / 2;
    const k = Math.min(2.5, Math.max(0.25, view.k * f));
    view.x = cx - (cx - view.x) * (k / view.k); view.y = cy - (cy - view.y) * (k / view.k); view.k = k; apply();
  };
  $$("[data-z]", stage).forEach(b => b.onclick = () => (b.dataset.z === "fit" ? fitView() : zoom(b.dataset.z === "in" ? 1.2 : 1 / 1.2)));
  svg.addEventListener("wheel", (e) => { e.preventDefault(); const r = svg.getBoundingClientRect(); zoom(Math.exp(-e.deltaY * 0.0015), e.clientX - r.left, e.clientY - r.top); }, { passive: false });
  let drag = null;
  svg.addEventListener("pointerdown", (e) => { if (e.target.closest(".mm-node")) return; drag = { x: e.clientX - view.x, y: e.clientY - view.y }; svg.classList.add("dragging"); svg.setPointerCapture(e.pointerId); });
  svg.addEventListener("pointermove", (e) => { if (!drag) return; view.x = e.clientX - drag.x; view.y = e.clientY - drag.y; apply(); });
  svg.addEventListener("pointerup", () => { drag = null; svg.classList.remove("dragging"); });
  draw(true);
}

async function askAbout(node, parent) {
  const chat = await api("/chats", { method: "POST" });
  await api(`/chats/${chat.id}/messages`, { method: "POST", body: { content: `Explain “${node.title}”${parent && parent.depth > 0 ? ` (part of ${parent.title})` : ""} from my notes, with an example.` } });
  location.hash = `#/chat/${chat.id}`;
}

// ------------------------------------------------------------------ layout
function textWidth(s, font) {
  ctxMeasure ??= document.createElement("canvas").getContext("2d");
  ctxMeasure.font = font;
  return ctxMeasure.measureText(s).width;
}
const clip = (s, n) => (s.length > n ? s.slice(0, n - 1) + "…" : s);

function layoutAndPaint(vp, root, collapsed, onClick, tip, stage) {
  const STYLE = [
    { font: "600 15px Inter, sans-serif", h: 44, pad: 20, max: 34 },
    { font: "600 13px Inter, sans-serif", h: 36, pad: 16, max: 30 },
    { font: "500 12px Inter, sans-serif", h: 30, pad: 12, max: 34 },
    { font: "400 11.5px Inter, sans-serif", h: 26, pad: 10, max: 38 },
  ];
  const GAP_X = 56, GAP_Y = 10;
  const st = (d) => STYLE[Math.min(d, 3)];
  const prep = (n, d, key) => {
    n.depth = d; n.key = key;
    n.label = clip(n.title || "", st(d).max);
    n.w = textWidth(n.label, st(d).font) + st(d).pad * 2 + (n.children?.length && d > 0 ? 18 : 0);
    n.vis = collapsed.has(key) ? [] : (n.children || []);
    n.vis.forEach((c, i) => prep(c, d + 1, `${key}.${i}`));
  };
  prep(root, 0, "0");

  // vertical extent of a subtree
  const extent = (n) => (n.vis.length ? Math.max(st(n.depth).h, n.vis.reduce((a, c) => a + extent(c), 0) + GAP_Y * (n.vis.length - 1)) : st(n.depth).h);
  const place = (n, x, top, dir) => {
    const e = extent(n);
    n.x = x; n.y = top + e / 2; n.dir = dir;
    let cy = top + (e - (n.vis.reduce((a, c) => a + extent(c), 0) + GAP_Y * Math.max(0, n.vis.length - 1))) / 2;
    n.vis.forEach(c => {
      const cx = dir > 0 ? x + n.w / 2 + GAP_X + c.w / 2 : x - n.w / 2 - GAP_X - c.w / 2;
      place(c, cx, cy, dir); cy += extent(c) + GAP_Y;
    });
  };
  // balance main branches left/right
  const main = root.vis;
  const right = [], left = [];
  let rh = 0, lh = 0;
  main.forEach(c => { const e = extent(c); if (rh <= lh) { right.push(c); rh += e + GAP_Y * 2; } else { left.push(c); lh += e + GAP_Y * 2; } });
  root.x = 0; root.y = 0;
  const side = (list, dir, total) => {
    let y = -total / 2;
    list.forEach(c => {
      const cx = dir * (root.w / 2 + GAP_X + 20 + c.w / 2);
      place(c, cx, y, dir); y += extent(c) + GAP_Y * 2;
    });
  };
  side(right, 1, rh - GAP_Y * 2); side(left, -1, lh - GAP_Y * 2);

  const all = [];
  const walk = (n, parent) => { all.push([n, parent]); n.vis.forEach(c => walk(c, n)); };
  walk(root, null);

  const links = document.createElementNS(NS, "g");
  const nodes = document.createElementNS(NS, "g");
  vp.append(links, nodes);
  const b = { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity };
  for (const [n, p] of all) {
    b.minX = Math.min(b.minX, n.x - n.w / 2); b.maxX = Math.max(b.maxX, n.x + n.w / 2);
    b.minY = Math.min(b.minY, n.y - 20); b.maxY = Math.max(b.maxY, n.y + 20);
    if (p) {
      const dir = n.dir;
      const x1 = p.x + dir * p.w / 2, x2 = n.x - dir * n.w / 2, mx = (x1 + x2) / 2;
      const path = document.createElementNS(NS, "path");
      path.setAttribute("d", `M${x1},${p.y} C${mx},${p.y} ${mx},${n.y} ${x2},${n.y}`);
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", n.depth === 1 ? "#B9C9F8" : "#D5D8DF");
      path.setAttribute("stroke-width", n.depth === 1 ? 2 : 1.5);
      links.appendChild(path);
    }
    const g = document.createElementNS(NS, "g");
    g.setAttribute("class", "mm-node");
    const s = st(n.depth);
    const isLeaf = !(n.children && n.children.length);
    const fill = n.depth === 0 ? "#14161B" : n.depth === 1 ? "#FFFFFF" : n.depth === 2 ? "#FFFFFF" : "#F7F8FA";
    const stroke = n.depth === 0 ? "#14161B" : n.depth === 1 ? "#D5E0FD" : "#E1E3E8";
    const color = n.depth === 0 ? "#FFFFFF" : n.depth === 1 ? "#14161B" : n.depth === 2 ? "#2B303A" : "#4A505C";
    g.innerHTML = `<rect x="${n.x - n.w / 2}" y="${n.y - s.h / 2}" width="${n.w}" height="${s.h}" rx="${n.depth === 0 ? 14 : 10}" fill="${fill}" stroke="${stroke}" stroke-width="${n.depth === 1 ? 1.5 : 1}"/>
      ${n.depth === 1 ? `<rect x="${n.x - n.w / 2 + 6}" y="${n.y - 7}" width="3" height="14" rx="1.5" fill="#3D6BF5"/>` : ""}
      <text x="${n.x - (n.depth > 0 && !isLeaf ? 9 : 0)}" y="${n.y}" dominant-baseline="central" text-anchor="middle" style="font:${s.font}" fill="${color}">${esc(n.label)}</text>
      ${n.depth > 0 && !isLeaf ? `<g transform="translate(${n.x + n.w / 2 - 16},${n.y})"><circle r="8" fill="${collapsed.has(n.key) ? "#3D6BF5" : "#EEF3FF"}"/><text text-anchor="middle" dominant-baseline="central" style="font:600 10px Inter" fill="${collapsed.has(n.key) ? "#fff" : "#3D6BF5"}">${collapsed.has(n.key) ? n.children.length : "−"}</text></g>` : ""}`;
    g.onclick = (e) => { e.stopPropagation(); if (n.depth > 0) onClick(n, n.key, isLeaf, p); };
    g.onmouseenter = () => {
      const txt = [n.title !== n.label ? `<b>${esc(n.title)}</b>` : "", n.note ? esc(n.note) : "", n.depth > 0 ? `<span style="opacity:.6">${isLeaf ? "Click to ask Prepwise about this" : collapsed.has(n.key) ? "Click to expand" : "Click to collapse"}</span>` : ""].filter(Boolean).join("<br>");
      if (!txt) return;
      tip.innerHTML = txt; tip.classList.remove("hidden");
      const r = g.getBoundingClientRect(), sr = stage.getBoundingClientRect();
      tip.style.left = `${Math.min(sr.width - 290, Math.max(8, r.left - sr.left))}px`;
      tip.style.top = `${r.bottom - sr.top + 8}px`;
    };
    g.onmouseleave = () => tip.classList.add("hidden");
    nodes.appendChild(g);
  }
  return b;
}
