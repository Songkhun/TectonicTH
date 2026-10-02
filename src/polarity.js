// Geomagnetic polarity strip: segments mapped linearly in age inside each period band.

const POLARITY_WORDS = {
  th: { normal: 'ปกติ', reversed: 'กลับ', mixed: 'สลับบ่อย/ไม่ทราบแน่ชัด' },
  en: { normal: 'normal', reversed: 'reversed', mixed: 'frequent reversals / poorly known' },
};

export function polarityRects(period, band, segments, minH = 1) {
  const span = period.start_ma - period.end_ma;
  const rects = [];
  for (const seg of segments) {
    if (seg.base_ma <= period.end_ma || seg.top_ma >= period.start_ma) continue;
    const top = Math.max(seg.top_ma, period.end_ma);
    const base = Math.min(seg.base_ma, period.start_ma);
    const y = band.y + ((period.start_ma - base) / span) * band.h;
    const h = Math.max(minH, ((base - top) / span) * band.h);
    rects.push({ y, h, polarity: seg.polarity, seg });
  }
  return rects;
}

export function polarityLabel(seg, lang) {
  const th = lang === 'th';
  const approx = seg.approx ? '≈' : '';
  const note = seg.approx ? (th ? ' (โดยประมาณ)' : ' (approximate)') : '';
  const ages = `${approx}${seg.top_ma}–${seg.base_ma} ${th ? 'ล้านปีก่อน' : 'Ma'}${note}`;
  return `${seg.name} · ${ages} · ${POLARITY_WORDS[th ? 'th' : 'en'][seg.polarity]}`;
}

// The chron at a tapped y: the rect containing it, else the nearest within `reach` px (thin chrons).
export function polarityAt(rects, y, reach = 4) {
  let best = null;
  let bestDist = Infinity;
  for (const r of rects) {
    const d = y < r.y ? r.y - y : y > r.y + r.h ? y - (r.y + r.h) : 0;
    if (d < bestDist || (d === 0 && bestDist === 0 && r.h < best.h)) { best = r; bestDist = d; }
  }
  return bestDist <= reach ? best : null;
}
