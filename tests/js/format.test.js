import test from 'node:test';
import assert from 'node:assert/strict';
import { formatAge, formatLat, esc } from '../../src/format.js';

test('deep time ages in Ma', () => {
  assert.equal(formatAge(270, 15, 'en'), '270 ± 15 Ma');
  assert.equal(formatAge(270, 15, 'th'), '270 ± 15 ล้านปีก่อน');
  assert.equal(formatAge(251.94, null, 'en'), '251.9 Ma');
});

test('prehistoric ages in years ago', () => {
  assert.equal(formatAge(0.004, null, 'en'), '≈4,000 years ago');
  assert.equal(formatAge(0.004, null, 'th'), '≈4,000 ปีก่อน');
});

test('historic ages as calendar years', () => {
  assert.equal(formatAge(0.000083, null, 'en', 2026), '1943 CE');
  assert.equal(formatAge(0.000083, null, 'th', 2026), 'พ.ศ. 2486 (ค.ศ. 1943)');
});

test('present', () => {
  assert.equal(formatAge(0, null, 'en'), 'Present');
  assert.equal(formatAge(0, null, 'th'), 'ปัจจุบัน');
});

test('latitude readout', () => {
  assert.equal(formatLat(-37.45), '≈37°S');
  assert.equal(formatLat(14.02), '≈14°N');
});

test('esc neutralises HTML', () => {
  assert.equal(esc('<script>"a" & \'b\'</script>'), '&lt;script&gt;&quot;a&quot; &amp; &#39;b&#39;&lt;/script&gt;');
  assert.equal(esc(null), '');
});
