import { t, field, getLang } from './i18n.js';
import { esc, formatLat } from './format.js';

export const EVIDENCE_METHODS = ['paleomagnetism', 'geochronology', 'biostratigraphy', 'seismic', 'gravity',
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
  return `${head} · ${th ? 'แบบจำลอง' : 'model'} ${formatLat(modelLat)}`;
}

export function evidenceHtml(eventId, items, modelLat) {
  const list = evidenceFor(eventId, items);
  if (!list.length) return '';
  const lang = getLang();
  const rows = list.map(it => {
    const badge = it.verified ? '' : ` <span class="badge">${esc(t('draft'))}</span>`;
    const value = it.value ? `<span class="ev-value">${esc(it.value)}</span>` : '';
    const compare = it.paleolat
      ? `<span class="ev-compare">${esc(formatPaleolatCompare(it.paleolat, modelLat, lang))}</span>`
      : '';
    const data = value || compare ? `<p class="ev-data">${value}${value && compare ? ' · ' : ''}${compare}</p>` : '';
    const site = it.site
      ? ` · <a href="https://www.google.com/maps?q=${it.site.lat},${it.site.lon}" target="_blank" rel="noopener">${esc(field(it.site, 'name'))}</a>`
      : '';
    return `<li class="ev-item"><div class="ev-head"><span class="ev-chip ev-${esc(it.method)}">${esc(t(`method_${it.method}`))}</span>`
      + `<strong>${esc(field(it, 'title'))}</strong>${badge}</div>`
      + `<p>${esc(field(it, 'finding'))}</p>${data}`
      + `<p class="ev-cite"><a href="${esc(it.citation.url)}" target="_blank" rel="noopener">${esc(it.citation.text)}</a>${site}</p></li>`;
  }).join('');
  return `<section class="evidence"><h3>${esc(t('evidence_heading'))}</h3><ul>${rows}</ul></section>`;
}
