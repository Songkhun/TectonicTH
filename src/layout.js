export function periodOf(age, periods) {
  for (const p of periods) {
    if (age >= p.end_ma && age < p.start_ma) return p;
  }
  return null;
}

export function layoutTimeline(events, periods, { rowH = 64, minPeriodH = 140 } = {}) {
  const ordered = [...periods].sort((a, b) => b.start_ma - a.start_ma);
  const groups = new Map(ordered.map(p => [p.id, []]));
  for (const e of events) {
    const p = periodOf(e.age_ma, ordered);
    if (!p) throw new Error(`Event ${e.id} (age ${e.age_ma} Ma) is outside the time scale`);
    groups.get(p.id).push(e);
  }
  const rows = [];
  const bands = [];
  let y = 0;
  for (const p of ordered) {
    const evs = groups.get(p.id).sort((a, b) => b.age_ma - a.age_ma || a.id.localeCompare(b.id));
    const h = Math.max(minPeriodH, evs.length * rowH);
    bands.push({ period: p, y, h });
    evs.forEach((e, i) => rows.push({ event: e, y: y + i * rowH }));
    y += h;
  }
  return { rows, bands, height: y };
}
