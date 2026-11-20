import { api, $, $$, h, esc, icon, modal, toast, toastError } from "../lib.js";

export async function openQuiz(topicId, onDone) {
  const m = modal({ title: "Preparing quiz…", width: 600, body: `<div class="skeleton" style="height:120px"></div><div class="skeleton" style="height:120px"></div>` });
  let data;
  try { data = await api(`/topics/${topicId}/quiz`, { method: "POST" }); }
  catch (e) { m.close(); return toastError(e); }
  $(".modal-head h2", m.el).textContent = `Quiz · ${data.topic.title}`;
  const answers = new Array(data.questions.length).fill(null);
  m.body.innerHTML = `<p class="lead">Current mastery <b>${Math.round(data.topic.mastery)}%</b>. Answer honestly — your roadmap adapts to the result.</p>
    ${data.questions.map((q, i) => `<div class="q" data-q="${i}"><h4>${i + 1}. ${esc(q.q)}</h4>
      <div class="opts">${q.options.map((o, j) => `<button class="opt" data-o="${j}">${esc(o)}</button>`).join("")}</div></div>`).join("")}
    <button class="btn primary" style="align-self:flex-end" data-submit disabled>Check answers</button>`;
  $$(".q", m.body).forEach(qEl => {
    const i = +qEl.dataset.q;
    $$(".opt", qEl).forEach(b => b.onclick = () => {
      if (qEl.classList.contains("locked")) return;
      answers[i] = +b.dataset.o;
      $$(".opt", qEl).forEach(x => x.classList.toggle("picked", x === b));
      $("[data-submit]", m.body).disabled = answers.includes(null);
    });
  });
  $("[data-submit]", m.body).onclick = async (e) => {
    let score = 0;
    data.questions.forEach((q, i) => {
      const qEl = $(`[data-q="${i}"]`, m.body);
      qEl.classList.add("locked");
      const opts = $$(".opt", qEl);
      opts[q.answer].classList.add("right");
      if (answers[i] === q.answer) score++; else opts[answers[i]].classList.add("wrong");
      if (q.why) qEl.appendChild(h(`<div class="why">${icon("bulb")} ${esc(q.why)}</div>`));
    });
    e.target.remove();
    try {
      const res = await api(`/topics/${topicId}/quiz/submit`, { method: "POST", body: { score, total: data.questions.length } });
      const pct = Math.round(100 * score / data.questions.length);
      m.body.prepend(h(`<div class="score-ring"><b>${score}/${data.questions.length}</b>
        <div class="muted">${pct >= 80 ? "Excellent — this topic is getting solid." : pct >= 50 ? "Good progress. One more revision will lock it in." : "That's okay — this is exactly what practice is for."}
        Mastery is now <b style="color:var(--text)">${Math.round(res.mastery)}%</b>.</div></div>`));
      m.body.scrollTop = 0;
      onDone?.(res.mastery);
    } catch (err) { toastError(err); }
  };
}
