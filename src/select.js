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

// Index of the lecture stop closest in age to the event now on screen (keeps Next/Previous in step
// after the student scrolls by hand).
export function nearestStopIndex(stops, event) {
  let best = -1;
  let bestDist = Infinity;
  stops.forEach((s, i) => {
    const d = Math.abs(s.age_ma - event.age_ma);
    if (d < bestDist) { bestDist = d; best = i; }
  });
  return best;
}

// What a key does in lecture mode; null means let the browser handle it.
export function lectureKeyAction(key, targetTag, dialogOpen) {
  if (dialogOpen) return null;
  if (key === ' ' && (targetTag === 'BUTTON' || targetTag === 'A')) return null;
  if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(key)) return 'next';
  if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(key)) return 'prev';
  if (key === 'Escape') return 'exit';
  return null;
}
