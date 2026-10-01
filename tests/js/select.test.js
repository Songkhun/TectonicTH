import test from 'node:test';
import assert from 'node:assert/strict';
import { activeIndex, nearestSlice } from '../../src/select.js';

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
