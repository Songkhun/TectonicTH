import { t, getLang } from './i18n.js';
import { esc } from './format.js';
import { ageToY } from './layout.js';

export const FOSSIL_GROUPS = {
  trilobite: { icon: '🪲', th: 'ไทรโลไบต์', en: 'Trilobite' },
  nautiloid: { icon: '🦑', th: 'นอติลอยด์', en: 'Nautiloid' },
  graptolite: { icon: '🪶', th: 'แกรปโตไลต์', en: 'Graptolite' },
  conodont: { icon: '🦷', th: 'โคโนดอนต์', en: 'Conodont' },
  tentaculitid: { icon: '📍', th: 'เทนตาคูไลติด', en: 'Tentaculitid' },
  brachiopod: { icon: '🦪', th: 'แบรคิโอพอด', en: 'Brachiopod' },
  fusulinid: { icon: '🌾', th: 'ฟิวซูลินิด', en: 'Fusulinid' },
  coral: { icon: '🪸', th: 'ปะการัง', en: 'Coral' },
  ammonoid: { icon: '🐚', th: 'แอมโมนอยด์', en: 'Ammonoid' },
  bivalve: { icon: '🫘', th: 'หอยสองฝา', en: 'Bivalve' },
  gastropod: { icon: '🐌', th: 'หอยฝาเดียว', en: 'Gastropod' },
  radiolarian: { icon: '✳️', th: 'เรดิโอลาเรียน', en: 'Radiolarian' },
  crinoid: { icon: '🌿', th: 'ไครนอยด์', en: 'Crinoid' },
  fish: { icon: '🐟', th: 'ปลา', en: 'Fish' },
  reptile: { icon: '🐊', th: 'สัตว์เลื้อยคลาน', en: 'Reptile' },
  dinosaur: { icon: '🦕', th: 'ไดโนเสาร์', en: 'Dinosaur' },
  mammal: { icon: '🐘', th: 'สัตว์เลี้ยงลูกด้วยนม', en: 'Mammal' },
  primate: { icon: '🐒', th: 'ไพรเมต', en: 'Primate' },
  plant: { icon: '🌳', th: 'พืช', en: 'Plant' },
  amphibian: { icon: '🐸', th: 'สัตว์สะเทินน้ำสะเทินบก', en: 'Amphibian' },
  other: { icon: '🦴', th: 'อื่น ๆ', en: 'Other' },
};

export function fossilMidAge(f) {
  return (f.age_top_ma + f.age_base_ma) / 2;
}

// Icons sit at their mid-age, linear inside the band of their period. Overlaps move to the next
// column, then down; every icon is clamped to its own band so it never reads as the wrong period,
// and a crowded band compresses the spacing instead of spilling into the next one.
export function placeFossils(bands, fossils, { size = 18, columns = 2, gap = 2 } = {}) {
  const out = [];
  for (const band of bands) {
    const p = band.period;
    const top = band.y;
    const bottom = band.y + band.h - size;
    const items = fossils
      .filter(f => { const m = fossilMidAge(f); return m <= p.start_ma && m >= p.end_ma; })
      .map(f => ({ fossil: f, y0: Math.min(bottom, Math.max(top, ageToY(fossilMidAge(f), [band]) - size / 2)) }))
      .sort((a, b) => a.y0 - b.y0);
    const cols = Array.from({ length: columns }, () => []);
    const ends = new Array(columns).fill(-Infinity);
    for (const it of items) {
      let col = ends.findIndex(e => it.y0 >= e);
      let y = it.y0;
      if (col < 0) {
        col = ends.indexOf(Math.min(...ends));
        y = ends[col];
      }
      ends[col] = y + size;
      cols[col].push({ fossil: it.fossil, y });
    }
    cols.forEach((list, col) => {
      const last = list[list.length - 1];
      if (list.length > 1 && last.y > bottom) {
        const first = Math.min(list[0].y, bottom);
        const step = (bottom - first) / (list.length - 1);
        list.forEach((it, i) => { it.y = first + i * step; });
      }
      list.forEach(it => out.push({ x: col * (size + gap), y: Math.min(bottom, it.y), fossil: it.fossil }));
    });
  }
  return out;
}

export function localityText(loc, lang) {
  if (lang === 'th') {
    return [loc.name_th || loc.name_en, loc.tambon_th && `ต.${loc.tambon_th}`, loc.amphoe_th && `อ.${loc.amphoe_th}`, `จ.${loc.province_th}`]
      .filter(Boolean).join(' ');
  }
  return [loc.name_en, loc.tambon_th && `Tambon ${loc.tambon_th}`, loc.amphoe_th && `Amphoe ${loc.amphoe_th}`, `${loc.province_en} Province`]
    .filter(Boolean).join(', ');
}

function haystack(f) {
  const l = f.locality;
  const g = FOSSIL_GROUPS[f.group] || {};
  return [f.taxon, f.stage, f.formation_en, f.formation_th, g.th, g.en, l.name_en, l.name_th, l.tambon_th, l.amphoe_th,
    l.province_th, l.province_en, localityText(l, 'th'), localityText(l, 'en')].filter(Boolean).join(' ').toLowerCase();
}

export function filterFossils(list, { q = '', period = '', province = '', group = '' } = {}, periods = []) {
  const p = periods.find(x => x.id === period);
  const needle = q.trim().toLowerCase();
  return list
    .filter(f => !needle || haystack(f).includes(needle))
    .filter(f => !p || (f.age_top_ma < p.start_ma && f.age_base_ma > p.end_ma))
    .filter(f => !province || f.locality.province_en === province || f.locality.province_th === province)
    .filter(f => !group || f.group === group)
    .sort((a, b) => b.age_base_ma - a.age_base_ma);
}

export function fossilAgeText(f, lang) {
  return `${f.age_top_ma}–${f.age_base_ma} ${lang === 'th' ? 'ล้านปีก่อน' : 'Ma'}`;
}

export function fossilCardHtml(f) {
  const lang = getLang();
  const th = lang === 'th';
  const g = FOSSIL_GROUPS[f.group] || FOSSIL_GROUPS.other;
  const l = f.locality;
  const badge = f.verified ? '' : `<span class="badge">${esc(t('draft'))}</span>`;
  const formation = [th ? f.formation_th : f.formation_en, th ? f.formation_en : f.formation_th].filter(Boolean)[0];
  const precision = t(`precision_${l.precision}`);
  return `<div class="card-head"><span class="card-age">${esc(fossilAgeText(f, lang))} · ${esc(f.stage)}</span>${badge}`
    + `<button type="button" class="card-close" aria-label="${esc(t('close'))}">×</button></div>`
    + `<h2><span aria-hidden="true">${g.icon}</span> <em>${esc(f.taxon)}</em></h2>`
    + `<p class="card-unit">${esc(th ? g.th : g.en)}${formation ? ` · ${esc(formation)}` : ''}</p>`
    + `<p>${esc(th ? f.significance_th : f.significance_en)}</p>`
    + `<p><strong>${esc(t('fossil_locality'))}:</strong> ${esc(localityText(l, lang))}</p>`
    + `<p><a href="https://www.google.com/maps?q=${esc(l.lat)},${esc(l.lon)}" target="_blank" rel="noopener">${esc(l.lat)}, ${esc(l.lon)}</a> <span class="card-cite">(${esc(precision)})</span></p>`
    + `<p class="card-cite"><strong>${esc(t('source'))}:</strong> <a href="${esc(f.citation.url)}" target="_blank" rel="noopener">${esc(f.citation.text)}</a></p>`;
}

// "Wernette S.J., Hughes N.C., … 2020, Title…" → "Wernette et al. 2020" for compact table cells.
export function shortCitation(text) {
  const m = text.match(/\b(1[89]\d{2}|20\d{2})\b/);
  if (!m) return text;
  const authors = text.slice(0, m.index).trim().replace(/,$/, '');
  const surname = s => s.trim().split(/\s+/)[0].replace(/,$/, '');
  const parts = authors.split(/\s*&\s*|\s+and\s+/);
  if (parts.length === 2 && !parts[0].includes(',')) return `${surname(parts[0])} & ${surname(parts[1])} ${m[0]}`;
  const many = authors.includes(',') || authors.includes('&') || /\bet al\b/.test(authors);
  return `${surname(authors)}${many ? ' et al.' : ''} ${m[0]}`;
}
