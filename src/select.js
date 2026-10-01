export function activeIndex(rows, centerY, rowH) {
  let best = -1;
  let bestDist = Infinity;
  rows.forEach((r, i) => {
    const d = Math.abs(r.y + rowH / 2 - centerY);
    if (d < bestDist) { bestDist = d; best = i; }
  });
  return best;
}

export function nearestSlice(age, sliceAges) {
  if (!sliceAges.length) throw new Error('No paleo slices available');
  let best = sliceAges[0];
  for (const a of sliceAges) {
    if (Math.abs(a - age) < Math.abs(best - age)) best = a;
  }
  return { age: best, exact: best === age };
}
