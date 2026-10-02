import test from 'node:test';
import assert from 'node:assert/strict';
import { initLang, setLang } from '../../src/i18n.js';
import { FOSSIL_GROUPS, fossilMidAge, placeFossils, localityText, filterFossils, fossilCardHtml } from '../../src/fossils.js';
import { ageToY } from '../../src/layout.js';

const loc = { name_en: 'Ban Tha Kradan', name_th: 'บ้านท่ากระดาน', tambon_th: 'ท่ากระดาน', amphoe_th: 'ศรีสวัสดิ์',
  province_th: 'กาญจนบุรี', province_en: 'Kanchanaburi', lat: 14.6, lon: 99.1, precision: 'area' };
const mk = (id, top, base, extra = {}) => ({ id, taxon: `Taxon ${id}`, group: 'nautiloid', age_top_ma: top, age_base_ma: base,
  stage: 'Sandbian', formation_en: 'Pa Kae Fm', formation_th: 'หมวดหินป่าแก่', locality: loc, significance_th: 'ก',
  significance_en: 'Index <fossil>', citation: { text: 'F 2021', url: 'https://doi.org/10.1/x' }, source_type: 'peer-reviewed', verified: false, ...extra });
const periods = [
  { id: 'ordovician', start_ma: 486.85, end_ma: 443.1, name_th: 'ยุคออร์โดวิเชียน', name_en: 'Ordovician' },
  { id: 'permian', start_ma: 298.9, end_ma: 251.902, name_th: 'ยุคเพอร์เมียน', name_en: 'Permian' },
];
const bands = [{ period: periods[0], y: 0, h: 200 }, { period: periods[1], y: 200, h: 100 }];

test('groups have icon and both labels', () => {
  for (const g of Object.values(FOSSIL_GROUPS)) assert.ok(g.icon && g.th && g.en);
  assert.ok(FOSSIL_GROUPS.trilobite && FOSSIL_GROUPS.dinosaur && FOSSIL_GROUPS.fusulinid);
});

test('fossilMidAge is the middle of the range', () => {
  assert.equal(fossilMidAge(mk('a', 449, 459)), 454);
});

test('ageToY maps linearly inside the band containing the age', () => {
  assert.equal(ageToY(486.85, bands), 0);
  assert.equal(Math.round(ageToY(275.4, bands)), 250);
  assert.equal(ageToY(600, bands), null);
});

test('placeFossils puts icons at their age and never overlaps within a column', () => {
  const list = [mk('a', 454, 454.2), mk('b', 454, 454.2), mk('c', 454, 454.2), mk('d', 270, 280)];
  const placed = placeFossils(bands, list, { size: 18, columns: 2 });
  assert.equal(placed.length, 4);
  const byId = Object.fromEntries(placed.map(p => [p.fossil.id, p]));
  assert.notEqual(byId.a.x, byId.b.x);
  assert.equal(byId.c.y, byId.a.y + 18);
  for (const col of [0, 20]) {
    const ys = placed.filter(p => p.x === col).map(p => p.y).sort((m, n) => m - n);
    for (let i = 1; i < ys.length; i++) assert.ok(ys[i] - ys[i - 1] >= 18);
  }
});

test('fossils outside every band are skipped', () => {
  assert.equal(placeFossils(bands, [mk('z', 100, 110)], { size: 18, columns: 1 }).length, 0);
});

test('localityText in Thai and English, skipping unknown tambon or amphoe', () => {
  assert.equal(localityText(loc, 'th'), 'บ้านท่ากระดาน ต.ท่ากระดาน อ.ศรีสวัสดิ์ จ.กาญจนบุรี');
  assert.equal(localityText(loc, 'en'), 'Ban Tha Kradan, Tambon ท่ากระดาน, Amphoe ศรีสวัสดิ์, Kanchanaburi Province');
  assert.equal(localityText({ ...loc, tambon_th: null, amphoe_th: null }, 'th'), 'บ้านท่ากระดาน จ.กาญจนบุรี');
});

test('filterFossils by text, period, province and group', () => {
  const list = [mk('a', 449, 459), mk('d', 270, 280, { group: 'fusulinid', taxon: 'Neoschwagerina', locality: { ...loc, name_th: 'เขางู', name_en: 'Khao Ngu', tambon_th: 'เจดีย์หัก', amphoe_th: 'เมืองราชบุรี', province_en: 'Ratchaburi', province_th: 'ราชบุรี' } })];
  assert.deepEqual(filterFossils(list, { q: 'neosch' }, periods).map(f => f.id), ['d']);
  assert.deepEqual(filterFossils(list, { q: 'ท่ากระดาน' }, periods).map(f => f.id), ['a']);
  assert.deepEqual(filterFossils(list, { period: 'permian' }, periods).map(f => f.id), ['d']);
  assert.deepEqual(filterFossils(list, { province: 'Kanchanaburi' }, periods).map(f => f.id), ['a']);
  assert.deepEqual(filterFossils(list, { group: 'fusulinid' }, periods).map(f => f.id), ['d']);
  assert.deepEqual(filterFossils(list, {}, periods).map(f => f.id), ['a', 'd']);
});

test('fossil card escapes text and shows locality, coordinates and map link', () => {
  initLang(null);
  setLang('en');
  const html = fossilCardHtml(mk('a', 449, 459));
  assert.ok(html.includes('<em>Taxon a</em>'));
  assert.ok(html.includes('Index &lt;fossil&gt;'));
  assert.ok(html.includes('Ban Tha Kradan, Tambon'));
  assert.ok(html.includes('https://www.google.com/maps?q=14.6,99.1'));
  assert.ok(html.includes('449–459 Ma'));
  setLang('th');
});

test('amphibians have a group', () => {
  assert.ok(FOSSIL_GROUPS.amphibian && FOSSIL_GROUPS.amphibian.th);
});

test('locality falls back to the English place name when the Thai one is unknown', () => {
  assert.equal(localityText({ ...loc, name_th: null }, 'th'), 'Ban Tha Kradan ต.ท่ากระดาน อ.ศรีสวัสดิ์ จ.กาญจนบุรี');
});

test('shortCitation gives first author, et al. and year', async () => {
  const { shortCitation } = await import('../../src/fossils.js');
  assert.equal(shortCitation('Wernette S.J., Hughes N.C., Myrow P.M., Sardsud A. 2020, Satunarcus, a new genus, J Paleont 94:867-880'), 'Wernette et al. 2020');
  assert.equal(shortCitation('Archbold 1999, Neochonetes, Proc Roy Soc Vic'), 'Archbold 1999');
  assert.equal(shortCitation('Filoux A. & Suteethorn V. 2018, A late Pleistocene skeleton, Geobios 51:31-49'), 'Filoux & Suteethorn 2018');
  assert.equal(shortCitation('No year here'), 'No year here');
});
