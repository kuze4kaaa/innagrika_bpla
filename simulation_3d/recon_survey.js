'use strict';

const ReconSurvey = (() => {
  // Параметрический интервал отрезка внутри прямоугольника. Касание его
  // границы разрешено: рабочий отступ уже меньше планового на 2 см.
  function crossesInterior(a, b, box) {
    let enter = 0;
    let exit = 1;
    for (const [axis, min, max] of [['x', box.minX, box.maxX], ['y', box.minY, box.maxY]]) {
      const delta = b[axis] - a[axis];
      if (delta === 0) {
        if (a[axis] <= min || a[axis] >= max) return false;
        continue;
      }
      const t1 = (min - a[axis]) / delta;
      const t2 = (max - a[axis]) / delta;
      enter = Math.max(enter, Math.min(t1, t2));
      exit = Math.min(exit, Math.max(t1, t2));
      if (enter >= exit) return false;
    }
    return true;
  }

  function safeLeg(a, b, obstacles, corners) {
    const clear = (p, q) => obstacles.every(box => !crossesInterior(p, q, box));
    if (clear(a, b)) return [b];

    // Рёбра графа видимости только по свободным отрезкам. Вес равен длине.
    const nodes = [a, b, ...corners];
    const distances = nodes.map(() => Infinity);
    const parents = nodes.map(() => -1);
    const visited = new Set();
    distances[0] = 0;
    while (true) {
      let current = -1;
      for (let i = 0; i < nodes.length; i++) {
        if (visited.has(i) || !Number.isFinite(distances[i])) continue;
        if (current === -1 || distances[i] < distances[current]) current = i;
      }
      if (current === -1) return null;
      if (current === 1) break;
      visited.add(current);
      for (let i = 1; i < nodes.length; i++) {
        if (visited.has(i) || !clear(nodes[current], nodes[i])) continue;
        const length = distances[current] + Math.hypot(
          nodes[i].x - nodes[current].x, nodes[i].y - nodes[current].y
        );
        if (length < distances[i]) {
          distances[i] = length;
          parents[i] = current;
        }
      }
    }
    const leg = [];
    for (let i = 1; i !== 0; i = parents[i]) leg.push(nodes[i]);
    return leg.reverse();
  }

  function freeSpans(y, left, right, obstacles) {
    const blocked = obstacles
      .filter(box => box.minY < y && y < box.maxY)
      .map(box => [Math.max(left, box.minX), Math.min(right, box.maxX)])
      .filter(([start, end]) => start < end)
      .sort(([a], [b]) => a - b);
    const spans = [];
    let cursor = left;
    for (const [start, end] of blocked) {
      if (start > cursor) spans.push([cursor, start]);
      cursor = Math.max(cursor, end);
    }
    if (cursor < right) spans.push([cursor, right]);
    return spans;
  }

  function plan({ width, height, clearance, obstacles, home, footprint, cells }) {
    const bounds = { minX: clearance, maxX: width - clearance, minY: clearance, maxY: height - clearance };
    const expanded = obstacles.map(({ cx, cy, w, h }) => ({
      minX: cx - (w / 2 + clearance), maxX: cx + (w / 2 + clearance),
      minY: cy - (h / 2 + clearance), maxY: cy + (h / 2 + clearance)
    }));
    const inside = (p, box) => box.minX < p.x && p.x < box.maxX && box.minY < p.y && p.y < box.maxY;
    const safePoint = p => p.x >= bounds.minX && p.x <= bounds.maxX &&
      p.y >= bounds.minY && p.y <= bounds.maxY && !expanded.some(box => inside(p, box));
    if (!safePoint(home) || footprint.x <= clearance || footprint.y <= clearance) return null;

    const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
    const corners = [bounds, ...expanded].flatMap(box => [box.minX, box.maxX].flatMap(x =>
      [box.minY, box.maxY].map(y => ({
        x: clamp(x, bounds.minX, bounds.maxX), y: clamp(y, bounds.minY, bounds.maxY)
      })))).filter(safePoint);
    const path = [{ ...home, kind: 'takeoff' }];
    const pending = new Set(cells);
    const viewBox = p => ({
      minX: p.x - footprint.x, maxX: p.x + footprint.x,
      minY: p.y - footprint.y, maxY: p.y + footprint.y
    });
    function append(p, kind) {
      const previous = path[path.length - 1];
      if (previous.x !== p.x || previous.y !== p.y) path.push({ ...p, kind });
      for (const cell of pending) {
        if (crossesInterior(previous, p, viewBox(cell))) pending.delete(cell);
      }
    }

    // 20% перекрытия. Крайние галсы находятся у границ безопасной области.
    const rowCount = Math.max(1, Math.ceil((bounds.maxY - bounds.minY) / (1.6 * footprint.y)));
    for (let row = 0; row <= rowCount; row++) {
      const y = bounds.minY + (bounds.maxY - bounds.minY) * (row / rowCount);
      const spans = freeSpans(y, bounds.minX, bounds.maxX, expanded);
      if (row % 2) spans.reverse();
      for (const span of spans) {
        const [start, end] = row % 2 ? [span[1], span[0]] : span;
        const leg = safeLeg(path[path.length - 1], { x: start, y }, expanded, corners);
        if (!leg) continue;
        for (const p of leg) append(p, 'transit');
        append({ x: end, y }, 'survey');
      }
    }

    // После основных галсов доснимаем клетки, которые могли остаться за обходом.
    // Проверяем ближайшие точки на сетке границ препятствий и проекций клетки.
    const axes = [bounds, ...expanded];
    for (const cell of pending) {
      const { minX, maxX, minY, maxY } = viewBox(cell);
      const xs = new Set([clamp(cell.x, bounds.minX, bounds.maxX), ...axes.flatMap(b => [b.minX, b.maxX])]);
      const ys = new Set([clamp(cell.y, bounds.minY, bounds.maxY), ...axes.flatMap(b => [b.minY, b.maxY])]);
      const candidates = [...xs].flatMap(x => [...ys].map(y => ({ x, y })))
        .filter(p => minX < p.x && p.x < maxX && minY < p.y && p.y < maxY && safePoint(p));
      const from = path[path.length - 1];
      candidates.sort((a, b) => Math.hypot(a.x - from.x, a.y - from.y) - Math.hypot(b.x - from.x, b.y - from.y));
      for (const candidate of candidates) {
        const leg = safeLeg(from, candidate, expanded, corners);
        if (!leg) continue;
        for (const p of leg) append(p, 'fill');
        break;
      }
    }

    const returnLeg = safeLeg(path[path.length - 1], home, expanded, corners);
    if (!returnLeg) return null;
    for (const p of returnLeg) append(p, 'return');
    path.push({ ...home, kind: 'land' });
    return { path, uncoveredCells: pending.size };
  }

  return { plan, crossesInterior };
})();

if (typeof module !== 'undefined') module.exports = ReconSurvey;
