import test from 'node:test';
import assert from 'node:assert/strict';
import { initLang, setLang } from '../../src/i18n.js';
import { mapPoints } from '../../src/map.js';
import { modelLayout, rolesTableHtml } from '../../src/models.js';

const data = {
  evidence: [
    { id: 'e1', method: 'paleomagnetism', title_en: 'Pole <x>', title_th: 'ขั้ว', site: { name_en: 'Baoshan', name_th: 'เป่าซาน', lat: 25.1, lon: 99.2 } },
    { id: 'e2', method: 'seismic', title_en: 'No site', title_th: 'ไม่มี', site: null },
  ],
  fossils: [{ id: 'f1', taxon: 'Sinoceras chinense', group: 'nautiloid', locality: { name_en: 'Tha Kradan', lat: 14.45, lon: 99.11, province_en: 'Kanchanaburi' } }],
  events: [
    { id: 'v1', title_en: 'Erawan', title_th: 'เอราวัณ', visit_site: { name_en: 'Erawan Falls', name_th: 'น้ำตกเอราวัณ', lat: 14.37, lon: 99.14 } },
    { id: 'v2', title_en: 'No site', visit_site: null },
  ],
};

test('mapPoints collects every located item with its kind and skips unlocated ones', () => {
  const pts = mapPoints(data);
  assert.deepEqual(pts.map(p => `${p.kind}:${p.id}`), ['evidence:e1', 'fossil:f1', 'visit:v1']);
  const e = pts[0];
  assert.equal(e.lat, 25.1);
  assert.equal(e.lon, 99.2);
  assert.equal(e.method, 'paleomagnetism');
  assert.equal(pts[1].icon, '🦑');
  assert.equal(pts[1].kan, true);
});

const Q = {
  axis: { base_ma: 300, top_ma: 200 },
  models: [{ id: 'a', phases: [{ base_ma: 260, top_ma: 240, label_en: 'Collision' }] }, { id: 'b', phases: [{ base_ma: 230, top_ma: 220, label_en: 'Late' }] }],
  evidence: [{ evidence_id: 'x', age_base_ma: 250, age_top_ma: 250, roles: { a: 'supports', b: 'challenges' } },
             { evidence_id: 'y', age_base_ma: 290, age_top_ma: 270, roles: { a: 'neutral', b: 'supports' } }],
};

test('modelLayout puts older ages on the left and scales bars to the axis', () => {
  const L = modelLayout(Q, 1000, { left: 0, right: 0 });
  assert.equal(L.x(300), 0);
  assert.equal(L.x(200), 1000);
  const bar = L.rows[0].bars[0];
  assert.equal(bar.x, 400);
  assert.equal(bar.w, 200);
  assert.equal(L.markers[0].x, 500);
  assert.equal(L.markers[0].w, 0);
  assert.equal(L.markers[1].x, 100);
  assert.equal(L.markers[1].w, 200);
});

test('modelLayout clamps out-of-window ages to the axis', () => {
  const L = modelLayout({ ...Q, evidence: [{ evidence_id: 'z', age_base_ma: 400, age_top_ma: 150, roles: {} }] }, 1000, { left: 0, right: 0 });
  assert.equal(L.markers[0].x, 0);
  assert.equal(L.markers[0].w, 1000);
});

test('rolesTableHtml shows a mark for every model and escapes text', () => {
  initLang(null);
  setLang('en');
  const q = { ...Q, models: [{ ...Q.models[0], name_en: 'Model <A>' }, { ...Q.models[1], name_en: 'Model B' }],
    evidence: [{ ...Q.evidence[0], reason_en: 'Fits & "works"' }] };
  const html = rolesTableHtml(q, { x: { id: 'x', title_en: 'Chert <ages>', method: 'biostratigraphy' } });
  assert.ok(html.includes('Model &lt;A&gt;') && html.includes('Chert &lt;ages&gt;'));
  assert.ok(html.includes('Fits &amp; &quot;works&quot;'));
  assert.ok(html.includes('role-supports') && html.includes('role-challenges'));
  assert.ok(html.includes('data-evidence="x"'));
  setLang('th');
});
