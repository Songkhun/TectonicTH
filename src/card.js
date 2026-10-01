import { t, field, getLang } from './i18n.js';
import { formatAge, esc } from './format.js';

export function createCard(el, { onPrev, onNext, onClose } = {}) {
  let shown = null;
  let lecture = false;

  function hide() {
    shown = null;
    el.hidden = true;
  }

  function render() {
    if (!shown) { el.hidden = true; return; }
    const e = shown;
    const badge = e.verified ? '' : `<span class="badge">${esc(t('draft'))}</span>`;
    const body = field(e, 'body') ? `<p>${esc(field(e, 'body'))}</p>` : '';
    const unit = e.rock_unit ? `<p class="card-unit">${esc(e.rock_unit)}</p>` : '';
    const site = e.visit_site
      ? `<p><strong>${esc(t('visit'))}:</strong> <a href="https://www.google.com/maps?q=${e.visit_site.lat},${e.visit_site.lon}" target="_blank" rel="noopener">${esc(field(e.visit_site, 'name'))}</a></p>`
      : '';
    const cite = e.citation
      ? `<p class="card-cite"><strong>${esc(t('source'))}:</strong> <a href="${esc(e.citation.url)}" target="_blank" rel="noopener">${esc(e.citation.text)}</a></p>`
      : '';
    const nav = lecture
      ? `<div class="card-nav"><button type="button" class="prev">← ${esc(t('prev'))}</button><button type="button" class="next">${esc(t('next'))} →</button></div>`
      : '';
    el.innerHTML = `<div class="card-head"><span class="card-age">${esc(formatAge(e.age_ma, e.age_uncertainty_ma, getLang()))}</span>${badge}<button type="button" class="card-close" aria-label="${esc(t('close'))}">×</button></div><h2>${esc(field(e, 'title'))}</h2>${body}${unit}${site}${cite}${nav}`;
    el.hidden = false;
    el.querySelector('.card-close').addEventListener('click', () => { hide(); if (onClose) onClose(); });
    if (lecture) {
      el.querySelector('.prev').addEventListener('click', () => onPrev && onPrev());
      el.querySelector('.next').addEventListener('click', () => onNext && onNext());
    }
  }

  function show(e) { shown = e; render(); }
  function lectureMode(on) { lecture = on; render(); }

  return { show, hide, refresh: render, lectureMode };
}
