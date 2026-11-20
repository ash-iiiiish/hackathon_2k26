import { api, $, $$, esc, icon, modal, toast, toastError, confirmDialog, relDay, bytes, withLoading } from "../lib.js";

export function render(view) {
  view.innerHTML = `
    <div class="page">
      <div class="page-head"><div class="grow"><h1>Library</h1><p>Your study material. Everything here is indexed, so chat answers, mind maps and quizzes come from your own notes.</p></div>
        <div class="actions"><button class="btn" id="paste">${icon("edit")} Paste text</button></div></div>
      <label class="dropzone" id="drop">
        <div class="big-ico" style="width:40px;height:40px;margin:0 auto;border-radius:11px;background:#fff;display:grid;place-items:center;color:var(--accent);box-shadow:var(--shadow-sm)">${icon("upload")}</div>
        <h3>Drop your notes here</h3><p>PDF, Markdown or text · up to 15 MB · scanned PDFs need OCR first</p>
        <span class="btn primary">${icon("plus")} Choose files</span>
        <input type="file" multiple accept=".pdf,.md,.markdown,.txt" hidden>
      </label>
      <div id="docs"></div>
    </div>`;
  const drop = $("#drop", view), input = $("input", drop);
  input.onchange = () => upload([...input.files]).then(() => { input.value = ""; });
  ["dragenter", "dragover"].forEach(ev => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach(ev => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
  drop.addEventListener("drop", (e) => upload([...e.dataTransfer.files]));
  $("#paste", view).onclick = pasteModal;
  draw();
}

async function upload(files) {
  for (const f of files) {
    const form = new FormData(); form.append("file", f);
    const close = toast(`Indexing ${f.name}…`, { timeout: 0 });
    try {
      const d = await api("/documents", { method: "POST", form });
      close(); toast(`Added “${d.title}”`, { body: `${d.chunks} passages indexed.` });
    } catch (e) { close(); toastError(e); }
  }
  draw();
}

function pasteModal() {
  modal({
    title: "Paste notes", width: 620,
    body: `<div class="field"><label>Title</label><input class="input" name="title" placeholder="e.g. DBMS — Normalization"></div>
      <div class="field"><label>Notes</label><textarea class="textarea" name="text" rows="12" placeholder="Paste lecture notes, a chapter, or your own summary. Headings (# Title) help build better mind maps."></textarea></div>`,
    actions: [{ label: "Cancel" }, { label: "Add to library", kind: "primary", loading: "Indexing…", run: async (b) => {
      const form = new FormData();
      form.append("text", b.querySelector("[name=text]").value);
      if (b.querySelector("[name=title]").value) form.append("title", b.querySelector("[name=title]").value);
      await api("/documents", { method: "POST", form });
      draw();
    } }],
  });
}

async function draw() {
  const box = $("#docs");
  if (!box) return;
  let docs;
  try { docs = await api("/documents"); } catch (e) { return toastError(e); }
  if (!docs.length) {
    box.innerHTML = `<div class="empty"><div class="big-ico">${icon("library")}</div><h3>No material yet</h3><p>Upload a chapter, then generate a mind map — Prepwise will also pull out the exam topics for your roadmap.</p></div>`;
    return;
  }
  box.innerHTML = `<div class="panel"><div class="panel-head"><h3>Documents</h3><span class="sub">${docs.length} file${docs.length > 1 ? "s" : ""}</span></div>
    <div class="panel-body" style="padding-top:8px">${docs.map(d => `
      <div class="list-row">
        <div class="file-ico ${d.kind === "pdf" ? "" : "blue"}">${icon(d.kind === "pdf" ? "pdf" : "file")}</div>
        <div class="row-main"><div class="row-title">${esc(d.title)}</div>
          <div class="row-meta">${d.kind === "pdf" ? "PDF" : d.kind === "pasted" ? "Pasted" : "Notes"} · ${bytes(d.size_bytes)} · ${d.chunks} passages · ${relDay(d.created_at)}${d.mindmaps ? ` · ${d.mindmaps} mind map${d.mindmaps > 1 ? "s" : ""}` : ""}</div></div>
        <div class="actions">
          <button class="btn sm" data-view="${d.id}">${icon("eye")} View</button>
          <button class="btn sm primary" data-mm="${d.id}" data-loading="Mapping…">${icon("mindmap")} Mind map</button>
          <button class="icon-btn" data-del="${d.id}" title="Delete">${icon("trash")}</button>
        </div>
      </div>`).join("")}</div></div>`;
  $$("[data-mm]", box).forEach(b => b.onclick = () => mindmapModal(+b.dataset.mm));
  $$("[data-view]", box).forEach(b => b.onclick = async () => {
    const d = await api(`/documents/${b.dataset.view}`);
    modal({ title: d.title, width: 720, body: `<pre style="white-space:pre-wrap;font:13px/1.65 var(--font);margin:0">${esc(d.content)}</pre>` });
  });
  $$("[data-del]", box).forEach(b => b.onclick = async () => {
    if (!(await confirmDialog("Delete document?", "Its passages will no longer be used for answers. Mind maps made from it are kept."))) return;
    await api(`/documents/${b.dataset.del}`, { method: "DELETE" }); draw();
  });
}

export function mindmapModal(documentId) {
  modal({
    title: "Generate mind map", width: 520,
    body: `<p class="lead">Builds a mind map from this document using retrieval over its passages, and adds the exam topics it finds to your syllabus.</p>
      <div class="field"><label>Focus <span class="muted">(optional)</span></label><input class="input" name="focus" placeholder="e.g. deadlocks — leave empty for the whole document">
      <span class="hint">With a focus, only the most relevant passages are used.</span></div>
      <label style="display:flex;gap:8px;align-items:center;font-size:12.5px"><input type="checkbox" name="topics" checked style="accent-color:var(--accent)"> Add topics to my syllabus & roadmap</label>`,
    actions: [{ label: "Cancel" }, { label: `${icon("sparkle")} Generate`, kind: "primary", loading: "Reading your notes…", run: async (b) => {
      const m = await api("/mindmaps", { method: "POST", body: {
        document_id: documentId, focus: b.querySelector("[name=focus]").value, extract_topics: b.querySelector("[name=topics]").checked } });
      if (m.topics_added?.length) toast("Topics added", { body: `${m.topics_added.length} topics are now in your syllabus. Rebuild your roadmap to schedule them.` });
      location.hash = `#/mindmaps/${m.id}`;
    } }],
  });
}
