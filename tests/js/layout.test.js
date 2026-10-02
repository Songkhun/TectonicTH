import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { periodOf, layoutTimeline } from '../../src/layout.js';

const periods = JSON.parse(readFileSync(new URL('../../content/timescale.json', import.meta.url), 'utf8'));
const ev = (id, age) => ({ id, age_ma: age });

test('periodOf boundaries: base age belongs to the older period', () => {
  assert.equal(periodOf(251.94, periods).id, 'permian');
  assert.equal(periodOf(251.902, periods).id, 'permian');
  assert.equal(periodOf(251.9, periods).id, 'triassic');
  assert.equal(periodOf(0, periods).id, 'quaternary');
  assert.equal(periodOf(500, periods).id, 'cambrian');
  assert.equal(periodOf(600, periods), null);
});

test('layout orders oldest first and never overlaps', () => {
  const events = [ev('b', 270), ev('a', 470), ev('c', 0.004), ev('d', 0), ev('e', 280)];
  const { rows, bands, height } = layoutTimeline(events, periods, { rowH: 50, minPeriodH: 120 });
  assert.deepEqual(rows.map(r => r.event.id), ['a', 'e', 'b', 'c', 'd']);
  for (let i = 1; i < rows.length; i++) assert.ok(rows[i].y >= rows[i - 1].y + 50);
  assert.equal(bands.length, periods.length);
  assert.ok(bands.every(b => b.h >= 120));
  assert.equal(height, bands.reduce((s, b) => s + b.h, 0));
});

test('busy period grows beyond the minimum', () => {
  const events = [ev('p1', 290), ev('p2', 280), ev('p3', 270)];
  const { bands } = layoutTimeline(events, periods, { rowH: 50, minPeriodH: 120 });
  assert.equal(bands.find(b => b.period.id === 'permian').h, 150);
});

test('event outside the time scale throws with its id', () => {
  assert.throws(() => layoutTimeline([ev('too-old', 600)], periods), /too-old/);
});
