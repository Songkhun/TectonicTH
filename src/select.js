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

// The active line sits a quarter of the way down the timeline so the event card never covers it.
export function scrollPads(clientHeight) {
  const top = Math.round(clientHeight * 0.25);
  return { top, bottom: clientHeight - top };
}

// Idle redraws (the marker pulse) run at about 15 fps; animation frames always draw.
export function frameDue(now, lastDraw, animating, interval = 66) {
  return animating || now - lastDraw >= interval;
}
