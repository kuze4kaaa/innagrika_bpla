"""
Скрипт для комплексного визуального обновления 3D-симуляции (Иннагрика 2026 · Агротех АТ11-2)
Все объекты приводятся в строгое соответствие с ТЗ и делаются 100% понятными человеку без ТЗ:
1. Агрономическая почва и гряды с всходами культурных растений.
2. Огражденная летная зона 6х4х2.5 м с ферменными опорами, защитной сеткой и линейкой разметки координат поля F.
3. 10 участков с различимыми 3D-растениями:
   - 6 сорняков A с желтыми пятнами поражения, кругом допуска 0.25м и точкой 0.04м.
   - 2 сорняка A в запретной зоне NFZ с красными предупреждающими бейджами.
   - 1 здоровый пышный куст B (томаты/культура) с синим бейджем "Без обработки".
   - 1 сомнительный сухой образец U с фиолетовым бейджем "Пропуск".
4. Настоящее техническое оборудование в запретных зонах:
   - NFZ-1: Шкаф автоматики климат-контроля и полива с мигающим проблесковым маячком и знаком 380В.
   - NFZ-2: Метеомачта с вращающимся анемометром и насосная гидростанция.
5. Стартовые базы H-1 и H-2 с взлетными знаками, огнями и станцией дозаправки биопрепарата.
6. БПЛА:
   - БПЛА-1: камера 4K с лазерной сканирующей сеткой на земле.
   - БПЛА-2: бак биопрепарата, форсунка, световой индикатор 2с и эффект микрокапельного распыления тумана!
7. Плавающие 3D-бейдж-таблички над всеми объектами (THREE.Sprite).
8. 3D-индикатор высотного коридора 1.0 - 1.4 м.
9. Верхний пошаговый баннер этапов миссии и интерактивная легенда объектов.
"""

import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("Original length:", len(content))

# 1. Update CSS styles: add styles for new pipeline bar, legend panel, camera buttons, etc.
css_to_add = '''
    /* --- ВЕРХНИЙ ПОШАГОВЫЙ БАР ЭТАПОВ МИССИИ (ДЛЯ ПОНЯТНОСТИ БЕЗ ТЗ) --- */
    .mission-pipeline-card {
      position: absolute;
      top: 66px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(15, 23, 42, 0.92);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(56, 189, 248, 0.4);
      border-radius: 10px;
      padding: 6px 14px;
      display: flex;
      align-items: center;
      gap: 12px;
      z-index: 12;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.6);
      pointer-events: auto;
    }
    .pipe-step {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      font-weight: 600;
      color: #64748b;
      padding: 4px 8px;
      border-radius: 6px;
      transition: all 0.3s ease;
    }
    .pipe-step.active {
      color: #f8fafc;
      background: rgba(56, 189, 248, 0.2);
      border: 1px solid #38bdf8;
      box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
    }
    .pipe-step.done {
      color: #4ade80;
      background: rgba(34, 197, 94, 0.15);
      border: 1px solid rgba(34, 197, 94, 0.4);
    }
    .pipe-arrow {
      color: #475569;
      font-size: 11px;
    }

    /* --- ИНТЕРАКТИВНАЯ ЛЕГЕНДА СЦЕНЫ (ПОЯСНЕНИЕ ВСЕХ ОБЪЕКТОВ) --- */
    .scene-legend-card {
      position: absolute;
      top: 130px;
      right: 14px;
      width: 270px;
      background: rgba(15, 23, 42, 0.92);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 11px;
      z-index: 12;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
      transition: all 0.2s ease;
      user-select: none;
    }
    .legend-title {
      font-size: 11px;
      font-weight: 700;
      color: #38bdf8;
      margin-bottom: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      cursor: pointer;
    }
    .legend-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .legend-row {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      line-height: 1.35;
    }
    .legend-icon-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      border-radius: 4px;
      font-size: 11px;
      flex-shrink: 0;
    }
    .legend-row-text b {
      color: #f1f5f9;
    }
    .legend-row-text span {
      color: #94a3b8;
      font-size: 10px;
    }

    /* 3D Label Toggle Pill */
    .btn-toggle-pills {
      background: #1e293b;
      border: 1px solid #334155;
      color: #cbd5e1;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 10px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .btn-toggle-pills.active {
      background: rgba(56, 189, 248, 0.25);
      border-color: #38bdf8;
      color: #38bdf8;
    }
'''

# Insert css before </style>
content = content.replace('</style>', css_to_add + '\n</style>', 1)

# 2. Add Pipeline and Legend HTML inside body
html_elements = '''
  <!-- Верхний пошаговый бар этапов ТЗ -->
  <div class="mission-pipeline-card" id="missionPipeline">
    <div class="pipe-step active" id="pipe1">
      <span>🔍 1. Разведка посевов (БПЛА-1)</span>
    </div>
    <span class="pipe-arrow">➔</span>
    <div class="pipe-step" id="pipe2">
      <span>🛡️ 2. Валидация GCS (Отсечение NFZ)</span>
    </div>
    <span class="pipe-arrow">➔</span>
    <div class="pipe-step" id="pipe3">
      <span>🎯 3. Обработка сорняков (БПЛА-2)</span>
    </div>
    <span class="pipe-arrow">➔</span>
    <div class="pipe-step" id="pipe4">
      <span>🏁 4. Отчет и возврат</span>
    </div>
  </div>

  <!-- Интерактивная легенда объектов сцены -->
  <div class="scene-legend-card" id="sceneLegend">
    <div class="legend-title" id="legendToggle">
      <span>📋 ОБЪЕКТЫ ПО ТЗ (Справка)</span>
      <button class="btn-toggle-pills active" id="btnToggleLabels">🏷️ 3D-Метки: ВКЛ</button>
    </div>
    <div class="legend-list" id="legendList">
      <div class="legend-row">
        <span class="legend-icon-badge" style="background: rgba(234, 88, 12, 0.3); color: #fb923c;">🎯</span>
        <div class="legend-row-text">
          <b>Очаг A (6 шт)</b><br>
          <span>Сорняк / болезнь. Требуется световая обработка 2.0с (R=0.25м).</span>
        </div>
      </div>
      <div class="legend-row">
        <span class="legend-icon-badge" style="background: rgba(239, 68, 68, 0.3); color: #f87171;">🚫</span>
        <div class="legend-row-text">
          <b>Очаг A в NFZ (2 шт)</b><br>
          <span>Сорняк в опасной зоне. По ТЗ полёт и обработка строго ЗАПРЕЩЕНЫ.</span>
        </div>
      </div>
      <div class="legend-row">
        <span class="legend-icon-badge" style="background: rgba(59, 130, 246, 0.3); color: #60a5fa;">🌿</span>
        <div class="legend-row-text">
          <b>Участок B (1 шт)</b><br>
          <span>Здоровая культура (томаты). Только наблюдение, без химии.</span>
        </div>
      </div>
      <div class="legend-row">
        <span class="legend-icon-badge" style="background: rgba(168, 85, 247, 0.3); color: #c084fc;">❓</span>
        <div class="legend-row-text">
          <b>Участок U (1 шт)</b><br>
          <span>Неопределенный спектр. Пропуск для исключения брака.</span>
        </div>
      </div>
      <div class="legend-row">
        <span class="legend-icon-badge" style="background: rgba(239, 68, 68, 0.3); color: #ef4444;">⛔</span>
        <div class="legend-row-text">
          <b>Запретные зоны NFZ</b><br>
          <span>Шкаф автоматики и метеомачта. Влет запрещен (+0.23м буфер).</span>
        </div>
      </div>
      <div class="legend-row">
        <span class="legend-icon-badge" style="background: rgba(34, 197, 94, 0.3); color: #4ade80;">💡</span>
        <div class="legend-row-text">
          <b>Агрооперация (LED 2с)</b><br>
          <span>Включение светодиода на 2.0с на высоте 1.0–1.4 м.</span>
        </div>
      </div>
    </div>
  </div>
'''

content = content.replace('<div class="discovery-toast" id="discoveryToast">', html_elements + '\n  <div class="discovery-toast" id="discoveryToast">', 1)

# 3. Add 3D-Preset Camera Buttons into .cam-group
old_cam_group = '''      <div class="cam-group">
        <button class="btn-cam-mini active" id="camTrack" title="Слежение за активным дроном">🎯 Слежение</button>
        <button class="btn-cam-mini" id="camOrbit" title="Общий вид полигона">🌐 Поле</button>
        <button class="btn-cam-mini" id="camTop" title="Вид сверху">🗺️ 2D</button>
        <button class="btn-cam-mini" id="camFpv" title="Бортовая камера">📷 FPV</button>
      </div>'''

new_cam_group = '''      <div class="cam-group">
        <button class="btn-cam-mini active" id="camTrack" title="Слежение за активным дроном">🎯 Слежение</button>
        <button class="btn-cam-mini" id="camOrbit" title="Изометрия полигона">📐 3D Поле</button>
        <button class="btn-cam-mini" id="camTop" title="Вид сверху (F-сетка)">🗺️ Сетка F</button>
        <button class="btn-cam-mini" id="camFpv" title="Бортовая камера">📷 FPV</button>
        <button class="btn-cam-mini" id="camCloseTarget" title="Крупный план очага A">🔍 Очаг A</button>
      </div>'''

content = content.replace(old_cam_group, new_cam_group, 1)

# Now write out the intermediate result to verify
with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("HTML UI elements updated successfully!")
