import { t, initLang, getLang, setLang, onLangChange } from './i18n.js';
import { formatLat, formatSliceAge, esc } from './format.js';
import { createGlobe } from './globe.js';
import { createTimeline } from './timeline.js';
import { createCard } from './card.js';
import { nearestStopIndex, lectureKeyAction } from './select.js';
import { polarityLabel } from './polarity.js';
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
    showPolarity,
    onPolarity: showPolarityTip,
    onActive: e => {
      showReadout(globe.showSlice(e.paleo_age));
      if (!lecture) card.hide();
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
  lectureBtn.addEventListener('click', () => setLecture(!lecture));
  document.getElementById('btn-lang').addEventListener('click', () => setLang(getLang() === 'th' ? 'en' : 'th'));
  document.getElementById('btn-about').addEventListener('click', () => document.getElementById('about').showModal());
  document.addEventListener('keydown', ev => {
    if (!lecture) return;
    const action = lectureKeyAction(ev.key, ev.target && ev.target.tagName, document.getElementById('about').open);
    if (action === 'next') { ev.preventDefault(); goStop(stopIndex + 1); }
    if (action === 'prev') { ev.preventDefault(); goStop(stopIndex - 1); }
    if (action === 'exit') setLecture(false);
  });
  onLangChange(() => {
    applyStaticText();
    renderAbout();
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
