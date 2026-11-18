# -*- coding: utf-8 -*-
with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add SLAM grid and Motor Mixer state variables after 'let targetsData = [];'
target_var_anchor = 'let targetsData = [];\n    let targetMeshes = [];'
slam_and_motors_vars = '''let targetsData = [];
    let targetMeshes = [];

    // --- 2D SLAM Occupancy Grid (60 x 40 клеток по 0.1 м) ---
    const SLAM_COLS = 60;
    const SLAM_ROWS = 40;
    const SLAM_RES = 0.1; // 10 см на клетку (полигон 6.0 x 4.0 м)
    // 0: Неотсканировано (туман), 1: Свободно, 2: Стена, 3: Внутри фигуры стен (сплошная преграда)
    const slamGrid = new Uint8Array(SLAM_COLS * SLAM_ROWS);
    let slamCoverage = 0.0;
    let slamWallsCount = 0;
    let totalReachableCells = 0;

    // Расчет достижимых клеток поля (без внутренних объемов NFZ)
    for (let c = 0; c < SLAM_COLS; c++) {
      const cx = (c + 0.5) * SLAM_RES;
      for (let r = 0; r < SLAM_ROWS; r++) {
        const cy = (r + 0.5) * SLAM_RES;
        let insideNfz = false;
        nfzZones.forEach(z => {
          if (cx >= (z.cx - z.w/2) && cx <= (z.cx + z.w/2) &&
              cy >= (z.cy - z.h/2) && cy <= (z.cy + z.h/2)) {
            insideNfz = true;
          }
        });
        if (!insideNfz) totalReachableCells++;
      }
    }

    // --- Переключаемый режим управления: Полетник (WASD) vs Моторы (RPM Mixer) ---
    let controlMode = 'flight_controller'; // 'flight_controller' | 'motor_mixer'
    const motorRPM = [0, 0, 0, 0]; // M1..M4 в процентах 0..100%
'''

text = text.replace(target_var_anchor, slam_and_motors_vars, 1)

# 2. Add SLAM scan & 2D Canvas rendering functions
slam_funcs = '''
    // Функция сканирования сенсором камеры и заполнения SLAM-карты
    function updateSlamScan(px, py, pz) {
      if (pz < 0.20) return;
      const scanR = 0.95; // Радиус обзора камеры (угол 70° на высоте 1.2 м)
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
              const onBorderX = (Math.abs(cx - xMin) < 0.12 || Math.abs(cx - xMax) < 0.12) && (cy >= yMin - 0.05 && cy <= yMax + 0.05);
              const onBorderY = (Math.abs(cy - yMin) < 0.12 || Math.abs(cy - yMax) < 0.12) && (cx >= xMin - 0.05 && cx <= xMax + 0.05);

              if (onBorderX || onBorderY) {
                isWall = true;
              } else if (cx > xMin && cx < xMax && cy > yMin && cy < yMax) {
                // ТЗ: если найдена фигура из стен, внутри тоже считается стеной!
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
                slamGrid[idx] = 1;
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
      slamCtx.fillStyle = '#080d19';
      slamCtx.fillRect(0, 0, W, H);

      // 2. Отрисовка клеток Occupancy Grid
      const cellW = W / SLAM_COLS;
      const cellH = H / SLAM_ROWS;

      for (let c = 0; c < SLAM_COLS; c++) {
        for (let r = 0; r < SLAM_ROWS; r++) {
          const val = slamGrid[r * SLAM_COLS + c];
          const px = c * cellW;
          const py = H - (r + 1) * cellH; // Инвертируем Y для совпадения с миром

          if (val === 1) {
            slamCtx.fillStyle = '#14382b'; // Просканированная свободная зона
            slamCtx.fillRect(px, py, cellW + 0.5, cellH + 0.5);
          } else if (val === 2) {
            slamCtx.fillStyle = '#f59e0b'; // Обнаруженная стена
            slamCtx.fillRect(px, py, cellW + 0.5, cellH + 0.5);
          } else if (val === 3) {
            slamCtx.fillStyle = '#7f1d1d'; // Заполненный внутренний объем фигуры из стен
            slamCtx.fillRect(px, py, cellW + 0.5, cellH + 0.5);
          } else {
            // Легкая сетка тумана
            if (c % 5 === 0 && r % 5 === 0) {
              slamCtx.fillStyle = '#1e293b';
              slamCtx.fillRect(px, py, 1.5, 1.5);
            }
          }
        }
      }

      // 3. Подписи зон стен
      slamCtx.fillStyle = '#fca5a5';
      slamCtx.font = '8px monospace';
      slamCtx.textAlign = 'center';
      nfzZones.forEach(z => {
        const zx = z.cx * scaleX;
        const zy = H - z.cy * scaleY;
        slamCtx.fillText(`[СТЕНА ${z.id}]`, zx, zy);
      });

      // 4. Посадочные площадки Home
      // Home-1 (0.4, 0.4)
      slamCtx.strokeStyle = '#ea580c';
      slamCtx.lineWidth = 2;
      slamCtx.beginPath();
      slamCtx.arc(0.4 * scaleX, H - 0.4 * scaleY, 7, 0, Math.PI * 2);
      slamCtx.stroke();
      slamCtx.fillStyle = '#ea580c';
      slamCtx.font = '7px sans-serif';
      slamCtx.fillText('H1', 0.4 * scaleX, H - 0.4 * scaleY + 2.5);

      // Home-2 (0.4, 1.2)
      slamCtx.strokeStyle = '#22c55e';
      slamCtx.lineWidth = 2;
      slamCtx.beginPath();
      slamCtx.arc(0.4 * scaleX, H - 1.2 * scaleY, 7, 0, Math.PI * 2);
      slamCtx.stroke();
      slamCtx.fillStyle = '#22c55e';
      slamCtx.fillText('H2', 0.4 * scaleX, H - 1.2 * scaleY + 2.5);

      // 5. Обнаруженные цели
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
          slamCtx.arc(tx, ty, 4, 0, Math.PI * 2);
          slamCtx.fill();

          slamCtx.fillStyle = '#ffffff';
          slamCtx.font = 'bold 7px sans-serif';
          slamCtx.fillText(t.type === 'A_NFZ' ? 'X' : t.type, tx, ty + 2.5);
        }
      });

      // 6. Позиции дронов на 2D-карте
      [drone2State, drone1State].forEach(dr => {
        const dx = dr.x * scaleX;
        const dy = H - dr.y * scaleY;
        const isRecon = (dr.role === 'recon');
        const color = isRecon ? '#ea580c' : '#22c55e';

        // Корпус БПЛА
        slamCtx.fillStyle = color;
        slamCtx.beginPath();
        slamCtx.arc(dx, dy, 5, 0, Math.PI * 2);
        slamCtx.fill();

        // Стрелка курса (Yaw)
        slamCtx.strokeStyle = '#ffffff';
        slamCtx.lineWidth = 1.5;
        slamCtx.beginPath();
        slamCtx.moveTo(dx, dy);
        slamCtx.lineTo(dx + Math.cos(dr.yaw) * 10, dy - Math.sin(dr.yaw) * 10);
        slamCtx.stroke();
      });
    }
'''

# Insert slam_funcs before 'function generateRandomTargets()'
text = text.replace('function generateRandomTargets() {', slam_funcs + '\n    function generateRandomTargets() {', 1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Inserted SLAM grid and functions!')
