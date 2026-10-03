import { t, field, getLang } from './i18n.js';
import { esc } from './format.js';

// Horizontal layout for one question: older ages on the left, one row of phase bars per model,
// and evidence markers spanning their stated age range (clamped to the axis window).
export function modelLayout(q, width, { left = 120, right = 12 } = {}) {
  const { base_ma: base, top_ma: top } = q.axis;
  const span = width - left - right;
  const x = age => left + ((base - age) / (base - top)) * span;
  const range = (b, tp) => {
    const x0 = x(Math.min(b, base));
    return { x: x0, w: x(Math.max(tp, top)) - x0 };
  };
  return {
    x,
    rows: q.models.map(m => ({ model: m, bars: m.phases.map(ph => ({ ...range(ph.base_ma, ph.top_ma), phase: ph })) })),
    markers: q.evidence.map(ev => ({ ...range(ev.age_base_ma, ev.age_top_ma), ev })),
  };
}

const MARK = { supports: '✓', challenges: '✗', neutral: '–' };

export function rolesTableHtml(q, evidenceById) {
  const head = q.models.map(m => `<th scope="col">${esc(field(m, 'name'))}</th>`).join('');
  const rows = q.evidence.map(ev => {
    const it = evidenceById[ev.evidence_id] || {};
    const cells = q.models.map(m => {
      const role = ev.roles[m.id] || 'neutral';
      return `<td class="role role-${esc(role)}" title="${esc(t(`role_${role}`))}">${MARK[role] || '–'}</td>`;
    }).join('');
    return `<tr data-evidence="${esc(ev.evidence_id)}"><th scope="row"><button type="button" class="mdl-ev">${esc(field(it, 'title') || ev.evidence_id)}</button>`
      + `<span class="mdl-ev-method">${esc(t(`method_${it.method}`))}</span></th>${cells}<td class="mdl-reason">${esc(field(ev, 'reason'))}</td></tr>`;
  }).join('');
  return `<table class="mdl-table"><thead><tr><th scope="col">${esc(t('models_evidence'))}</th>${head}<th scope="col">${esc(t('models_why'))}</th></tr></thead><tbody>${rows}</tbody></table>`;
}

// Draw every question: phase bars per model, a data row of evidence markers, the roles table and synthesis.
export function renderModels(container, data, { onEvidence }) {
  const evidenceById = Object.fromEntries((data.evidence || []).map(it => [it.id, it]));
  const width = Math.max(320, container.clientWidth - 32);
  const rowH = 26;
  container.innerHTML = '';
  for (const q of data.models || []) {
    const sec = document.createElement('section');
    sec.className = 'mdl-q';
    const L = modelLayout(q, width, { left: Math.min(170, width * 0.32), right: 12 });
    const h = (q.models.length + 1) * rowH + 30;
    const ticks = d3.ticks(q.axis.top_ma, q.axis.base_ma, 6);
    let svg = `<svg class="mdl-chart" viewBox="0 0 ${width} ${h}" width="${width}" height="${h}" role="img" aria-label="${esc(field(q, 'title'))}">`;
    for (const tk of ticks) {
      svg += `<line class="mdl-grid" x1="${L.x(tk)}" x2="${L.x(tk)}" y1="0" y2="${h - 18}"></line><text class="mdl-tick" x="${L.x(tk)}" y="${h - 4}">${tk}</text>`;
    }
    L.rows.forEach((row, i) => {
      const y = i * rowH + 4;
      svg += `<text class="mdl-name" x="0" y="${y + 15}">${esc(field(row.model, 'name'))}</text>`;
      for (const b of row.bars) {
        svg += `<rect class="mdl-bar mdl-bar-${i % 4}" x="${b.x}" y="${y + 3}" width="${Math.max(2, b.w)}" height="${rowH - 8}" rx="3"><title>${esc(field(b.phase, 'label'))} · ${b.phase.base_ma}–${b.phase.top_ma} Ma</title></rect>`;
      }
    });
    const dy = q.models.length * rowH + 4;
    svg += `<text class="mdl-name mdl-data" x="0" y="${dy + 15}">${esc(t('models_data_row'))}</text>`;
    for (const m of L.markers) {
      const it = evidenceById[m.ev.evidence_id] || {};
      const cx = m.x + m.w / 2;
      svg += `<g class="mdl-marker" data-evidence="${esc(m.ev.evidence_id)}" tabindex="0" role="button" aria-label="${esc(field(it, 'title'))}">`
        + (m.w > 1 ? `<line x1="${m.x}" x2="${m.x + m.w}" y1="${dy + 12}" y2="${dy + 12}"></line>` : '')
        + `<circle cx="${cx}" cy="${dy + 12}" r="5"></circle><title>${esc(field(it, 'title'))} · ${m.ev.age_base_ma}–${m.ev.age_top_ma} Ma</title></g>`;
    }
    svg += '</svg>';
    const modelsList = q.models.map(m => `<li><strong>${esc(field(m, 'name'))}</strong> — ${esc(field(m, 'summary'))} `
      + `<a href="${esc(m.citation.url)}" target="_blank" rel="noopener">${esc(m.citation.text)}</a></li>`).join('');
    sec.innerHTML = `<h2>${esc(field(q, 'title'))}${q.verified ? '' : ` <span class="badge">${esc(t('draft'))}</span>`}</h2>`
      + `<p class="mdl-question">${esc(field(q, 'question'))}</p><div class="mdl-chart-wrap">${svg}</div>`
      + `<ul class="mdl-models">${modelsList}</ul><div class="mdl-table-wrap">${rolesTableHtml(q, evidenceById)}</div>`
      + `<h3>${esc(t('models_synthesis'))}</h3><p>${esc(field(q, 'synthesis'))}</p>`;
    container.appendChild(sec);
  }
  container.onclick = ev => {
    const hit = ev.target.closest('[data-evidence]');
    if (hit && evidenceById[hit.dataset.evidence]) onEvidence(evidenceById[hit.dataset.evidence]);
  };
  container.onkeydown = ev => {
    const hit = ev.target.closest('.mdl-marker');
    if (hit && (ev.key === 'Enter' || ev.key === ' ')) { ev.preventDefault(); onEvidence(evidenceById[hit.dataset.evidence]); }
  };
}
