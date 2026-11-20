const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const test = require('node:test');
const { runInThisContext } = require('node:vm');

const html = readFileSync(join(__dirname, '../simulation_3d/index.html'), 'utf8');
const planner = html.match(/<script id="recon-survey">([\s\S]*?)<\/script>/);
assert.ok(planner, 'the survey planner must be bundled with the page');
const { plan, repairPath, crossesInterior } = runInThisContext(
  '(function () {' + planner[1] + '\nreturn ReconSurvey;\n})()',
  { filename: 'index.html#recon-survey' }
);

const config = {
  width: 6, height: 4, clearance: 0.25,
  home: { x: 0.4, y: 0.4 }, footprint: { x: 0.726, y: 0.517 }, cells: []
};

const grid = Array.from({ length: 2400 }, (_, i) => ({
  x: (i % 60 + 0.5) / 10, y: (Math.floor(i / 60) + 0.5) / 10
}));

test('empty field: alternating horizontal survey legs cover the whole grid', () => {
  const result = plan({ ...config, cells: grid, obstacles: [] });
  assert.equal(result.uncoveredCells, 0);
  const walks = result.path.flatMap((end, i) => end.kind === 'survey' ? [[result.path[i - 1], end]] : []);
  assert.ok(walks.length >= 2);
  for (const [i, [start, end]] of walks.entries()) {
    assert.equal(start.y, end.y);
    assert.equal(start.x, i % 2 ? 5.75 : 0.25);
    assert.equal(end.x, i % 2 ? 0.25 : 5.75);
  }
});

test('obstacles: flies both free parts of an interrupted lane and returns to base', () => {
  const obstacles = [{ cx: 2.5, cy: 2, w: 1, h: 1 }, { cx: 4.5, cy: 2, w: 0.5, h: 1 }];
  const { path } = plan({ ...config, obstacles });
  const row = path.filter(p => Math.abs(p.y - 2.35) < 1e-9);
  assert.deepEqual(row.map(p => p.x), [5.75, 5, 4, 3.25, 1.75, 0.25]);
  assert.equal(row.filter(p => p.kind === 'survey').length, 3);
  assert.deepEqual(path.at(-1), { ...config.home, kind: 'land' });
  for (let i = 1; i < path.length; i++) {
    for (const { cx, cy, w, h } of obstacles) {
      assert.equal(crossesInterior(path[i - 1], path[i], {
        minX: cx - w / 2 - 0.23, maxX: cx + w / 2 + 0.23,
        minY: cy - h / 2 - 0.23, maxY: cy + h / 2 + 0.23
      }), false);
    }
  }
});

test('reports cells behind an impassable wall and does not route through it', () => {
  const obstacle = { cx: 3, cy: 2, w: 0.4, h: 4 };
  const result = plan({ ...config, obstacles: [obstacle], cells: [{ x: 5, y: 2 }] });
  assert.equal(result.uncoveredCells, 1);
  assert.ok(result.path.every(p => p.x <= 2.55));
  assert.deepEqual(result.path.at(-1), { ...config.home, kind: 'land' });
});

test('fills a gap missed by the main passes around an obstacle', () => {
  const obstacle = { cx: 2.5, cy: 2.23, w: 1.2, h: 0.1 };
  const cells = grid.filter(({ x, y }) =>
    Math.abs(x - obstacle.cx) > obstacle.w / 2 || Math.abs(y - obstacle.cy) > obstacle.h / 2
  );
  const result = plan({ ...config, obstacles: [obstacle], cells, footprint: { x: 0.31, y: 0.33 } });
  assert.ok(result.path.some(p => p.kind === 'fill'));
  assert.equal(result.uncoveredCells, 0);
});

test('rejects a base inside the required obstacle clearance', () => {
  const obstacles = [{ cx: 0.65, cy: 0.45, w: 0.3, h: 0.3 }];
  assert.equal(plan({ ...config, obstacles }), null);
});

test('the sweep stays straight until a zone is seen, then rejoins just beyond it in either direction', () => {
  const obstacle = { cx: 3, cy: 2, w: 1, h: 1 };
  const box = { minX: 2.25, maxX: 3.75, minY: 1.25, maxY: 2.75 };

  for (const [x, destination, entry, exit] of [[1, 5.75, 2.25, 3.75], [5, 0.25, 3.75, 2.25]]) {
    const from = { x, y: 2 };
    const end = { x: destination, y: 2, kind: 'survey' };
    const opts = { ...config, from, waypoints: [end] };
    assert.deepEqual(repairPath({ ...opts, obstacles: [] }), [end]);
    const detour = repairPath({ ...opts, obstacles: [obstacle] });
    assert.equal(detour[0].x, entry);
    assert.equal(detour[0].y, from.y);
    assert.equal(detour.at(-2).x, exit);
    assert.equal(detour.at(-2).y, from.y);
    assert.deepEqual(detour.at(-1), end);
    assert.ok(detour.some(p => p.y !== from.y));
    assert.ok(detour.every((p, i) => !crossesInterior(detour[i - 1] ?? from, p, box)));
  }
});

test('a second discovery during a detour preserves the safe approach and the original sweep endpoint', () => {
  const first = { cx: 2.5, cy: 2, w: 1, h: 1 };
  const second = { cx: 4.5, cy: 2, w: 0.5, h: 1 };
  const end = { x: 5.75, y: 2, kind: 'survey' };
  const initial = repairPath({ ...config, from: { x: 1, y: 2 }, waypoints: [end], obstacles: [first] });
  const from = initial[1];
  const detour = repairPath({ ...config, from, waypoints: initial.slice(2), obstacles: [first, second] });
  assert.deepEqual(detour.at(-1), end);
  assert.ok(detour.some(p => p.x === 5 && p.y === 2));
  for (const ob of [first, second]) {
    const box = { minX: ob.cx - ob.w / 2 - 0.25, maxX: ob.cx + ob.w / 2 + 0.25,
      minY: ob.cy - ob.h / 2 - 0.25, maxY: ob.cy + ob.h / 2 + 0.25 };
    assert.ok(detour.every((p, i) => !crossesInterior(detour[i - 1] ?? from, p, box)));
  }
});

test('a late obstacle redirects the return leg and still reaches the original landing point', () => {
  const obstacle = { cx: 3, cy: 2, w: 1, h: 1 };
  const from = { x: 5, y: 3 };
  const waypoints = [{ x: 3, y: 2, kind: 'return' },
    { ...config.home, kind: 'return' }, { ...config.home, kind: 'land' }];
  const path = repairPath({ ...config, from, waypoints, obstacles: [obstacle] });
  assert.deepEqual(path.slice(-2), waypoints.slice(-2));
  assert.ok(path.slice(0, -1).every(point => point.kind === 'return'));
  const box = { minX: 2.25, maxX: 3.75, minY: 1.25, maxY: 2.75 };
  assert.ok(path.every((p, i) => !crossesInterior(path[i - 1] ?? from, p, box)));
});

test('an unreachable landing point cannot produce a route', () => {
  const obstacle = { cx: 3, cy: 2, w: 0.5, h: 4 };
  const from = { x: 5, y: 2 };
  const waypoints = [{ ...config.home, kind: 'return' }, { ...config.home, kind: 'land' }];
  assert.equal(repairPath({ ...config, from, waypoints, obstacles: [obstacle] }), null);
});

test('coverage passes start at the current position and return home without restarting the sweep', () => {
  const start = { x: 5, y: 3 };
  const result = plan({ ...config, obstacles: [], cells: [{ x: 4.5, y: 1.5 }], start, sweep: false });
  assert.deepEqual(result.path[0], { ...start, kind: 'transit' });
  assert.ok(result.path.some(point => point.kind === 'fill'));
  assert.ok(result.path.every(point => point.kind !== 'survey'));
  assert.deepEqual(result.path.at(-1), { ...config.home, kind: 'land' });
  assert.equal(result.uncoveredCells, 0);
});
