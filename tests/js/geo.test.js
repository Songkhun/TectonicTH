import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { shortestLonDelta, normalizeWinding } from '../../src/geo.js';

// d3.min.js is a UMD script; run it as a classic script so it sets `d3` on the sandbox global.
const sandbox = vm.createContext({});
vm.runInContext(readFileSync(new URL('../../vendor/d3.min.js', import.meta.url), 'utf8'), sandbox);
const d3 = sandbox.d3;

test('shortestLonDelta takes the short way across the antimeridian', () => {
  assert.equal(shortestLonDelta(170, -170), 20);
  assert.equal(shortestLonDelta(-170, 170), -20);
  assert.equal(shortestLonDelta(0, 90), 90);
  assert.equal(shortestLonDelta(10, 10), 0);
});

const ccw = [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]];
const fc = ring => ({ type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [ring] } }] });

test('normalizeWinding flips RFC 7946 rings so d3 fills the land, not the ocean', () => {
  assert.ok(d3.geoArea(fc(ccw)) > 2 * Math.PI);
  const fixed = normalizeWinding(fc(ccw), d3.geoArea);
  assert.ok(d3.geoArea(fixed) < 0.1);
});

test('normalizeWinding leaves correct rings and handles MultiPolygon', () => {
  const cw = [...ccw].reverse();
  assert.deepEqual(normalizeWinding(fc(cw), d3.geoArea).features[0].geometry.coordinates[0], cw);
  const multi = { type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: { type: 'MultiPolygon', coordinates: [[ccw], [cw]] } }] };
  assert.ok(d3.geoArea(normalizeWinding(multi, d3.geoArea)) < 0.2);
});
