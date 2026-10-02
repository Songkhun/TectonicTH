import test from 'node:test';
import assert from 'node:assert/strict';
import { polarityRects, polarityLabel } from '../../src/polarity.js';

const period = { id: 'quaternary', start_ma: 2.58, end_ma: 0 };
const band = { y: 100, h: 258 };
const segs = [
  { top_ma: 0, base_ma: 0.773, polarity: 'normal', name: 'C1n', source: 'gts2020', approx: false },
  { top_ma: 0.773, base_ma: 0.99, polarity: 'reversed', name: 'C1r', source: 'gts2020', approx: false },
  { top_ma: 0.99, base_ma: 0.99001, polarity: 'normal', name: 'C1r', source: 'gts2020', approx: false },
  { top_ma: 0.99001, base_ma: 3.0, polarity: 'reversed', name: 'C2r', source: 'gts2020', approx: false },
  { top_ma: 3.0, base_ma: 5.0, polarity: 'normal', name: 'C3n', source: 'gts2020', approx: false },
];

test('rects map age linearly inside the band, oldest at the top', () => {
  const r = polarityRects(period, band, segs);
  const youngest = r.find(x => x.seg.name === 'C1n');
  assert.equal(Math.round(youngest.y + youngest.h), 358);
  assert.equal(Math.round(youngest.h), 77);
});

test('segments are clipped to the period and outside ones dropped', () => {
  const r = polarityRects(period, band, segs);
  assert.ok(!r.some(x => x.seg.name === 'C3n'));
  const clipped = r.find(x => x.seg.name === 'C2r');
  assert.equal(clipped.y, 100);
});

test('very thin chrons still get at least 1 px', () => {
  const r = polarityRects(period, band, segs);
  assert.ok(r.every(x => x.h >= 1));
});

test('labels name the chron, ages and polarity in both languages', () => {
  assert.equal(polarityLabel(segs[0], 'th'), 'C1n · 0–0.773 ล้านปีก่อน · ปกติ');
  assert.equal(polarityLabel(segs[1], 'en'), 'C1r · 0.773–0.99 Ma · reversed');
  assert.equal(polarityLabel({ top_ma: 462, base_ma: 482, polarity: 'reversed', name: 'Moyero Reverse Superchron', approx: true }, 'en'),
    'Moyero Reverse Superchron · ≈462–482 Ma (approximate) · reversed');
  assert.equal(polarityLabel({ top_ma: 121.4, base_ma: 265, polarity: 'mixed', name: 'Frequent reversals', approx: false }, 'th'),
    'Frequent reversals · 121.4–265 ล้านปีก่อน · สลับบ่อย/ไม่ทราบแน่ชัด');
});

test('polarityAt finds the chron under a tap, or the nearest thin one within reach', async () => {
  const { polarityAt } = await import('../../src/polarity.js');
  const rects = [{ y: 100, h: 50, seg: { name: 'A' } }, { y: 150, h: 0.6, seg: { name: 'thin' } }, { y: 150.6, h: 40, seg: { name: 'B' } }];
  assert.equal(polarityAt(rects, 120).seg.name, 'A');
  assert.equal(polarityAt(rects, 170).seg.name, 'B');
  assert.equal(polarityAt(rects, 150.3).seg.name, 'thin');
  assert.equal(polarityAt(rects, 400, 4), null);
});
