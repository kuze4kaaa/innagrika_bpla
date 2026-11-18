# -*- coding: utf-8 -*-
import sys

with open('simulation_3d/index.html.bak', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. CSS to insert before </style>
css_extra = """
    /* --- 2D SLAM Minimap Card --- */
    .slam-map-card {
      position: absolute;
      bottom: 74px;
      left: 14px;
      width: 324px;
      background: rgba(15, 23, 42, 0.94);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(56, 189, 248, 0.35);
      border-radius: 10px;
      padding: 10px 12px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.65);
      z-index: 15;
      user-select: none;
      transition: opacity 0.2s ease;
    }
    .slam-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .slam-title {
      font-size: 11px;
      font-weight: 700;
      color: #38bdf8;
      letter-spacing: 0.5px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .slam-pulse {
      display: inline-block;
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #22c55e;
      box-shadow: 0 0 8px #22c55e;
      animation: pulseAnim 1.5s infinite;
    }
    @keyframes pulseAnim {
      0% { opacity: 0.4; }
      50% { opacity: 1; }
      100% { opacity: 0.4; }
    }
    .slam-badge {
      font-size: 10px;
      font-weight: 700;
      color: #4ade80;
      background: rgba(34, 197, 94, 0.15);
      padding: 2px 7px;
      border-radius: 4px;
      border: 1px solid rgba(74, 222, 128, 0.3);
      font-family: monospace;
    }
    .slam-canvas-wrap {
      width: 300px;
      height: 200px;
      background: #080d19;
      border: 1px solid #1e293b;
      border-radius: 6px;
      overflow: hidden;
      position: relative;
    }
    #slamCanvas {
      width: 300px;
      height: 200px;
      display: block;
    }
    .slam-legend {
      display: flex;
      justify-content: space-between;
      margin-top: 6px;
      font-size: 9px;
      color: #94a3b8;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 3px;
    }
    .legend-box {
      width: 8px;
      height: 8px;
      border-radius: 2px;
      display: inline-block;
    }
    .legend-box.unscanned { background: #0b1329; border: 1px solid #334155; }
    .legend-box.scanned { background: #15803d; }
    .legend-box.wall { background: #f59e0b; }
    .legend-box.inside-nfz { background: #b91c1c; }

    /* --- Motor Control RPM Panel --- */
    .motor-panel {
      position: absolute;
      bottom: 74px;
      right: 14px;
      width: 334px;
      background: rgba(15, 23, 42, 0.94);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(234, 88, 12, 0.45);
      border-radius: 10px;
      padding: 10px 14px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.65);
      z-index: 15;
      display: none;
      user-select: none;
    }
    .motor-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .motor-title {
      font-size: 11px;
      font-weight: 700;
      color: #fb923c;
      letter-spacing: 0.4px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .motor-close {
      cursor: pointer;
      color: #94a3b8;
      font-size: 16px;
      line-height: 1;
    }
    .motor-close:hover { color: #fff; }
    .motor-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 5px;
      font-size: 11px;
      gap: 6px;
    }
    .motor-label {
      width: 110px;
      font-size: 10px;
      font-weight: 600;
    }
    .motor-slider {
      flex: 1;
      height: 5px;
      accent-color: #ea580c;
      cursor: pointer;
    }
    .motor-val {
      width: 82px;
      text-align: right;
      font-family: monospace;
      font-size: 10px;
      color: #fdba74;
    }
    .motor-btn-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 4px;
      margin-top: 8px;
    }
    .btn-mot {
      background: #1e293b;
      border: 1px solid #334155;
      color: #cbd5e1;
      border-radius: 4px;
      padding: 4px 2px;
      font-size: 9px;
      font-weight: 600;
      cursor: pointer;
      text-align: center;
      transition: all 0.15s;
    }
    .btn-mot:hover {
      background: rgba(234, 88, 12, 0.25);
      color: #fdba74;
      border-color: #ea580c;
    }
    .motor-telemetry {
      margin-top: 6px;
      padding-top: 6px;
      border-top: 1px solid rgba(148, 163, 184, 0.15);
      font-family: monospace;
      font-size: 9px;
      color: #94a3b8;
      display: flex;
      justify-content: space-between;
    }
"""

text = text.replace('</style>', css_extra + '\n  </style>', 1)

# 2. HTML panels before <div class="hud-controls">
html_extra = """  <!-- 2D SLAM Minimap -->
  <div class="slam-map-card" id="slamMapCard">
    <div class="slam-header">
      <div class="slam-title">
        <span class="slam-pulse"></span>
        <span>2D КАРТА ОБСЛЕДОВАНИЯ (SLAM)</span>
      </div>
      <span class="slam-badge" id="slamCoverageBadge">ПОКРЫТИЕ: 0.0%</span>
    </div>
    <div class="slam-canvas-wrap">
      <canvas id="slamCanvas" width="300" height="200"></canvas>
    </div>
    <div class="slam-legend">
      <span class="legend-item"><span class="legend-box unscanned"></span> Туман</span>
      <span class="legend-item"><span class="legend-box scanned"></span> Чисто</span>
      <span class="legend-item"><span class="legend-box wall"></span> Стена</span>
      <span class="legend-item"><span class="legend-box inside-nfz"></span> Стена внутри</span>
    </div>
  </div>

  <!-- Motor RPM Control Panel -->
  <div class="motor-panel" id="motorPanel">
    <div class="motor-header">
      <div class="motor-title">🎛️ МИКШЕР 4 МОТОРОВ (RPM / 6-DOF)</div>
      <span class="motor-close" id="motorCloseBtn">&times;</span>
    </div>
    <div class="motor-row">
      <span class="motor-label" style="color:#fdba74;">M1 (Перед-Л CCW)</span>
      <input type="range" min="0" max="100" value="0" class="motor-slider" id="m1Slider">
      <span class="motor-val" id="m1Val">0% (0)</span>
    </div>
    <div class="motor-row">
      <span class="motor-label" style="color:#fdba74;">M2 (Перед-П CW)</span>
      <input type="range" min="0" max="100" value="0" class="motor-slider" id="m2Slider">
      <span class="motor-val" id="m2Val">0% (0)</span>
    </div>
    <div class="motor-row">
      <span class="motor-label" style="color:#38bdf8;">M3 (Зад-П CCW)</span>
      <input type="range" min="0" max="100" value="0" class="motor-slider" id="m3Slider">
      <span class="motor-val" id="m3Val">0% (0)</span>
    </div>
    <div class="motor-row">
      <span class="motor-label" style="color:#38bdf8;">M4 (Зад-Л CW)</span>
      <input type="range" min="0" max="100" value="0" class="motor-slider" id="m4Slider">
      <span class="motor-val" id="m4Val">0% (0)</span>
    </div>
    <div class="motor-btn-grid">
      <button class="btn-mot" id="btnHover50">⚖️ Висение 50%</button>
      <button class="btn-mot" id="btnThrotUp">⬆️ Газ +5%</button>
      <button class="btn-mot" id="btnThrotDn">⬇️ Газ -5%</button>
      <button class="btn-mot" id="btnStopMotors" style="color:#f87171;">🛑 Стоп 0%</button>
      <button class="btn-mot" id="btnNoseDown">🔼 Вперед</button>
      <button class="btn-mot" id="btnNoseUp">🔽 Назад</button>
      <button class="btn-mot" id="btnRollL">◀️ Крен Л</button>
      <button class="btn-mot" id="btnRollR">▶️ Крен П</button>
    </div>
    <div class="motor-telemetry">
      <span id="motorThrustVal">Тяга Fz: 0.00 Н</span>
      <span id="motorTorqueVal">Углы: 0.0° / 0.0°</span>
    </div>
  </div>

"""

text = text.replace('<div class="hud-controls">', html_extra + '  <div class="hud-controls">', 1)

# 3. New buttons in hud-controls
old_btns = '<button class="btn btn-active-toggle" id="btnToggleRoute">🗺️ Маршрут: ВКЛ</button>'
new_btns = '''<button class="btn btn-active-toggle" id="btnToggleRoute">🗺️ Маршрут: ВКЛ</button>
    <button class="btn btn-active-toggle" id="btnToggleSlam">🗺️ 2D Карта SLAM</button>
    <button class="btn" id="btnToggleMotors">🎛️ Моторы (RPM): ВЫКЛ</button>'''

text = text.replace(old_btns, new_btns, 1)

# 4. Camera Frustum setup in buildQuadcopter: attach to scene so it's in world coords!
text = text.replace('frustumGroup.visible = false;\n        droneBody.add(frustumGroup);\n        cameraFrustum = frustumGroup;',
                    'frustumGroup.visible = false;\n        scene.add(frustumGroup);\n        cameraFrustum = frustumGroup;', 1)

# 5. Stabilized Nadir Frustum update in updateDronePhysics:
old_frustum_calc = '''      if (st.role === 'recon' && obj.cameraFrustum && obj.cameraFrustum.visible && obj.frustumPyrGeo) {
        const vApex = [0.02, 0, -0.026];
        const hRel = -Math.max(st.z - 0.005, 0.05);
        const w = 0.38 * (Math.abs(hRel) / 1.2);
        const d = 0.30 * (Math.abs(hRel) / 1.2);

        const vFL = [0.02 + w,  d, hRel];
        const vFR = [0.02 + w, -d, hRel];
        const vRR = [0.02 - w, -d, hRel];
        const vRL = [0.02 - w,  d, hRel];'''

new_frustum_calc = '''      if (st.role === 'recon' && obj.cameraFrustum && obj.cameraFrustum.visible && obj.frustumPyrGeo) {
        // Стабилизированная камера (Gimbal): проекция строго вертикально вниз (Nadir)
        // Конус НЕ наклоняется и НЕ качается при маневрах и наклонах дрона!
        const vApex = [st.x, st.y, Math.max(st.z - 0.026, 0.02)];
        const hRel = Math.max(st.z, 0.05);
        const w = 0.44 * (hRel / 1.2);
        const d = 0.34 * (hRel / 1.2);

        const vFL = [st.x + w, st.y + d, 0.005];
        const vFR = [st.x + w, st.y - d, 0.005];
        const vRR = [st.x - w, st.y - d, 0.005];
        const vRL = [st.x - w, st.y + d, 0.005];'''

text = text.replace(old_frustum_calc, new_frustum_calc, 1)

# 6. Waypoints for 100% complete field coverage
old_recon_wp = '''    const plannedReconWaypoints = [
      { x: 0.40, y: 0.40, z: 1.2 }, // 1. Старт с площадки Home-1
      { x: 1.10, y: 0.42, z: 1.2 }, // 2. Сектор Юго-Запад (цель A-1)
      { x: 2.10, y: 0.42, z: 1.2 }, // 3. Сектор Юг (цель A-2)
      { x: 3.20, y: 0.42, z: 1.2 }, // 4. Коридор южнее NFZ-1
      { x: 4.40, y: 0.38, z: 1.2 }, // 5. Сектор южнее NFZ-2 (цель A-NFZ2)
      { x: 5.48, y: 0.38, z: 1.2 }, // 6. Сектор Юго-Восток (цель U)
      { x: 5.48, y: 1.35, z: 1.2 }, // 7. Восточный коридор низ
      { x: 5.48, y: 2.40, z: 1.2 }, // 8. Сектор Восток (цель A-6)
      { x: 5.48, y: 3.48, z: 1.2 }, // 9. Северо-Восток
      { x: 4.20, y: 3.48, z: 1.2 }, // 10. Сектор Северо-Восток (цель A-5)
      { x: 2.60, y: 3.48, z: 1.2 }, // 11. Сектор Север (цель A-4)
      { x: 1.10, y: 3.48, z: 1.2 }, // 12. Сектор Северо-Запад (цель A-3)
      { x: 0.70, y: 2.80, z: 1.2 }, // 13. Сектор Запад (цель B)
      { x: 0.70, y: 1.60, z: 1.2 }, // 14. Западный коридор
      { x: 1.20, y: 1.60, z: 1.2 }, // 15. Внутренний коридор западнее NFZ-1
      { x: 1.20, y: 2.20, z: 1.2 }, // 16. Центр западнее NFZ-1 (цель A-NFZ1)
      { x: 0.70, y: 1.00, z: 1.2 }, // 17. Выход на предпосадочный курс
      { x: 0.40, y: 0.40, z: 1.2 }, // 18. Зависание над Home-1
      { x: 0.40, y: 0.40, z: 0.08 } // 19. Точная посадка на Home-1
    ];'''

new_recon_wp = '''    const plannedReconWaypoints = [
      { x: 0.40, y: 0.40, z: 1.2 }, // 1. Старт с Home-1
      { x: 1.10, y: 0.42, z: 1.2 }, // 2. Сектор Юго-Запад (A-1)
      { x: 2.10, y: 0.42, z: 1.2 }, // 3. Сектор Юг (A-2)
      { x: 3.20, y: 0.42, z: 1.2 }, // 4. Коридор южнее NFZ-1
      { x: 4.40, y: 0.38, z: 1.2 }, // 5. Южнее NFZ-2 (A-NFZ2)
      { x: 5.48, y: 0.38, z: 1.2 }, // 6. Сектор Юго-Восток (U)
      { x: 5.48, y: 1.35, z: 1.2 }, // 7. Восточный коридор низ
      { x: 5.48, y: 2.40, z: 1.2 }, // 8. Сектор Восток (A-6)
      { x: 5.48, y: 3.48, z: 1.2 }, // 9. Северо-Восток
      { x: 4.20, y: 3.48, z: 1.2 }, // 10. Северо-Восток (A-5)
      { x: 3.55, y: 3.48, z: 1.2 }, // 11. Вход в центральный коридор
      { x: 3.55, y: 2.40, z: 1.2 }, // 12. Центральный коридор (между NFZ-1 и NFZ-2)
      { x: 3.55, y: 1.20, z: 1.2 }, // 13. Центральный проход Юг
      { x: 3.55, y: 2.40, z: 1.2 }, // 14. Центральный проход возврат
      { x: 3.55, y: 3.48, z: 1.2 }, // 15. Выход на Север
      { x: 2.60, y: 3.48, z: 1.2 }, // 16. Сектор Север (A-4)
      { x: 1.10, y: 3.48, z: 1.2 }, // 17. Сектор Северо-Запад (A-3)
      { x: 0.70, y: 2.80, z: 1.2 }, // 18. Сектор Запад (B)
      { x: 0.70, y: 1.60, z: 1.2 }, // 19. Западный коридор
      { x: 1.20, y: 1.60, z: 1.2 }, // 20. Коридор западнее NFZ-1
      { x: 1.20, y: 2.20, z: 1.2 }, // 21. Сканирование западной границы NFZ-1 (A-NFZ1)
      { x: 0.70, y: 1.00, z: 1.2 }, // 22. Предпосадочный курс
      { x: 0.40, y: 0.40, z: 1.2 }, // 23. Зависание над Home-1 (100% покрытия)
      { x: 0.40, y: 0.40, z: 0.08 } // 24. Финальная посадка строго в Home-1
    ];'''

text = text.replace(old_recon_wp, new_recon_wp, 1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated Part 1 (UI, CSS, Frustum, Waypoints)!')
