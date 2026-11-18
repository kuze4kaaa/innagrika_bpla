
const p1 = { x: 3.58, y: 3.08 };
const p2 = { x: 5.48, y: 2.05 };
// test across randomized NFZ-2
for (let cy = 1.30; cy <= 1.70; cy += 0.05) {
  for (let cx = 4.20; cx <= 4.70; cx += 0.05) {
    const z = {
      barrierMinX: cx - 0.4 - 0.33,
      barrierMaxX: cx + 0.4 + 0.33,
      barrierMinY: cy - 0.4 - 0.33,
      barrierMaxY: cy + 0.4 + 0.33
    };
    const dist = Math.hypot(p2.x - p1.x, p2.y - p1.y);
    const steps = Math.max(1, Math.ceil(dist / 0.04));
    for (let s = 1; s < steps; s++) {
      const px = p1.x + (p2.x - p1.x) * (s / steps);
      const py = p1.y + (p2.y - p1.y) * (s / steps);
      if (px > z.barrierMinX && px < z.barrierMaxX && py > z.barrierMinY && py < z.barrierMaxY) {
        console.log(HIT at cx=, cy=: px=, py=);
        break;
      }
    }
  }
}
