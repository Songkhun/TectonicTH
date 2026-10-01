import test from 'node:test';
import assert from 'node:assert/strict';
import { activeIndex, nearestSlice, scrollPads, frameDue } from '../../src/select.js';

const rows = [{ y: 0 }, { y: 50 }, { y: 100 }];

test('activeIndex picks the row whose centre is nearest', () => {
  assert.equal(activeIndex(rows, 74, 50), 1);
  assert.equal(activeIndex(rows, 126, 50), 2);
});

test('activeIndex clamps at the extremes', () => {
  assert.equal(activeIndex(rows, -500, 50), 0);
  assert.equal(activeIndex(rows, 99999, 50), 2);
  assert.equal(activeIndex([], 10, 50), -1);
});

test('nearestSlice exact and approximate', () => {
  const ages = [0, 5, 20, 270, 290];
  assert.deepEqual(nearestSlice(270, ages), { age: 270, exact: true });
  assert.deepEqual(nearestSlice(275, ages), { age: 270, exact: false });
  assert.deepEqual(nearestSlice(0.004, ages), { age: 0, exact: false });
  assert.throws(() => nearestSlice(10, []));
});

test('scrollPads put the active line in the top quarter, clear of the card', () => {
  assert.deepEqual(scrollPads(800), { top: 200, bottom: 600 });
  assert.deepEqual(scrollPads(0), { top: 0, bottom: 0 });
});

test('frameDue throttles idle pulse redraws but never an animation', () => {
  assert.equal(frameDue(1000, 990, false), false);
  assert.equal(frameDue(1100, 990, false), true);
  assert.equal(frameDue(1000, 999, true), true);
});
