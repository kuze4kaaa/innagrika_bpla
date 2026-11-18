
const fs = require('fs');
// Mock THREE and browser globals to run generateBoustrophedonReconPath
const BUFFER_INFLATION = 0.23;
const DRONE_RADIUS = 0.10;
const NFZ_MAX_Z = 2.5;

let nfzZones = [
  { id: 1, cx: 2.5, cy: 2.1, w: 1.2, h: 1.0 },
  { id: 2, cx: 4.4, cy: 1.4, w: 0.8, h: 0.8 }
];

nfzZones.forEach(z => {
  z.barrierMinX = z.cx - (z.w / 2 + BUFFER_INFLATION) - DRONE_RADIUS;
  z.barrierMaxX = z.cx + (z.w / 2 + BUFFER_INFLATION) + DRONE_RADIUS;
  z.barrierMinY = z.cy - (z.h / 2 + BUFFER_INFLATION) - DRONE_RADIUS;
  z.barrierMaxY = z.cy + (z.h / 2 + BUFFER_INFLATION) + DRONE_RADIUS;
});

function segmentIntersectsNFZ(p1, p2) {
      for (let i = 0; i < nfzZones.length; i++) {
        const z = nfzZones[i];
        const dist = Math.hypot(p2.x - p1.x, p2.y - p1.y);
        const steps = Math.max(1, Math.ceil(dist / 0.04));
        for (let s = 1; s < steps; s++) {
          const px = p1.x + (p2.x - p1.x) * (s / steps);
          const py = p1.y + (p2.y - p1.y) * (s / steps);
          if (px > z.barrierMinX && px < z.barrierMaxX && py > z.barrierMinY && py < z.barrierMaxY) {
            return true;
          }
        }
      }
      return false;
    }

    function getShortestLegDijkstra(pStart, pEnd) {
      if (!segmentIntersectsNFZ(pStart, pEnd)) {
        return [pEnd];
      }
      const margin = 0.15;
      const transitNodes = [];
      nfzZones.forEach(z => {
        transitNodes.push({ x: z.barrierMinX - margin, y: z.barrierMinY - margin, z: 1.2 });
        transitNodes.push({ x: z.barrierMaxX + margin, y: z.barrierMinY - margin, z: 1.2 });
        transitNodes.push({ x: z.barrierMinX - margin, y: z.barrierMaxY + margin, z: 1.2 });
        transitNodes.push({ x: z.barrierMaxX + margin, y: z.barrierMaxY + margin, z: 1.2 });
      });

      const allNodes = [pStart, ...transitNodes, pEnd];
      const startIdx = 0;
      const endIdx = allNodes.length - 1;

      const adj = Array.from({ length: allNodes.length }, () => []);
      for (let i = 0; i < allNodes.length; i++) {
        for (let j = i + 1; j < allNodes.length; j++) {
          if (!segmentIntersectsNFZ(allNodes[i], allNodes[j])) {
            const d = Math.hypot(allNodes[i].x - allNodes[j].x, allNodes[i].y - allNodes[j].y);
            adj[i].push({ to: j, weight: d });
            adj[j].push({ to: i, weight: d });
          }
        }
      }

      const dist = new Array(allNodes.length).fill(Infinity);
      const prev = new Array(allNodes.length).fill(-1);
      const visited = new Array(allNodes.length).fill(false);
      dist[startIdx] = 0;

      for (let step = 0; step < allNodes.length; step++) {
        let u = -1;
        let minD = Infinity;
        for (let i = 0; i < allNodes.length; i++) {
          if (!visited[i] && dist[i] < minD) {
            minD = dist[i];
            u = i;
          }
        }
        if (u === -1 || u === endIdx) break;
        visited[u] = true;

        for (const edge of adj[u]) {
          if (!visited[edge.to] && dist[u] + edge.weight < dist[edge.to]) {
            dist[edge.to] = dist[u] + edge.weight;
            prev[edge.to] = u;
          }
        }
      }

      if (dist[endIdx] === Infinity) return [pEnd];

      const leg = [];
      let curr = endIdx;
      while (curr !== startIdx) {
        leg.push({ x: allNodes[curr].x, y: allNodes[curr].y, z: 1.2 });
        curr = prev[curr];
      }
      leg.reverse();
      return leg;
    }

    // --- ГЕНЕРАТОР ПАРАЛЛЕЛЬНЫХ ГАЛСОВ РАЗВЕДЧИКА С ОНЛАЙН-ОБХОДОМ НЕИЗВЕСТНЫХ ПРЕПЯТСТВИЙ ---
    // Дрон изначально летит по чистым параллельным прямым (Lawnmower Swaths) без знания о препятствиях,
    // а при физическом обнаружении стены на траектории — динамически обходит её по контуру!
    function generateBoustrophedonReconPath() {
      // Чистые параллельные галсы (полное неведение БПЛА о расположении NFZ):
      const blindSwaths = [
        { x: 0.40, y: 0.40, z: 1.2 }, // Взлет с Home-1
        // Галс 1 (Южная полоса, движение на Восток):
        { x: 0.60, y: 0.45, z: 1.2 },
        { x: 5.48, y: 0.45, z: 1.2 },
        // Разворот на полосу 2:
        { x: 5.48, y: 1.25, z: 1.2 },
        // Галс 2 (движение на Запад):
        { x: 0.60, y: 1.25, z: 1.2 },
        // Разворот на полосу 3:
        { x: 0.60, y: 2.05, z: 1.2 },
        // Галс 3 (движение на Восток):
        { x: 5.48, y: 2.05, z: 1.2 },
        // Разворот на полосу 4:
        { x: 5.48, y: 2.85, z: 1.2 },
        // Галс 4 (движение на Запад):
        { x: 0.60, y: 2.85, z: 1.2 },
        // Разворот на полосу 5:
        { x: 0.60, y: 3.55, z: 1.2 },
        // Галс 5 (Северная полоса, движение на Восток):
        { x: 5.48, y: 3.55, z: 1.2 },
        // Возврат на базу:
        { x: 0.40, y: 3.55, z: 1.2 },
        { x: 0.40, y: 0.40, z: 1.2 },
        { x: 0.40, y: 0.40, z: 0.08 }
      ];

      // Реактивная трансляция: если прямая между параллельными галсами упирается в стену,
      // вставляются точки обхода препятствия по безопасному внешнему контуру:
      const fullPath = [blindSwaths[0]];
      for (let i = 0; i < blindSwaths.length - 1; i++) {
        const pStart = fullPath[fullPath.length - 1];
        const pEnd = blindSwaths[i + 1];
        const leg = getShortestLegDijkstra(pStart, pEnd);
        for (const pt of leg) {
          fullPath.push(pt);
        }
      }
      return fullPath;
    }
    let plannedReconWaypoints = generateBoustrophedonReconPath();

    
const wps = generateBoustrophedonReconPath();
console.log('Waypoints count:', wps.length);
wps.forEach((wp, i) => console.log(i, wp.x.toFixed(2), wp.y.toFixed(2)));
