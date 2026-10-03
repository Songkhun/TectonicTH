import { t, field, getLang } from './i18n.js';
import { esc } from './format.js';
import { FOSSIL_GROUPS } from './fossils.js';
import { normalizeWinding } from './geo.js';

// Every located item for the map: evidence sites, fossil localities and event visit sites.
export function mapPoints(data) {
  const pts = [];
  for (const it of data.evidence || []) {
    if (it.site) pts.push({ kind: 'evidence', id: it.id, lat: it.site.lat, lon: it.site.lon, method: it.method, item: it });
  }
  for (const f of data.fossils || []) {
    const g = FOSSIL_GROUPS[f.group] || FOSSIL_GROUPS.other;
    pts.push({ kind: 'fossil', id: f.id, lat: f.locality.lat, lon: f.locality.lon, icon: g.icon,
      kan: f.locality.province_en === 'Kanchanaburi', item: f });
  }
  for (const e of data.events || []) {
    if (e.visit_site) pts.push({ kind: 'visit', id: e.id, lat: e.visit_site.lat, lon: e.visit_site.lon, item: e });
  }
  return pts;
}

const METHOD_COLOR = {
  paleomagnetism: '--ev-paleomag', geochronology: '--ev-dating', thermochronology: '--ev-dating', biostratigraphy: '--ev-dating',
  geochemistry: '--ev-dating', mapping: '--ev-field', 'field-survey': '--ev-field',
};

// D3 map: Natural Earth base map (region) or the 0 Ma globe slice (world), faults, schematic sutures,
// terrane labels and every located item. Points keep their size while zooming.
export function createMap(svgEl, data, { onSelect }) {
  const svg = d3.select(svgEl);
  const pts = mapPoints(data);
  const layers = { evidence: true, fossils: true, visits: true, faults: true, sutures: true, terranes: true };
  let world = false;
  let transform = d3.zoomIdentity;
  let projection = null;
  const css = name => getComputedStyle(svgEl).getPropertyValue(name).trim();

  const zoom = d3.zoom().scaleExtent([1, 40]).on('zoom', ev => { transform = ev.transform; place(); });
  svg.call(zoom);

  function regionProjection(w, h) {
    const box = (data.basemap && data.basemap.bbox) || [85, -12, 125, 32];
    const outline = { type: 'Feature', geometry: { type: 'Polygon', coordinates: [[[box[0], box[1]], [box[2], box[1]], [box[2], box[3]], [box[0], box[3]], [box[0], box[1]]]] } };
    return d3.geoMercator().fitExtent([[4, 4], [w - 4, h - 4]], outline);
  }

  function render() {
    const { width: w, height: h } = svgEl.getBoundingClientRect();
    if (!w || !h) return;
    svg.attr('viewBox', `0 0 ${w} ${h}`);
    svg.selectAll('*').remove();
    projection = world ? d3.geoEquirectangular().fitExtent([[4, 4], [w - 4, h - 4]], { type: 'Sphere' }) : regionProjection(w, h);
    const path = d3.geoPath(projection);
    const base = svg.append('g').attr('class', 'mp-base');
    base.append('rect').attr('x', -1e4).attr('y', -1e4).attr('width', 2e4).attr('height', 2e4).attr('fill', css('--globe-ocean'));
    const land = world ? normalizeWindingForMap(data.slices['0'].coastlines) : data.basemap && data.basemap.land;
    if (land) base.append('path').attr('d', path(land)).attr('fill', css('--globe-land'));
    if (!world && data.basemap) {
      base.append('path').attr('d', path(data.basemap.borders)).attr('class', 'mp-border');
    }
    if (!world && data.faults && layers.faults) {
      base.append('path').attr('d', path(data.faults.faults)).attr('class', 'mp-fault');
    }
    if (layers.sutures) {
      for (const s of data.sutures.sutures) {
        const line = { type: 'LineString', coordinates: s.points.map(p => [p.lon, p.lat]) };
        base.append('path').attr('d', path(line)).attr('class', 'mp-suture').append('title').text(field(s, 'name'));
      }
    }
    svg.append('g').attr('class', 'mp-labels');
    svg.append('g').attr('class', 'mp-points');
    place();
  }

  function place() {
    if (!projection) return;
    svg.select('.mp-base').attr('transform', transform);
    const at = (lon, lat) => { const p = projection([lon, lat]); return [transform.applyX(p[0]), transform.applyY(p[1])]; };
    const labels = svg.select('.mp-labels');
    labels.selectAll('*').remove();
    if (layers.terranes) {
      for (const tr of data.sutures.terranes) {
        const [x, y] = at(tr.label_lon, tr.label_lat);
        labels.append('text').attr('x', x).attr('y', y).attr('class', 'mp-terrane').text(field(tr, 'name'));
      }
    }
    if (layers.sutures) {
      for (const s of data.sutures.sutures) {
        const mid = s.points[Math.floor(s.points.length / 2)];
        const [x, y] = at(mid.lon, mid.lat);
        labels.append('text').attr('x', x + 6).attr('y', y).attr('class', 'mp-suture-label').text(field(s, 'name'));
      }
    }
    const g = svg.select('.mp-points');
    g.selectAll('*').remove();
    for (const p of pts) {
      if ((p.kind === 'evidence' && !layers.evidence) || (p.kind === 'fossil' && !layers.fossils) || (p.kind === 'visit' && !layers.visits)) continue;
      const [x, y] = at(p.lon, p.lat);
      const node = p.kind === 'fossil'
        ? g.append('text').attr('x', x).attr('y', y).attr('class', `mp-fossil${p.kan ? ' is-kan' : ''}`).text(p.icon)
        : p.kind === 'visit'
          ? g.append('path').attr('transform', `translate(${x},${y})`).attr('d', d3.symbol(d3.symbolStar, 90)()).attr('class', 'mp-visit')
          : g.append('circle').attr('cx', x).attr('cy', y).attr('r', 5).attr('class', 'mp-ev')
            .attr('fill', css(METHOD_COLOR[p.method] || '--ev-geophys'));
      node.attr('tabindex', 0).attr('role', 'button')
        .attr('aria-label', p.kind === 'fossil' ? p.item.taxon : field(p.item, 'title'))
        .on('click', () => onSelect(p))
        .on('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); onSelect(p); } })
        .append('title').text(p.kind === 'fossil' ? p.item.taxon : field(p.item, 'title'));
    }
  }

  function showThailand() {
    world = false;
    render();
    const th = projection([96.5, 21]); const th2 = projection([106, 5.5]);
    const { width: w, height: h } = svgEl.getBoundingClientRect();
    const k = Math.min(w / (th2[0] - th[0]), h / (th2[1] - th[1])) * 0.92;
    const t0 = d3.zoomIdentity.translate(w / 2, h / 2).scale(k).translate(-(th[0] + th2[0]) / 2, -(th[1] + th2[1]) / 2);
    svg.call(zoom.transform, t0);
  }

  function showWorld() {
    world = true;
    svg.call(zoom.transform, d3.zoomIdentity);
    render();
  }

  function setLayer(name, on) { layers[name] = on; render(); }

  return { showThailand, showWorld, setLayer, refresh: () => { render(); }, isWorld: () => world };
}

function normalizeWindingForMap(fc) {
  return normalizeWinding(fc, d3.geoArea);
}
