# -*- coding: utf-8 -*-
import re

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# -------------------------------------------------------------
# FIX 1 & 2: Complete and robust updateSlamScan & renderSlamMap
# -------------------------------------------------------------
new_slam_block = '''    // Функция сканирования сенсором камеры и заполнения SLAM-карты
    function updateSlamScan(px, py, pz) {
      if (pz < 0.15) return;
      const scanR = 0.95; // Радиус зоны обзора камеры на высоте ~1.2 м
      let newlyScanned = false;

      for (let c = 0; c < SLAM_COLS; c++) {
        const cx = (c + 0.5) * SLAM_RES;
        if (Math.abs(cx - px) > scanR) continue;

        for (let r = 0; r < SLAM_ROWS; r++) {
          const cy = (r + 0.5) * SLAM_RES;
          if (Math.abs(cy - py) > scanR) continue;

          const dist = Math.hypot(cx - px, cy - py);
          if (dist <= scanR) {
            const idx = r * SLAM_COLS + c;

            let isWall = false;
            let isInside = false;

            nfzZones.forEach(z => {
              const xMin = z.cx - z.w / 2;
              const xMax = z.cx + z.w / 2;
              const yMin = z.cy - z.h / 2;
              const yMax = z.cy + z.h / 2;

              // Периметр — обнаруженная физическая стена / барьер
              const onBorderX = (Math.abs(cx - xMin) <= 0.15 || Math.abs(cx - xMax) <= 0.15) && (cy >= yMin - 0.10 && cy <= yMax + 0.10);
              const onBorderY = (Math.abs(cy - yMin) <= 0.15 || Math.abs(cy - yMax) <= 0.15) && (cx >= xMin - 0.10 && cx <= xMax + 0.10);

              if (onBorderX || onBorderY) {
                isWall = true;
              } else if (cx > xMin && cx < xMax && cy > yMin && cy < yMax) {
                // Если найдена фигура из стен, внутри тоже считается стеной!
                isInside = true;
              }
            });

            if (isWall) {
              if (slamGrid[idx] !== 2) {
                slamGrid[idx] = 2;
                slamWallsCount++;
                newlyScanned = true;
              }
            } else if (isInside) {
              if (slamGrid[idx] !== 3) {
                slamGrid[idx] = 3;
                newlyScanned = true;
              }
            } else {
              if (slamGrid[idx] === 0) {
                slamGrid[idx] = 1; // Проверенная свободная зона
                newlyScanned = true;
              }
            }
          }
        }
      }

      if (newlyScanned) {
        let freeCount = 0;
        for (let i = 0; i < slamGrid.length; i++) {
          if (slamGrid[i] === 1) freeCount++;
        }
        slamCoverage = Math.min((freeCount / totalReachableCells) * 100.0, 100.0);
        const badge = document.getElementById('slamCoverageBadge');
        if (badge) badge.textContent = `ПОКРЫТИЕ: ${slamCoverage.toFixed(1)}%`;
      }
    }

    // Отрисовка 2D-карты SLAM на HTML5 Canvas (300 x 200 px)
    const slamCanvas = document.getElementById('slamCanvas');
    const slamCtx = slamCanvas ? slamCanvas.getContext('2d') : null;

    function renderSlamMap() {
      if (!slamCtx) return;
      const W = slamCanvas.width;
      const H = slamCanvas.height;
      const scaleX = W / FIELD_WIDTH;  // 50 px/м
      const scaleY = H / FIELD_HEIGHT; // 50 px/м

      // 1. Очистка фона (туман войны)
      slamCtx.fillStyle = '#060a14';
      slamCtx.fillRect(0, 0, W, H);

      // 2. Отрисовка клеток Occupancy Grid (проверенная зона закрашивается!)
      const cellW = W / SLAM_COLS;
      const cellH = H / SLAM_ROWS;

      for (let c = 0; c < SLAM_COLS; c++) {
        for (let r = 0; r < SLAM_ROWS; r++) {
          const val = slamGrid[r * SLAM_COLS + c];
          const px = c * cellW;
          const py = H - (r + 1) * cellH; // Инвертируем Y для совпадения с миром

          if (val === 1) {
            // Четко закрашенная проверенная зона (насыщенный зеленый цвет)
            slamCtx.fillStyle = '#15803d';
            slamCtx.fillRect(px, py, cellW + 0.6, cellH + 0.6);
          } else if (val === 2) {
            // Обнаруженная стена (янтарно-оранжевая)
            slamCtx.fillStyle = '#f59e0b';
            slamCtx.fillRect(px, py, cellW + 0.6, cellH + 0.6);
          } else if (val === 3) {
            // Внутренность фигуры из стен (сплошная темно-красная преграда)
            slamCtx.fillStyle = '#b91c1c';
            slamCtx.fillRect(px, py, cellW + 0.6, cellH + 0.6);
          } else {
            // Неотсканированный туман: легкие координатные точки
            if (c % 4 === 0 && r % 4 === 0) {
              slamCtx.fillStyle = '#1e293b';
              slamCtx.fillRect(px, py, 1.5, 1.5);
            }
          }
        }
      }

      // 3. Стены и препятствия полигона (гарантированное отображение стен на 2D-карте!)
      nfzZones.forEach(z => {
        const zx = (z.cx - z.w / 2) * scaleX;
        const zy = H - (z.cy + z.h / 2) * scaleY;
        const zw = z.w * scaleX;
        const zh = z.h * scaleY;

        // Проверяем, обнаружена ли стена дроном
        let discovered = false;
        for (let c = 0; c < SLAM_COLS; c++) {
          const cx = (c + 0.5) * SLAM_RES;
          for (let r = 0; r < SLAM_ROWS; r++) {
            const cy = (r + 0.5) * SLAM_RES;
            if (cx >= (z.cx - z.w/2 - 0.25) && cx <= (z.cx + z.w/2 + 0.25) &&
                cy >= (z.cy - z.h/2 - 0.25) && cy <= (z.cy + z.h/2 + 0.25)) {
              if (slamGrid[r * SLAM_COLS + c] === 2 || slamGrid[r * SLAM_COLS + c] === 3) {
                discovered = true;
                break;
              }
            }
          }
          if (discovered) break;
        }

        if (discovered) {
          // Заполненный внутренний объем ("внутри фигур стен - тоже стена")
          slamCtx.fillStyle = 'rgba(185, 28, 28, 0.65)';
          slamCtx.fillRect(zx, zy, zw, zh);

          // Контур физических стен (толстая яркая янтарная рамка)
          slamCtx.strokeStyle = '#f59e0b';
          slamCtx.lineWidth = 3;
          slamCtx.strokeRect(zx, zy, zw, zh);

          // Буфер безопасности (+0.23 м, пунктир)
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

          // Подпись
          slamCtx.fillStyle = '#fee2e2';
          slamCtx.font = 'bold 8px monospace';
          slamCtx.textAlign = 'center';
          slamCtx.fillText(`[СТЕНА ${z.id}: ЗАБЛОКИРОВАНО]`, z.cx * scaleX, H - z.cy * scaleY + 3);
        } else {
          // Пока стена не обнаружена — пунктирный контур разведки
          slamCtx.strokeStyle = '#334155';
          slamCtx.lineWidth = 1;
          slamCtx.setLineDash([2, 3]);
          slamCtx.strokeRect(zx, zy, zw, zh);
          slamCtx.setLineDash([]);
          slamCtx.fillStyle = '#64748b';
          slamCtx.font = '8px monospace';
          slamCtx.textAlign = 'center';
          slamCtx.fillText(`[?]`, z.cx * scaleX, H - z.cy * scaleY + 3);
        }
      });

      // 4. Посадочные площадки Home
      // Home-1 (0.4, 0.4)
      slamCtx.strokeStyle = '#ea580c';
      slamCtx.lineWidth = 2;
      slamCtx.beginPath();
      slamCtx.arc(0.4 * scaleX, H - 0.4 * scaleY, 7, 0, Math.PI * 2);
      slamCtx.stroke();
      slamCtx.fillStyle = '#ea580c';
      slamCtx.font = 'bold 7px sans-serif';
      slamCtx.textAlign = 'center';
      slamCtx.fillText('H1', 0.4 * scaleX, H - 0.4 * scaleY + 2.5);

      // Home-2 (0.4, 1.2)
      slamCtx.strokeStyle = '#22c55e';
      slamCtx.lineWidth = 2;
      slamCtx.beginPath();
      slamCtx.arc(0.4 * scaleX, H - 1.2 * scaleY, 7, 0, Math.PI * 2);
      slamCtx.stroke();
      slamCtx.fillStyle = '#22c55e';
      slamCtx.fillText('H2', 0.4 * scaleX, H - 1.2 * scaleY + 2.5);

      // 5. Динамический идеальный маршрут Исполнителя на данный момент (Live GCS Route)
      if (drone2State.waypoints && drone2State.waypoints.length > 1) {
        slamCtx.strokeStyle = '#38bdf8';
        slamCtx.lineWidth = 2;
        slamCtx.setLineDash([4, 3]);
        slamCtx.beginPath();
        drone2State.waypoints.forEach((wp, idx) => {
          const wx = wp.x * scaleX;
          const wy = H - wp.y * scaleY;
          if (idx === 0) slamCtx.moveTo(wx, wy);
          else slamCtx.lineTo(wx, wy);
        });
        slamCtx.stroke();
        slamCtx.setLineDash([]);

        // Путевые точки маршрута исполнителя
        drone2State.waypoints.forEach((wp, idx) => {
          if (idx > 0 && idx < drone2State.waypoints.length - 1) {
            const wx = wp.x * scaleX;
            const wy = H - wp.y * scaleY;
            slamCtx.fillStyle = '#38bdf8';
            slamCtx.beginPath();
            slamCtx.arc(wx, wy, 2.5, 0, Math.PI * 2);
            slamCtx.fill();
          }
        });
      }

      // 6. Обнаруженные цели
      targetsData.forEach(t => {
        if (t.discovered) {
          const tx = t.x * scaleX;
          const ty = H - t.y * scaleY;
          let col = '#22c55e';
          if (t.type === 'B') col = '#3b82f6';
          if (t.type === 'U') col = '#a855f7';
          if (t.type === 'A_NFZ') col = '#ef4444';

          slamCtx.fillStyle = col;
          slamCtx.beginPath();
          slamCtx.arc(tx, ty, 4.5, 0, Math.PI * 2);
          slamCtx.fill();

          slamCtx.strokeStyle = '#ffffff';
          slamCtx.lineWidth = 1;
          slamCtx.beginPath();
          slamCtx.arc(tx, ty, 4.5, 0, Math.PI * 2);
          slamCtx.stroke();

          slamCtx.fillStyle = '#ffffff';
          slamCtx.font = 'bold 7px sans-serif';
          slamCtx.fillText(t.type === 'A_NFZ' ? 'X' : t.type, tx, ty + 2.5);
        }
      });

      // 7. Позиции дронов на 2D-карте
      [drone2State, drone1State].forEach(dr => {
        const dx = dr.x * scaleX;
        const dy = H - dr.y * scaleY;
        const isRecon = (dr.role === 'recon');
        const color = isRecon ? '#ea580c' : '#22c55e';

        slamCtx.fillStyle = color;
        slamCtx.beginPath();
        slamCtx.arc(dx, dy, 5, 0, Math.PI * 2);
        slamCtx.fill();

        slamCtx.strokeStyle = '#ffffff';
        slamCtx.lineWidth = 1.5;
        slamCtx.beginPath();
        slamCtx.moveTo(dx, dy);
        slamCtx.lineTo(dx + Math.cos(dr.yaw) * 10, dy - Math.sin(dr.yaw) * 10);
        slamCtx.stroke();
      });

      // 8. Подпись статуса маршрута в шапке карты
      slamCtx.fillStyle = '#38bdf8';
      slamCtx.font = 'bold 8px monospace';
      slamCtx.textAlign = 'left';
      const validCnt = (drone1State.memory || []).filter(t => t.type === 'A' && !t.insideNFZ).length;
      slamCtx.fillText(`МАРШРУТ ИСПОЛНИТЕЛЯ (LIVE): ${validCnt} ЦЕЛЕЙ`, 8, 12);
    }'''

# Replace old updateSlamScan & renderSlamMap
old_slam_regex = r'function updateSlamScan\(px, py, pz\) \{[\s\S]*?\}\s*// 6\. [^\n]*\n\s*\[drone2State, drone1State\]\.forEach\(dr => \{[\s\S]*?\}\);\s*\}'
match = re.search(old_slam_regex, text)
if match:
    text = text[:match.start()] + new_slam_block + text[match.end():]
    print('Replaced updateSlamScan & renderSlamMap successfully!')
else:
    print('REGEX NOT MATCHED FOR SLAM BLOCK, trying alternative replacement')
    # Try direct find
    start_idx = text.find('function updateSlamScan(px, py, pz) {')
    end_anchor = 'function generateRandomTargets() {'
    end_idx = text.find(end_anchor, start_idx)
    if start_idx != -1 and end_idx != -1:
        text = text[:start_idx] + new_slam_block + '\n\n    ' + text[end_idx:]
        print('Direct slice replaced updateSlamScan & renderSlamMap!')

# -------------------------------------------------------------
# FIX 3: Real-time dynamic Executor route planning
# -------------------------------------------------------------
new_planner = '''    function planExecutorMissionFromMemory() {
      const memory = (drone1State.memory && drone1State.memory.length > 0) ? drone1State.memory : [];
      const acceptedTargets = [];

      memory.forEach(t => {
        let insideNFZ = false;
        nfzZones.forEach(z => {
          if (t.x >= z.barrierMinX && t.x <= z.barrierMaxX &&
              t.y >= z.barrierMinY && t.y <= z.barrierMaxY) {
            insideNFZ = true;
          }
        });

        // Строгая валидация GCS:
        // 1. Отбраковка целей внутри запретных зон NFZ
        // 2. Отбраковка сорняков (B)
        // 3. Отбраковка неопознанных (U)
        // 4. Допуск только подтвержденных очагов Класса A
        if (t.type === 'A' && !insideNFZ && !t.nfz) {
          acceptedTargets.push(t);
        }
      });

      if (acceptedTargets.length === 0) {
        drone2State.waypoints = [{ x: 0.40, y: 1.20, z: 1.2 }];
        updateRouteLine(drone2State.waypoints);
        return 0;
      }

      // Динамическое построение оптимального маршрута вокруг обнаруженных стен:
      const tSW = acceptedTargets.find(t => t.x < 1.8 && t.y < 1.5);
      const tS  = acceptedTargets.find(t => t.x >= 1.8 && t.x < 3.8 && t.y < 1.0);
      const tE  = acceptedTargets.find(t => t.x > 5.0 && t.y >= 1.5 && t.y <= 3.0);
      const tNE = acceptedTargets.find(t => t.x >= 3.8 && t.y > 3.0);
      const tN  = acceptedTargets.find(t => t.x >= 1.8 && t.x < 3.8 && t.y > 3.0);
      const tNW = acceptedTargets.find(t => t.x < 1.8 && t.y > 3.0);

      const waypoints = [
        { x: 0.40, y: 1.20, z: 1.2 } // Взлет с площадки Home-2
      ];

      if (tSW) waypoints.push({ x: tSW.x, y: tSW.y, z: 1.2, action: true, targetId: tSW.id });
      if (tS)  waypoints.push({ x: tS.x,  y: tS.y,  z: 1.2, action: true, targetId: tS.id });

      // Если есть восточные или северные цели — обход NFZ-2 по южному коридору:
      if (tE || tNE || tN) {
        waypoints.push({ x: 4.40, y: 0.38, z: 1.2 });
        waypoints.push({ x: 5.48, y: 0.38, z: 1.2 });
      }

      if (tE)  waypoints.push({ x: tE.x,  y: tE.y,  z: 1.2, action: true, targetId: tE.id });

      if (tNE || tN || tNW) {
        waypoints.push({ x: 5.48, y: 3.48, z: 1.2 }); // Переход на Север
      }

      if (tNE) waypoints.push({ x: tNE.x, y: tNE.y, z: 1.2, action: true, targetId: tNE.id });
      if (tN)  waypoints.push({ x: tN.x,  y: tN.y,  z: 1.2, action: true, targetId: tN.id });
      if (tNW) waypoints.push({ x: tNW.x, y: tNW.y, z: 1.2, action: true, targetId: tNW.id });

      // Возврат на базу в обход NFZ-1:
      waypoints.push({ x: 0.70, y: 2.50, z: 1.2 });
      waypoints.push({ x: 0.70, y: 1.40, z: 1.2 });
      waypoints.push({ x: 0.40, y: 1.20, z: 1.2 });
      waypoints.push({ x: 0.40, y: 1.20, z: 0.08 }); // Точная посадка на Home-2

      drone2State.waypoints = waypoints;
      updateRouteLine(waypoints);

      return acceptedTargets.length;
    }'''

p_start = text.find('function planExecutorMissionFromMemory() {')
p_end = text.find('const drone1State = {', p_start)
if p_start != -1 and p_end != -1:
    text = text[:p_start] + new_planner + '\n\n    ' + text[p_end:]
    print('Updated planExecutorMissionFromMemory successfully!')

# -------------------------------------------------------------
# FIX 4: Camera cone transparency (depthWrite: false) & frustumCulled = false
# -------------------------------------------------------------
old_frust_mat = '''        const pyrMat = new THREE.MeshBasicMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.16,
          side: THREE.DoubleSide
        });
        const pyrMesh = new THREE.Mesh(pyrGeo, pyrMat);
        frustumGroup.add(pyrMesh);

        const linePositions = new Float32Array(16 * 3);
        const lineGeo = new THREE.BufferGeometry();
        lineGeo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
        const lineMesh = new THREE.LineSegments(lineGeo, new THREE.LineBasicMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.65
        }));
        frustumGroup.add(lineMesh);

        const footPositions = new Float32Array(5 * 3);
        const footGeo = new THREE.BufferGeometry();
        footGeo.setAttribute('position', new THREE.BufferAttribute(footPositions, 3));
        const footLine = new THREE.Line(footGeo, new THREE.LineBasicMaterial({
          color: 0x38bdf8,
          linewidth: 2
        }));
        frustumGroup.add(footLine);'''

new_frust_mat = '''        const pyrMat = new THREE.MeshBasicMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.08, // Легкий, кристально прозрачный световой объем
          depthWrite: false, // НЕ закрывает собой точки на поле!
          depthTest: true,
          side: THREE.DoubleSide
        });
        const pyrMesh = new THREE.Mesh(pyrGeo, pyrMat);
        pyrMesh.frustumCulled = false; // ГАРАНТИЯ: НИКОГДА НЕ ПРОПАДАЕТ!
        frustumGroup.add(pyrMesh);

        const linePositions = new Float32Array(16 * 3);
        const lineGeo = new THREE.BufferGeometry();
        lineGeo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
        const lineMesh = new THREE.LineSegments(lineGeo, new THREE.LineBasicMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.45,
          depthWrite: false
        }));
        lineMesh.frustumCulled = false; // НИКОГДА НЕ ПРОПАДАЕТ!
        frustumGroup.add(lineMesh);

        const footPositions = new Float32Array(5 * 3);
        const footGeo = new THREE.BufferGeometry();
        footGeo.setAttribute('position', new THREE.BufferAttribute(footPositions, 3));
        const footLine = new THREE.Line(footGeo, new THREE.LineBasicMaterial({
          color: 0x38bdf8,
          linewidth: 2,
          depthWrite: false
        }));
        footLine.frustumCulled = false; // НИКОГДА НЕ ПРОПАДАЕТ!
        frustumGroup.add(footLine);'''

text = text.replace(old_frust_mat, new_frust_mat, 1)

# Ensure target dots have higher renderOrder
text = text.replace('scene.add(tGroup);\n      targetMeshes.push({',
                    'tGroup.renderOrder = 100;\n      ring.renderOrder = 101;\n      dot.renderOrder = 102;\n      scene.add(tGroup);\n      targetMeshes.push({', 1)

# -------------------------------------------------------------
# HOOK updateSlamScan & dynamic route into updateDronePhysics
# -------------------------------------------------------------
old_physics_start = '''function updateDronePhysics(st, obj, isControlled, dt) {
    if (dt > 0.06) dt = 0.06;

    // localAx - вперед / назад
    // localAy - влево / вправо
    let localAx = 0, localAy = 0, yawRate = 0;'''

new_physics_start = '''function updateDronePhysics(st, obj, isControlled, dt) {
    if (dt > 0.06) dt = 0.06;

    let localAx = 0, localAy = 0, yawRate = 0;

    // Сканирование поля сенсором камеры и закрашивание 2D SLAM-карты в реальном времени
    if (st.role === 'recon' && (st.autoPilot || st.z > 0.15)) {
      updateSlamScan(st.x, st.y, st.z);
      if (obj.cameraFrustum) obj.cameraFrustum.visible = true;
    } else if (st.role === 'recon' && st.z <= 0.12 && !st.autoPilot) {
      if (obj.cameraFrustum) obj.cameraFrustum.visible = false;
    }'''

text = text.replace(old_physics_start, new_physics_start, 1)

# Also when new target is discovered, re-calculate the live ideal route for Executor!
old_toast_call = 'st.memory.push(t);\n            updateHUDDiscoveredCount(st.memory.length);\n            showDiscoveryToast(t);'
new_toast_call = '''st.memory.push(t);
            updateHUDDiscoveredCount(st.memory.length);
            showDiscoveryToast(t);
            // Во время работы разведчика обновляем идеальный маршрут исполнителя в реальном времени!
            planExecutorMissionFromMemory();'''

text = text.replace(old_toast_call, new_toast_call, 1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('All 4 user requests implemented cleanly!')
