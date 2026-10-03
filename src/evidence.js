import { t, field, getLang } from './i18n.js';
import { esc, formatLat } from './format.js';

export const EVIDENCE_METHODS = ['paleomagnetism', 'geochronology', 'thermochronology', 'biostratigraphy', 'geochemistry', 'mapping', 'seismic', 'gravity',
  'magnetic', 'electrical', 'seismicity', 'geodesy', 'field-survey'];

export function evidenceFor(eventId, items) {
  return items.filter(it => it.event_ids.includes(eventId));
}

export function formatPaleolatCompare(paleolat, modelLat, lang) {
  const th = lang === 'th';
  const err = paleolat.err == null ? '' : ` ± ${paleolat.err}`;
  const measured = `${Math.abs(paleolat.deg)}${err}°${paleolat.deg < 0 ? 'S' : 'N'}`;
  const head = `${th ? 'วัดได้' : 'measured'} ${measured}`;
  if (modelLat == null) return head;
  return `${head} · ${th ? 'แบบจำลอง ณ จุดเก็บตัวอย่าง' : 'model at site'} ${formatLat(modelLat)}`;
}

export function evidenceHtml(eventId, items) {
  const list = evidenceFor(eventId, items);
  if (!list.length) return '';
  const lang = getLang();
  const rows = list.map(it => {
    const badge = it.verified ? '' : ` <span class="badge">${esc(t('draft'))}</span>`;
    const value = it.value ? `<span class="ev-value">${esc(it.value)}</span>` : '';
    const compare = it.paleolat
      ? `<span class="ev-compare">${esc(formatPaleolatCompare(it.paleolat, it.model_paleolat ? it.model_paleolat.deg : null, lang))}</span>`
      : '';
    const data = value || compare ? `<p class="ev-data">${value}${value && compare ? ' · ' : ''}${compare}</p>` : '';
    const site = it.site
      ? ` · <a href="https://www.google.com/maps?q=${esc(it.site.lat)},${esc(it.site.lon)}" target="_blank" rel="noopener">${esc(field(it.site, 'name'))}</a>`
      : '';
    return `<li class="ev-item"><div class="ev-head"><span class="ev-chip ev-${esc(it.method)}">${esc(t(`method_${it.method}`))}</span>`
      + `<strong>${esc(field(it, 'title'))}</strong>${badge}</div>`
      + `<p>${esc(field(it, 'finding'))}</p>${data}`
      + `<p class="ev-cite"><a href="${esc(it.citation.url)}" target="_blank" rel="noopener">${esc(it.citation.text)}</a>${site}</p></li>`;
  }).join('');
  return `<section class="evidence"><h3>${esc(t('evidence_heading'))}</h3><ul>${rows}</ul></section>`;
}

// A single evidence item as a card (used when it is opened from the map or the models table).
export function evidenceItemCardHtml(it) {
  const inner = evidenceHtml(it.event_ids[0], [it]).replace(/^<section class="evidence">.*?<ul>/, '<ul class="ev-single">');
  return `<div class="card-head"><span class="card-age">${esc(t('evidence_heading'))}</span>`
    + `<button type="button" class="card-close" aria-label="${esc(t('close'))}">×</button></div>${inner.replace(/<\/section>$/, '')}`;
}
