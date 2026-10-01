export function shortestLonDelta(from, to) {
  return ((((to - from) % 360) + 540) % 360) - 180;
}

function fixPolygon(rings, geoArea) {
  const area = geoArea({ type: 'Polygon', coordinates: rings });
  return area > 2 * Math.PI ? rings.map(r => [...r].reverse()) : rings;
}

export function normalizeWinding(fc, geoArea) {
  return {
    type: 'FeatureCollection',
    features: fc.features.map(f => {
      const g = f.geometry;
      const coordinates = g.type === 'Polygon'
        ? fixPolygon(g.coordinates, geoArea)
        : g.coordinates.map(poly => fixPolygon(poly, geoArea));
      return { type: 'Feature', properties: {}, geometry: { type: g.type, coordinates } };
    }),
  };
}
