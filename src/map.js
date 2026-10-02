import { t, field, getLang } from './i18n.js';
import { esc } from './format.js';
import { FOSSIL_GROUPS } from './fossils.js';

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
