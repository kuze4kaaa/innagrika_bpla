const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const test = require('node:test');
const { runInThisContext } = require('node:vm');

const html = readFileSync(join(__dirname, '../simulation_3d/index.html'), 'utf8');
const planner = html.match(/<script id="recon-survey">([\s\S]*?)<\/script>/);
assert.ok(planner, 'the survey planner must be bundled with the page');
const { plan, crossesInterior } = runInThisContext(
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
