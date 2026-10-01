import { nearestSlice, frameDue } from './select.js';
import { shortestLonDelta, normalizeWinding } from './geo.js';

export function createGlobe(canvas, slices, { reducedMotion = false } = {}) {
  const ctx = canvas.getContext('2d');
  const projection = d3.geoOrthographic().clipAngle(90).precision(0.5);
  const path = d3.geoPath(projection, ctx);
  const graticule = d3.geoGraticule10();
  const prepared = {};
  for (const [k, s] of Object.entries(slices)) {
    prepared[k] = { ...s, coastlines: normalizeWinding(s.coastlines, d3.geoArea) };
  }
  const ages = Object.keys(prepared).map(Number);
  let current = null;
  let previous = null;
  let fade = 1;
  let rotation = [0, 0];
  let anim = null;
  let dragged = false;
  let width = 0;
  let height = 0;

  let palette = null;
  let lastDraw = -Infinity;

  function readColors() {
    const cs = getComputedStyle(canvas);
    const v = name => cs.getPropertyValue(name).trim();
    return { ocean: v('--globe-ocean'), land: v('--globe-land'), grid: v('--globe-grid'), edge: v('--globe-edge'), marker: v('--globe-marker') };
  }

  function colors() {
    if (!palette) palette = readColors();
    return palette;
  }

  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    palette = null;
    draw(performance.now());
  });

  function drawLand(slice, c) {
    ctx.beginPath();
    path(slice.coastlines);
    ctx.fillStyle = c.land;
    ctx.fill();
  }

  function drawMarker(lonlat, c, now) {
    if (d3.geoDistance(lonlat, [-rotation[0], -rotation[1]]) > Math.PI / 2) return;
    const p = projection(lonlat);
    if (!p) return;
    ctx.beginPath();
    ctx.arc(p[0], p[1], 5, 0, 2 * Math.PI);
    ctx.fillStyle = c.marker;
    ctx.fill();
    if (!reducedMotion) {
      const k = (now % 1600) / 1600;
      ctx.beginPath();
      ctx.arc(p[0], p[1], 5 + k * 14, 0, 2 * Math.PI);
      ctx.strokeStyle = c.marker;
      ctx.lineWidth = 2;
      ctx.globalAlpha = 1 - k;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
  }

  function draw(now) {
    if (!width) return;
    lastDraw = now;
    const c = colors();
    projection.rotate(rotation);
    ctx.clearRect(0, 0, width, height);
    ctx.beginPath(); path({ type: 'Sphere' }); ctx.fillStyle = c.ocean; ctx.fill();
    ctx.beginPath(); path(graticule); ctx.strokeStyle = c.grid; ctx.lineWidth = 0.5; ctx.stroke();
    if (previous && fade < 1) { ctx.globalAlpha = 1 - fade; drawLand(previous, c); }
    if (current) { ctx.globalAlpha = previous ? fade : 1; drawLand(current, c); }
    ctx.globalAlpha = 1;
    if (current) drawMarker(current.kanchanaburi, c, now);
    ctx.beginPath(); path({ type: 'Sphere' }); ctx.strokeStyle = c.edge; ctx.lineWidth = 1; ctx.stroke();
  }

  function frame(now) {
    if (anim) anim(now);
    if (frameDue(now, lastDraw, anim !== null)) draw(now);
    if (!reducedMotion || anim) requestAnimationFrame(frame);
  }

  function animateTo(target, withFade) {
    if (reducedMotion) {
      rotation = target; previous = null; fade = 1; draw(performance.now());
      return;
    }
    const start = rotation.slice();
    const dLon = shortestLonDelta(start[0], target[0]);
    const dLat = target[1] - start[1];
    const t0 = performance.now();
    fade = withFade ? 0 : 1;
    anim = now => {
      const k = Math.min(1, (now - t0) / 600);
      const e = d3.easeCubicInOut(k);
      rotation = [start[0] + dLon * e, start[1] + dLat * e];
      if (withFade) fade = e;
      if (k >= 1) { anim = null; previous = null; fade = 1; }
    };
  }

  function showSlice(age) {
    const { age: a, exact } = nearestSlice(age, ages);
    const next = prepared[String(a)];
    const info = { age: a, exact, lonlat: next.kanchanaburi };
    const target = [-next.kanchanaburi[0], -next.kanchanaburi[1]];
    if (current === next) {
      if (dragged) { dragged = false; animateTo(target, false); }
      return info;
    }
    const first = current === null;
    previous = current;
    current = next;
    dragged = false;
    if (first) { rotation = target; previous = null; draw(performance.now()); } else { animateTo(target, true); }
    return info;
  }

  function resize() {
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    width = rect.width; height = rect.height;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    projection.translate([width / 2, height / 2]).scale(Math.min(width, height) / 2 - 4);
    draw(performance.now());
  }

  d3.select(canvas).call(d3.drag().on('drag', ev => {
    dragged = true;
    anim = null;
    const lon = ((rotation[0] + ev.dx * 0.4 + 540) % 360) - 180;
    rotation = [lon, Math.max(-90, Math.min(90, rotation[1] - ev.dy * 0.4))];
    draw(performance.now());
  }));

  requestAnimationFrame(frame);
  return { showSlice, resize };
}
