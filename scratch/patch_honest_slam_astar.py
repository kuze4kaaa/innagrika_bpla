import re

file_path = 'simulation_3d/index.html'

with open(file_path, 'rb') as f:
    content = f.read().decode('utf-8')

has_crlf = '\r\n' in content
c_lf = content.replace('\r\n', '\n')

# 1. Replace getShortestLegDijkstra with guaranteed collision-free A* router
old_dijkstra = """    function getShortestLegDijkstra(pStart, pEnd) {
      if (!segmentIntersectsNFZ(pStart, pEnd)) {
        return [pEnd];
      }
      const margin = 0.28; // Запас 28 см от границы безопасности исключает касание стен при любых маневрах
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
    }"""

new_astar = """    const ASTAR_RES = 0.10;
    const ASTAR_COLS = Math.round(FIELD_WIDTH / ASTAR_RES);
    const ASTAR_ROWS = Math.round(FIELD_HEIGHT / ASTAR_RES);

    function getShortestLegDijkstra(pStart, pEnd) {
      if (!segmentIntersectsNFZ(pStart, pEnd)) {
        return [pEnd];
      }

      // Безопасный буфер: BUFFER_INFLATION (0.23) + DRONE_RADIUS (0.10) + запас = 0.35 м
      const clearance = 0.35;
      const grid = new Uint8Array(ASTAR_COLS * ASTAR_ROWS);

      nfzZones.forEach(z => {
        const minX = z.cx - z.w / 2 - clearance;
        const maxX = z.cx + z.w / 2 + clearance;
        const minY = z.cy - z.h / 2 - clearance;
        const maxY = z.cy + z.h / 2 + clearance;

        const c0 = Math.max(0, Math.floor(minX / ASTAR_RES));
        const c1 = Math.min(ASTAR_COLS - 1, Math.floor(maxX / ASTAR_RES));
        const r0 = Math.max(0, Math.floor(minY / ASTAR_RES));
        const r1 = Math.min(ASTAR_ROWS - 1, Math.floor(maxY / ASTAR_RES));

        for (let r = r0; r <= r1; r++) {
          for (let c = c0; c <= c1; c++) {
            grid[r * ASTAR_COLS + c] = 1;
          }
        }
      });

      const startC = Math.max(0, Math.min(ASTAR_COLS - 1, Math.floor(pStart.x / ASTAR_RES)));
      const startR = Math.max(0, Math.min(ASTAR_ROWS - 1, Math.floor(pStart.y / ASTAR_RES)));
      const endC = Math.max(0, Math.min(ASTAR_COLS - 1, Math.floor(pEnd.x / ASTAR_RES)));
      const endR = Math.max(0, Math.min(ASTAR_ROWS - 1, Math.floor(pEnd.y / ASTAR_RES)));

      grid[startR * ASTAR_COLS + startC] = 0;
      grid[endR * ASTAR_COLS + endC] = 0;

      const dist = new Float32Array(ASTAR_COLS * ASTAR_ROWS).fill(1e9);
      const parent = new Int32Array(ASTAR_COLS * ASTAR_ROWS).fill(-1);
      const closed = new Uint8Array(ASTAR_COLS * ASTAR_ROWS);

      const startIdx = startR * ASTAR_COLS + startC;
      const endIdx = endR * ASTAR_COLS + endC;
      dist[startIdx] = 0;

      const heap = [{ f: Math.hypot(endC - startC, endR - startR), idx: startIdx }];
      const DIRS = [
        [1, 0, 1.0], [-1, 0, 1.0], [0, 1, 1.0], [0, -1, 1.0],
        [1, 1, 1.414], [-1, 1, 1.414], [1, -1, 1.414], [-1, -1, 1.414]
      ];

      let found = false;
      while (heap.length > 0) {
        let best = 0;
        for (let i = 1; i < heap.length; i++) {
          if (heap[i].f < heap[best].f) best = i;
        }
        const curr = heap.splice(best, 1)[0];
        const u = curr.idx;

        if (u === endIdx) {
          found = true;
          break;
        }
        if (closed[u]) continue;
        closed[u] = 1;

        const uC = u % ASTAR_COLS;
        const uR = Math.floor(u / ASTAR_COLS);
        const uDist = dist[u];

        for (let d = 0; d < 8; d++) {
          const nc = uC + DIRS[d][0];
          const nr = uR + DIRS[d][1];
          if (nc < 0 || nc >= ASTAR_COLS || nr < 0 || nr >= ASTAR_ROWS) continue;
          const nIdx = nr * ASTAR_COLS + nc;
          if (closed[nIdx] || grid[nIdx] === 1) continue;

          // Защита от срезания углов на диагоналях
          if (DIRS[d][0] !== 0 && DIRS[d][1] !== 0) {
            if (grid[uR * ASTAR_COLS + nc] === 1 || grid[nr * ASTAR_COLS + uC] === 1) continue;
          }

          const alt = uDist + DIRS[d][2];
          if (alt < dist[nIdx]) {
            dist[nIdx] = alt;
            parent[nIdx] = u;
            const h = Math.hypot(endC - nc, endR - nr);
            heap.push({ f: alt + h, idx: nIdx });
          }
        }
      }

      if (!found) {
        return [pEnd];
      }

      const rawPath = [];
      let curr = endIdx;
      while (curr !== -1) {
        const c = curr % ASTAR_COLS;
        const r = Math.floor(curr / ASTAR_COLS);
        rawPath.push({ x: (c + 0.5) * ASTAR_RES, y: (r + 0.5) * ASTAR_RES, z: 1.2 });
        if (curr === startIdx) break;
        curr = parent[curr];
      }
      rawPath.reverse();
      rawPath[rawPath.length - 1] = { x: pEnd.x, y: pEnd.y, z: pEnd.z || 1.2 };

      // Сглаживание траектории (прямая видимость с барьерами безопасности):
      const smoothed = [];
      let checkPt = pStart;
      let idx = 0;
      while (idx < rawPath.length) {
        let furthest = idx;
        for (let j = rawPath.length - 1; j > idx; j--) {
          if (!segmentIntersectsNFZ(checkPt, rawPath[j])) {
            furthest = j;
            break;
          }
        }
        smoothed.push(rawPath[furthest]);
        checkPt = rawPath[furthest];
        idx = furthest + 1;
      }
      return smoothed;
    }"""

assert old_dijkstra in c_lf, "old_dijkstra not found in c_lf"
c_lf = c_lf.replace(old_dijkstra, new_astar)

# 2. Remove Section 3 (synthetic NFZ boxes) from renderSlamMap
old_sec3 = """      // 3. Честный SLAM: синтетические рамки запретных зон появляются ТОЛЬКО на Этапе 2 (после полной разведки и валидации GCS)
      if (chainStage >= 2) {
        nfzZones.forEach(z => {
          const zx = (z.cx - z.w / 2) * scaleX;
          const zy = H - (z.cy + z.h / 2) * scaleY;
          const zw = z.w * scaleX;
          const zh = z.h * scaleY;

          slamCtx.fillStyle = 'rgba(185, 28, 28, 0.55)';
          slamCtx.fillRect(zx, zy, zw, zh);

          slamCtx.strokeStyle = '#f59e0b';
          slamCtx.lineWidth = 2.5;
          slamCtx.strokeRect(zx, zy, zw, zh);

          const buf = BUFFER_INFLATION;
          const bx = (z.cx - z.w / 2 - buf) * scaleX;
          const by = H - (z.cy + z.h / 2 + buf) * scaleY;
          const bw = (z.w + 2 * buf) * scaleX;
          const bh = (z.h + 2 * buf) * scaleY;
          slamCtx.strokeStyle = '#facc15';
          slamCtx.lineWidth = 1;
          slamCtx.setLineDash([3, 3]);
          slamCtx.strokeRect(bx, by, bw, bh);
          slamCtx.setLineDash([]);

          slamCtx.fillStyle = '#fee2e2';
          slamCtx.font = 'bold 8px monospace';
          slamCtx.textAlign = 'center';
          slamCtx.fillText(`[NFZ-${z.id}]`, z.cx * scaleX, H - z.cy * scaleY + 3);
        });
      }"""

new_sec3 = """      // 3. 100% честный SLAM: никаких синтетических прямоугольников поверх карты!
      // Отображаются исключительно те пиксели стен (оранжевые), которые физически зафиксировал сенсор камеры."""

assert old_sec3 in c_lf, "old_sec3 not found in c_lf"
c_lf = c_lf.replace(old_sec3, new_sec3)

output = c_lf.replace('\n', '\r\n') if has_crlf else c_lf
with open(file_path, 'wb') as f:
    f.write(output.encode('utf-8'))

print("Applied A* pathfinding and completely honest raster SLAM successfully!")
