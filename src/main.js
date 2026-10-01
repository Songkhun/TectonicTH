import { t, initLang, getLang, setLang, onLangChange } from './i18n.js';
import { formatLat, formatSliceAge, esc } from './format.js';
import { createGlobe } from './globe.js';
import { createTimeline } from './timeline.js';
import { createCard } from './card.js';

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

  const card = createCard(document.getElementById('card'), {
    onPrev: () => goStop(stopIndex - 1),
    onNext: () => goStop(stopIndex + 1),
  });

  const timeline = createTimeline(document.getElementById('timeline'), data.events, data.periods, {
    onActive: e => showReadout(globe.showSlice(e.paleo_age)),
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
    const cites = data.events
      .filter(e => e.citation && !seen.has(e.citation.text) && seen.add(e.citation.text))
      .map(e => `<li><a href="${esc(e.citation.url)}" target="_blank" rel="noopener">${esc(e.citation.text)}</a></li>`)
      .join('');
    document.getElementById('about-body').innerHTML =
      `<h2>${esc(t('about_title'))}</h2><p>${esc(t('about_intro'))}</p>` +
      `<ul><li>${esc(t('credit_model'))}</li><li>${esc(t('credit_timescale'))}</li><li>${esc(t('credit_inspiration'))}</li></ul>` +
      `<h3>${esc(t('citations_heading'))}</h3><ol>${cites}</ol>`;
  }

  function applyStaticText() {
    document.documentElement.lang = getLang();
    document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = t(el.dataset.i18n); });
    globeEl.setAttribute('aria-label', t('globe_label'));
  }

  lectureBtn.addEventListener('click', () => setLecture(!lecture));
  document.getElementById('btn-lang').addEventListener('click', () => setLang(getLang() === 'th' ? 'en' : 'th'));
  document.getElementById('btn-about').addEventListener('click', () => document.getElementById('about').showModal());
  document.addEventListener('keydown', ev => {
    if (!lecture) return;
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(ev.key)) { ev.preventDefault(); goStop(stopIndex + 1); }
    if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(ev.key)) { ev.preventDefault(); goStop(stopIndex - 1); }
    if (ev.key === 'Escape') setLecture(false);
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
