const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { test } = require('node:test');
const { runInThisContext } = require('node:vm');

const html = readFileSync(join(__dirname, '../simulation_3d/index.html'), 'utf8');
const scripts = ['recon-survey', 'executor-routing'].map(id => {
  const match = html.match(new RegExp(`<script id="${id}">([\\s\\S]*?)<\\/script>`));
  assert.ok(match, `${id} must be bundled with the page`);
  return match[1];
});
const { ExecutorRouting, ReconSurvey } = runInThisContext(
  `(function () {${scripts.join('\n')}\nreturn { ExecutorRouting, ReconSurvey };})()`
);

const field = { width: 6, height: 4, clearance: 0.25 };

function exhaustiveLength(distances, current = 0, remaining = distances.slice(1).map((_, i) => i + 1)) {
  if (!remaining.length) return distances[current][0];
  return Math.min(...remaining.map(next => distances[current][next] +
    exhaustiveLength(distances, next, remaining.filter(i => i !== next))));
}

test('detours are priced into the matrix, and the closed tour matches exhaustive search', () => {
  const obstacle = { cx: 3, cy: 2, w: 1, h: 1.2 };
  const { shortestLeg, expanded } = ReconSurvey.createRouter({ ...field, obstacles: [obstacle] });
  const points = [
    { x: 0.4, y: 2 }, { x: 5.6, y: 2, action: true, targetId: 1 },
    { x: 4.2, y: 1, action: true, targetId: 2 }, { x: 0.8, y: 3, action: true, targetId: 3 },
  ];
  const plan = ExecutorRouting.plan(points, shortestLeg);
  assert.ok(plan.distances[0][1] > 5.2);
  assert.equal(plan.distances[0][1], plan.distances[1][0]);
  assert.ok(Math.abs(plan.length - exhaustiveLength(plan.distances)) < 1e-9);
  assert.equal(plan.order[0], 0);
  assert.equal(plan.order.at(-1), 0);
  const route = plan.routeLegs.flat();
  assert.deepEqual(route.filter(p => p.action).map(p => p.targetId).sort(), [1, 2, 3]);
  let previous = points[0];
  let length = 0;
  for (const point of route) {
    assert.ok(!ReconSurvey.crossesInterior(previous, point, expanded[0]));
    length += Math.hypot(previous.x - point.x, previous.y - point.y);
    previous = point;
  }
  assert.equal(previous, points[0]);
  assert.ok(Math.abs(length - plan.length) < 1e-9);
});

test('a target across an impassable wall prevents a closed tour', () => {
  const obstacles = [{ cx: 3, cy: 2, w: 0.5, h: 4 }];
  const { shortestLeg } = ReconSurvey.createRouter({ ...field, obstacles });
  assert.equal(ExecutorRouting.plan([{ x: 1, y: 2 }, { x: 5, y: 2 }], shortestLeg), null);
});
