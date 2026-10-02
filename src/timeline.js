import { layoutTimeline } from './layout.js';
import { activeIndex, scrollPads } from './select.js';
import { t, field, getLang } from './i18n.js';
import { formatAge, esc } from './format.js';
import { polarityRects, polarityLabel, polarityAt } from './polarity.js';
import { placeFossils, FOSSIL_GROUPS } from './fossils.js';
import { ageToY } from './layout.js';

const ROW_H = 64;
const MIN_PERIOD_H = 140;

export function createTimeline(container, events, periods, { onActive, onSelect, onPolarity, onFossil, fossils = [], polarity = null, showPolarity = false }) {
  const layout = layoutTimeline(events, periods, { rowH: ROW_H, minPeriodH: MIN_PERIOD_H });
  const inner = document.createElement('div');
  inner.className = 'tl-inner';
  container.appendChild(inner);
  let pad = 0;
  let padBottom = 0;
  let active = -1;
  let rowEls = [];
  let polarityOn = showPolarity && !!polarity;
  let jumping = false;
  let polRects = [];
  let placedFossils = [];
  let jumpTimer = null;

  function rowHtml(e) {
    if (e.lane === 'life') {
      return `<span class="tl-icon" aria-hidden="true">${esc(e.icon)}</span><span class="sr">${esc(field(e, 'title'))}</span>`;
    }
    const badge = e.verified ? '' : ` <span class="badge">${esc(t('draft'))}</span>`;
    return `<span class="tl-age">${esc(formatAge(e.age_ma, null, getLang()))}${badge}</span><span class="tl-title">${esc(field(e, 'title'))}</span>`;
  }

  function render() {
    ({ top: pad, bottom: padBottom } = scrollPads(container.clientHeight));
    const keepId = active >= 0 ? layout.rows[active].event.id : null;
    inner.innerHTML = '';
    polRects = [];
    inner.style.height = `${layout.height + pad + padBottom}px`;
    for (const b of layout.bands) {
      const el = document.createElement('div');
      el.className = 'tl-band';
      el.style.top = `${pad + b.y}px`;
      el.style.height = `${b.h - 4}px`;
      el.style.background = b.period.color;
      el.innerHTML = `<span>${esc(field(b.period, 'name').replace(/^ยุค/, ''))}</span>`;
      inner.appendChild(el);
      if (polarityOn) {
        for (const r of polarityRects(b.period, { y: pad + b.y, h: b.h - 4 }, polarity.segments)) {
          const s = document.createElement('div');
          s.className = `tl-pol pol-${r.polarity}`;
          s.style.top = `${r.y}px`;
          s.style.height = `${r.h}px`;
          s.title = polarityLabel(r.seg, getLang());
          s.dataset.pol = String(polRects.length);
          inner.appendChild(s);
          polRects.push(r);
        }
      }
    }
    inner.classList.toggle('with-pol', polarityOn);
    const columns = matchMedia('(max-width: 767px)').matches ? 1 : 2; // same breakpoint as --fossil-col
    const bandsPx = layout.bands.map(b => ({ period: b.period, y: pad + b.y, h: b.h - 4 }));
    placedFossils = placeFossils(bandsPx, fossils, { size: 18, columns });
    placedFossils.forEach((p, idx) => {
      const f = p.fossil;
      const g = FOSSIL_GROUPS[f.group] || FOSSIL_GROUPS.other;
      const el = document.createElement('button');
      el.type = 'button';
      el.className = `tl-fossil${f.locality.province_en === 'Kanchanaburi' ? ' is-kan' : ''}`;
      el.style.top = `${p.y}px`;
      el.style.left = `calc(100% - var(--fossil-col) + ${p.x}px)`;
      el.title = `${f.taxon} · ${f.locality.province_th}`;
      el.setAttribute('aria-label', el.title);
      el.textContent = g.icon;
      el.dataset.fossil = String(idx);
      inner.appendChild(el);
    });
    rowEls = layout.rows.map((r, idx) => {
      const el = document.createElement('button');
      el.type = 'button';
      el.className = `tl-row lane-${r.event.lane}`;
      el.style.top = `${pad + r.y + 2}px`;
      el.style.height = `${ROW_H - 4}px`;
      el.title = field(r.event, 'title');
      el.innerHTML = rowHtml(r.event);
      el.dataset.row = String(idx);
      inner.appendChild(el);
      return el;
    });
    active = -1;
    update(keepId);
  }

  // keepId: after a re-render, re-highlight the same event without telling the page it changed
  // (so toggling polarity, switching language or resizing keeps an open card open).
  function update(keepId = null) {
    const i = activeIndex(layout.rows, container.scrollTop, ROW_H);
    if (i < 0 || i === active) return;
    if (rowEls[active]) rowEls[active].classList.remove('is-active');
    rowEls[i].classList.add('is-active');
    active = i;
    if (!jumping && layout.rows[i].event.id !== keepId) onActive(layout.rows[i].event);
  }

  // One listener for every row, fossil icon and polarity strip.
  inner.addEventListener('click', ev => {
    const row = ev.target.closest('[data-row]');
    if (row) { onSelect(layout.rows[Number(row.dataset.row)].event); return; }
    const fos = ev.target.closest('[data-fossil]');
    if (fos) { if (onFossil) onFossil(placedFossils[Number(fos.dataset.fossil)].fossil); return; }
    if (!polarityOn || !onPolarity) return;
    const strip = ev.target.closest('[data-pol]');
    if (strip && ev.detail === 0) { onPolarity(polRects[Number(strip.dataset.pol)].seg); return; } // keyboard/scripted click
    const box = inner.getBoundingClientRect();
    const x = ev.clientX - box.left;
    const bandW = parseFloat(getComputedStyle(inner).getPropertyValue('--band-w')) || 72;
    if (x < bandW - 16 || x > bandW + 4) return;
    const hit = polarityAt(polRects, ev.clientY - box.top);
    if (hit) onPolarity(hit.seg);
  });

  let ticking = false;
  container.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { ticking = false; update(); });
  }, { passive: true });

  function scrollToEvent(id) {
    const r = layout.rows.find(row => row.event.id === id);
    if (!r) return;
    const smooth = !matchMedia('(prefers-reduced-motion: reduce)').matches;
    // While a jump scrolls past other rows, only the destination reaches onActive,
    // so the globe does not flicker through every slice in between.
    jumping = true;
    clearTimeout(jumpTimer);
    const finish = () => {
      if (!jumping) return;
      jumping = false;
      clearTimeout(jumpTimer);
      container.removeEventListener('scrollend', finish);
      active = -1;
      update();
    };
    container.addEventListener('scrollend', finish);
    jumpTimer = setTimeout(finish, smooth ? 900 : 50);
    container.scrollTo({ top: r.y + ROW_H / 2, behavior: smooth ? 'smooth' : 'auto' });
  }

  function scrollToAge(age) {
    const y = ageToY(age, layout.bands);
    if (y !== null) container.scrollTo({ top: y, behavior: 'auto' });
  }

  function setPolarity(on) {
    polarityOn = on && !!polarity;
    render();
  }

  render();
  return { scrollToEvent, scrollToAge, refresh: render, setPolarity };
}
