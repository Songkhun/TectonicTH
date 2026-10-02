import { layoutTimeline } from './layout.js';
import { activeIndex, scrollPads } from './select.js';
import { t, field, getLang } from './i18n.js';
import { formatAge, esc } from './format.js';
import { polarityRects, polarityLabel } from './polarity.js';

const ROW_H = 64;
const MIN_PERIOD_H = 140;

export function createTimeline(container, events, periods, { onActive, onSelect, onPolarity, polarity = null, showPolarity = false }) {
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
    inner.innerHTML = '';
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
          s.addEventListener('click', () => onPolarity && onPolarity(r.seg));
          inner.appendChild(s);
        }
      }
    }
    inner.classList.toggle('with-pol', polarityOn);
    rowEls = layout.rows.map(r => {
      const el = document.createElement('button');
      el.type = 'button';
      el.className = `tl-row lane-${r.event.lane}`;
      el.style.top = `${pad + r.y + 2}px`;
      el.style.height = `${ROW_H - 4}px`;
      el.title = field(r.event, 'title');
      el.innerHTML = rowHtml(r.event);
      el.addEventListener('click', () => onSelect(r.event));
      inner.appendChild(el);
      return el;
    });
    active = -1;
    update();
  }

  function update() {
    const i = activeIndex(layout.rows, container.scrollTop, ROW_H);
    if (i < 0 || i === active) return;
    if (rowEls[active]) rowEls[active].classList.remove('is-active');
    rowEls[i].classList.add('is-active');
    active = i;
    if (!jumping) onActive(layout.rows[i].event);
  }

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

  function setPolarity(on) {
    polarityOn = on && !!polarity;
    render();
  }

  render();
  return { scrollToEvent, refresh: render, setPolarity };
}
