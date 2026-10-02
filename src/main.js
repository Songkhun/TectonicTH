import { t, initLang, getLang, setLang, onLangChange } from './i18n.js';
import { formatLat, formatSliceAge, esc } from './format.js';
import { createGlobe } from './globe.js';
import { createTimeline } from './timeline.js';
import { createCard } from './card.js';
import { nearestStopIndex, lectureKeyAction } from './select.js';
import { polarityLabel } from './polarity.js';
import { FOSSIL_GROUPS, filterFossils, localityText, fossilAgeText, fossilMidAge, shortCitation } from './fossils.js';
import { evidenceHtml } from './evidence.js';

function start() {
  const data = JSON.parse(document.getElementById('dt-data').textContent);
  let storage = null;
  try { storage = window.localStorage; } catch (_) { storage = null; }
  initLang(storage);

  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const globeEl = document.getElementById('globe');
  const globe = createGlobe(globeEl, data.slices, { reducedMotion });
  const readout = document.getElementById('readout');
  const lectureBtn = document.getElementById('btn-lecture');
  const stops = data.events.filter(e => e.lecture_stop).sort((a, b) => b.age_ma - a.age_ma);
  let stopIndex = -1;
  let lecture = false;
  let lastInfo = null;
  let keepCardOnce = false; // a jump from the fossil table must not close the card it just opened

  function showReadout(info) {
    lastInfo = info;
    const approx = info.exact ? '' : ` · ${t('approx_slice')}`;
    readout.textContent = `${t('paleo_label')} ${formatLat(info.lonlat[1])} · ${formatSliceAge(info.age, getLang())}${approx}`;
  }

  const evidence = data.evidence || [];
  const card = createCard(document.getElementById('card'), {
    onPrev: () => goStop(stopIndex - 1),
    onNext: () => goStop(stopIndex + 1),
    extraHtml: e => evidenceHtml(e.id, evidence),
  });

  const polarityBox = document.getElementById('chk-polarity');
  const poltip = document.getElementById('poltip');
  let showPolarity = true;
  try { showPolarity = storage ? storage.getItem('dt-polarity') !== '0' : true; } catch (_) { showPolarity = true; }
  if (!data.polarity) polarityBox.closest('label').hidden = true;
  polarityBox.checked = showPolarity;
  let tipTimer = null;
  const showPolarityTip = seg => {
    poltip.textContent = polarityLabel(seg, getLang());
    poltip.hidden = false;
    clearTimeout(tipTimer);
    tipTimer = setTimeout(() => { poltip.hidden = true; }, 4000);
  };
  const timeline = createTimeline(document.getElementById('timeline'), data.events, data.periods, {
    polarity: data.polarity,
    fossils: data.fossils || [],
    onFossil: f => card.showFossil(f),
    showPolarity,
    onPolarity: showPolarityTip,
    onActive: e => {
      showReadout(globe.showSlice(e.paleo_age));
      if (!lecture) {
        if (keepCardOnce) keepCardOnce = false;
        else card.hide();
      }
      else if (stops[stopIndex] !== e) stopIndex = nearestStopIndex(stops, e);
    },
    onSelect: e => card.show(e),
  });

  function goStop(i) {
    if (!stops.length) return;
    stopIndex = Math.max(0, Math.min(stops.length - 1, i));
    const e = stops[stopIndex];
    timeline.scrollToEvent(e.id);
    card.show(e);
  }

  function setLecture(on) {
    lecture = on;
    document.body.classList.toggle('lecture', on);
    lectureBtn.setAttribute('aria-pressed', String(on));
    card.lectureMode(on);
    requestAnimationFrame(() => { globe.resize(); timeline.refresh(); if (on) goStop(stopIndex < 0 ? 0 : stopIndex); });
  }

  function renderAbout() {
    const seen = new Set();
    const cites = [...data.events, ...evidence]
      .filter(e => e.citation && !seen.has(e.citation.text) && seen.add(e.citation.text))
      .map(e => `<li><a href="${esc(e.citation.url)}" target="_blank" rel="noopener">${esc(e.citation.text)}</a></li>`)
      .join('');
    document.getElementById('about-body').innerHTML =
      `<h2>${esc(t('about_title'))}</h2><p>${esc(t('about_intro'))}</p>` +
      `<ul><li>${esc(t('credit_model'))}</li><li>${esc(t('credit_timescale'))}</li><li>${esc(t('credit_inspiration'))}</li></ul>` +
      (data.polarity
        ? `<h3>${esc(t('polarity_heading'))}</h3><p>${esc(t('polarity_legend'))}</p><ul>`
          + Object.values(data.polarity.sources).map(s => `<li><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.text)}</a></li>`).join('')
          + '</ul>'
        : '') +
      `<h3>${esc(t('citations_heading'))}</h3><ol>${cites}</ol>`;
  }

  function applyStaticText() {
    document.documentElement.lang = getLang();
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    globeEl.setAttribute('aria-label', t('globe_label'));
    polarityBox.setAttribute('aria-label', t('polarity_toggle'));
    polarityBox.closest('label').title = t('polarity_toggle');
  }

  polarityBox.addEventListener('change', () => {
    try { if (storage) storage.setItem('dt-polarity', polarityBox.checked ? '1' : '0'); } catch (_) { /* storage blocked */ }
    timeline.setPolarity(polarityBox.checked);
  });
  const fossils = data.fossils || [];
  const fosDialog = document.getElementById('fossils');
  const fosQ = document.getElementById('fos-q');
  const fosPeriod = document.getElementById('fos-period');
  const fosProvince = document.getElementById('fos-province');
  const fosGroup = document.getElementById('fos-group');
  const fosRows = document.getElementById('fos-rows');
  if (!fossils.length) document.getElementById('btn-fossils').hidden = true;

  function fillSelect(sel, firstLabel, options) {
    const keep = sel.value;
    sel.innerHTML = `<option value="">${esc(firstLabel)}</option>` + options.map(([v, label]) => `<option value="${esc(v)}">${esc(label)}</option>`).join('');
    sel.value = keep;
  }

  function renderFossilFilters() {
    const th = getLang() === 'th';
    fosQ.placeholder = t('fossils_search');
    fillSelect(fosPeriod, t('fossils_all_periods'), data.periods.map(p => [p.id, th ? p.name_th : p.name_en]));
    const provinces = [...new Map(fossils.map(f => [f.locality.province_en, f.locality])).values()]
      .sort((a, b) => a.province_en.localeCompare(b.province_en));
    fillSelect(fosProvince, t('fossils_all_provinces'), provinces.map(l => [l.province_en, th ? l.province_th : l.province_en]));
    const groups = [...new Set(fossils.map(f => f.group))];
    fillSelect(fosGroup, t('fossils_all_groups'), groups.map(g => [g, `${FOSSIL_GROUPS[g].icon} ${th ? FOSSIL_GROUPS[g].th : FOSSIL_GROUPS[g].en}`]));
  }

  function renderFossilRows() {
    const lang = getLang();
    const list = filterFossils(fossils, { q: fosQ.value, period: fosPeriod.value, province: fosProvince.value, group: fosGroup.value }, data.periods);
    document.getElementById('fos-count').textContent = `${list.length} ${t('fossils_count')}`;
    fosRows.innerHTML = list.map(f => {
      const g = FOSSIL_GROUPS[f.group];
      const l = f.locality;
      const formation = (lang === 'th' ? f.formation_th : f.formation_en) || f.formation_en || f.formation_th || '';
      return `<tr data-id="${esc(f.id)}"${l.province_en === 'Kanchanaburi' ? ' class="is-kan"' : ''}>`
        + `<td><em>${esc(f.taxon)}</em>${f.verified ? '' : ` <span class="badge">${esc(t('draft'))}</span>`}</td>`
        + `<td>${g.icon} ${esc(lang === 'th' ? g.th : g.en)}</td>`
        + `<td><span class="num">${esc(fossilAgeText(f, lang))}</span><br><span class="muted">${esc(f.stage)}</span></td>`
        + `<td>${esc(formation)}</td><td>${esc(localityText(l, lang))}</td>`
        + `<td><a class="num" href="https://www.google.com/maps?q=${esc(l.lat)},${esc(l.lon)}" target="_blank" rel="noopener">${esc(l.lat)}, ${esc(l.lon)}</a><br><span class="muted">${esc(t(`precision_${l.precision}`))}</span></td>`
        + `<td><a href="${esc(f.citation.url)}" target="_blank" rel="noopener" title="${esc(f.citation.text)}">${esc(shortCitation(f.citation.text))}</a></td></tr>`;
    }).join('');
  }

  fosRows.addEventListener('click', ev => {
    if (ev.target.closest('a')) return;
    const row = ev.target.closest('tr[data-id]');
    if (!row) return;
    const f = fossils.find(x => x.id === row.dataset.id);
    fosDialog.close();
    keepCardOnce = true;
    setTimeout(() => { keepCardOnce = false; }, 1500);
    timeline.scrollToAge(fossilMidAge(f));
    card.showFossil(f);
  });
  [fosQ, fosPeriod, fosProvince, fosGroup].forEach(c => c.addEventListener('input', renderFossilRows));
  document.getElementById('btn-fossils').addEventListener('click', () => {
    renderFossilFilters();
    renderFossilRows();
    fosDialog.showModal();
  });
  lectureBtn.addEventListener('click', () => setLecture(!lecture));
  document.getElementById('btn-lang').addEventListener('click', () => setLang(getLang() === 'th' ? 'en' : 'th'));
  document.getElementById('btn-about').addEventListener('click', () => document.getElementById('about').showModal());
  document.addEventListener('keydown', ev => {
    if (!lecture) return;
    const action = lectureKeyAction(ev.key, ev.target && ev.target.tagName, document.getElementById('about').open || fosDialog.open);
    if (action === 'next') { ev.preventDefault(); goStop(stopIndex + 1); }
    if (action === 'prev') { ev.preventDefault(); goStop(stopIndex - 1); }
    if (action === 'exit') setLecture(false);
  });
  onLangChange(() => {
    applyStaticText();
    renderAbout();
    if (fosDialog.open) { renderFossilFilters(); renderFossilRows(); }
    timeline.refresh();
    card.refresh();
    if (lastInfo) showReadout(lastInfo);
  });
  let resizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => { globe.resize(); timeline.refresh(); }, 120);
  });

  applyStaticText();
  renderAbout();
  globe.resize();
  timeline.refresh();
}

start();
