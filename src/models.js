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
