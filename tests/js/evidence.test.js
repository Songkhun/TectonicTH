import test from 'node:test';
import assert from 'node:assert/strict';
import { initLang, setLang, I18N_STRINGS } from '../../src/i18n.js';
import { EVIDENCE_METHODS, evidenceFor, formatPaleolatCompare, evidenceHtml } from '../../src/evidence.js';

const items = [
  { id: 'a', event_ids: ['x'], method: 'paleomagnetism', title_th: 'ขั้วแม่เหล็ก', title_en: 'Pole', finding_th: 'ผล', finding_en: 'Result',
    value: '32 ± 6°S', paleolat: { deg: -32, err: 6 }, site: null, citation: { text: 'S 2020', url: 'https://doi.org/10.1/x' }, source_type: 'peer-reviewed', verified: false },
  { id: 'b', event_ids: ['y', 'x'], method: 'seismic', title_th: 'สำรวจ <b>', title_en: 'Survey <b>', finding_th: 'พบ & "ชั้น"', finding_en: 'Found & "layer"',
    value: null, paleolat: null, site: { name_th: 'ไทรโยค', name_en: 'Sai Yok', lat: 14.4, lon: 98.85 }, citation: { text: 'T 2010', url: 'https://doi.org/10.2/y' }, source_type: 'peer-reviewed', verified: true },
];

test('evidenceFor filters by event and keeps file order', () => {
  assert.deepEqual(evidenceFor('x', items).map(i => i.id), ['a', 'b']);
  assert.deepEqual(evidenceFor('y', items).map(i => i.id), ['b']);
  assert.deepEqual(evidenceFor('z', items), []);
});

test('paleolatitude comparison shows hemisphere for measured and model', () => {
  assert.equal(formatPaleolatCompare({ deg: -32, err: 6 }, -35.6, 'th'), 'วัดได้ 32 ± 6°S · แบบจำลอง ≈36°S');
  assert.equal(formatPaleolatCompare({ deg: 12.5, err: 3 }, 6.6, 'en'), 'measured 12.5 ± 3°N · model ≈7°N');
  assert.equal(formatPaleolatCompare({ deg: -32, err: 6 }, null, 'en'), 'measured 32 ± 6°S');
});

test('evidenceHtml is empty for an event without evidence', () => {
  initLang(null);
  assert.equal(evidenceHtml('z', items, null), '');
});

test('evidenceHtml escapes text and includes heading, chips, comparison and links', () => {
  initLang(null);
  setLang('en');
  const html = evidenceHtml('x', items, -35.6);
  assert.ok(html.includes('How do we know?'));
  assert.ok(html.includes('Survey &lt;b&gt;') && !html.includes('Survey <b>'));
  assert.ok(html.includes('Found &amp; &quot;layer&quot;'));
  assert.ok(html.includes('measured 32 ± 6°S · model ≈36°S'));
  assert.ok(html.includes('ev-paleomagnetism') && html.includes('ev-seismic'));
  assert.ok(html.includes('https://www.google.com/maps?q=14.4,98.85'));
  assert.ok(html.includes('https://doi.org/10.1/x'));
  setLang('th');
});

test('every method has a label in both languages', () => {
  for (const m of EVIDENCE_METHODS) {
    assert.ok(I18N_STRINGS.th[`method_${m}`], m);
    assert.ok(I18N_STRINGS.en[`method_${m}`], m);
  }
});

test('paleolatitude without a stated error omits the ±', () => {
  assert.equal(formatPaleolatCompare({ deg: -13, err: null }, -17.2, 'en'), 'measured 13°S · model ≈17°S');
});
