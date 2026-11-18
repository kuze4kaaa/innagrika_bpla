"""
Скрипт радикального устранения нагромождения интерфейса (Decluttering):
1. Удаление гигантских 3D-билбордов в воздухе (cageSign, originSprite, padSprite, nfzSprite, droneTagSprite).
2. Замена 10 огромных текстовых карточек целей на микро-пины (маленькие компактные бейджи A1, A2, B, U, NFZ) с depthTest: true.
3. Скрытие по умолчанию 2D SLAM-карты и легенды "ОБЪЕКТЫ ПО ТЗ" (открываются по клику).
4. Объединение верхнего бара: компактный аккуратный заголовок, элегантный пошаговый пайплайн и телеметрия в едином стиле без наслоений.
5. Компактный нижний док управления.
"""

import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update CSS: hide SLAM card and Scene Legend by default, style them as elegant sliding modals
css_replacements = '''
    /* Скрытие по умолчанию тяжелых панелей (чистый экран) */
    .slam-map-card {
      display: none; /* Скрыто по умолчанию */
    }
    .scene-legend-card {
      display: none; /* Скрыто по умолчанию */
      position: absolute;
      top: 70px;
      right: 14px;
      width: 280px;
      background: rgba(15, 23, 42, 0.94);
      backdrop-filter: blur(14px);
      border: 1px solid rgba(56, 189, 248, 0.35);
      border-radius: 12px;
      padding: 12px 14px;
      font-size: 11px;
      z-index: 25;
      box-shadow: 0 12px 36px rgba(0, 0, 0, 0.7);
    }
    .legend-close {
      cursor: pointer;
      color: #94a3b8;
      font-size: 16px;
      font-weight: bold;
    }
    .legend-close:hover {
      color: #f8fafc;
    }

    /* Компактный верхний бар пайплайна (без нагромождения) */
    .mission-pipeline-card {
      position: absolute;
      top: 12px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(15, 23, 42, 0.88);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(56, 189, 248, 0.3);
      border-radius: 20px;
      padding: 4px 12px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 3px;
      z-index: 12;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
      pointer-events: auto;
    }
    .pipeline-steps-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .pipe-step {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 11px;
      font-weight: 600;
      color: #64748b;
      padding: 3px 8px;
      border-radius: 12px;
      transition: all 0.25s ease;
    }
    .pipe-step.active {
      color: #f8fafc;
      background: rgba(56, 189, 248, 0.25);
      border: 1px solid #38bdf8;
      box-shadow: 0 0 8px rgba(56, 189, 248, 0.35);
    }
    .pipe-step.done {
      color: #4ade80;
      background: rgba(34, 197, 94, 0.15);
      border: 1px solid rgba(34, 197, 94, 0.35);
    }
    .pipe-arrow {
      color: #475569;
      font-size: 10px;
    }
    .pipeline-subtext {
      font-size: 10px;
      color: #94a3b8;
      max-width: 480px;
      text-align: center;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* Убираем отдельный тяжелый mission-phase-banner */
    .mission-phase-banner {
      display: none !important;
    }

    /* Компактный Bottom Dock */
    .hud-controls {
      position: absolute;
      bottom: 12px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(15, 23, 42, 0.90);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(148, 163, 184, 0.2);
      border-radius: 12px;
      padding: 5px 8px;
      display: flex;
      align-items: center;
      gap: 6px;
      z-index: 10;
      box-shadow: 0 6px 24px rgba(0, 0, 0, 0.6);
    }
    .btn {
      padding: 6px 10px;
      font-size: 11px;
      border-radius: 6px;
    }
'''

# Replace CSS
text = text.replace('/* --- ВЕРХНИЙ ПОШАГОВЫЙ БАР ЭТАПОВ МИССИИ (ДЛЯ ПОНЯТНОСТИ БЕЗ ТЗ) --- */', css_replacements)

# 2. Update HTML of missionPipeline to be compact single bar
old_pipeline_html = '''  <!-- Верхний пошаговый бар этапов ТЗ -->
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
  </div>'''

new_pipeline_html = '''  <!-- Компактный верхний бар этапов ТЗ -->
  <div class="mission-pipeline-card" id="missionPipeline">
    <div class="pipeline-steps-row">
      <div class="pipe-step active" id="pipe1">
        <span>🔍 1. Разведка</span>
      </div>
      <span class="pipe-arrow">➔</span>
      <div class="pipe-step" id="pipe2">
        <span>🛡️ 2. Валидация</span>
      </div>
      <span class="pipe-arrow">➔</span>
      <div class="pipe-step" id="pipe3">
        <span>🎯 3. Обработка (6)</span>
      </div>
      <span class="pipe-arrow">➔</span>
      <div class="pipe-step" id="pipe4">
        <span>🏁 4. Финиш</span>
      </div>
    </div>
    <div class="pipeline-subtext" id="pipelineSubtext">Ожидание команды оператора · Нажмите «⚡ Запуск миссии»</div>
  </div>'''

text = text.replace(old_pipeline_html, new_pipeline_html, 1)

# 3. Update Legend Card HTML to include close button
old_legend_html = '''  <div class="scene-legend-card" id="sceneLegend">
    <div class="legend-title" id="legendToggle">
      <span>📋 ОБЪЕКТЫ ПО ТЗ (Справка)</span>
      <button class="btn-toggle-pills active" id="btnToggleLabels">🏷️ 3D-Метки: ВКЛ</button>
    </div>'''

new_legend_html = '''  <div class="scene-legend-card" id="sceneLegend">
    <div class="legend-title">
      <span>📋 ОБЪЕКТЫ ПО ТЗ (Справка)</span>
      <span class="legend-close" id="legendCloseBtn">&times;</span>
    </div>'''

text = text.replace(old_legend_html, new_legend_html, 1)

# 4. Update Bottom Controls to be clean and organized
old_hud_controls = '''  <div class="hud-controls">
    <button class="btn btn-chain" id="btnRunChain">⚡ Полная цепочка: Разведка → GCS → Исполнение</button>
    <button class="btn btn-primary" id="btnTakeoff">🚀 Взлет (1.2 м)</button>
    <button class="btn" id="btnLand">🛬 Посадка</button>
    <button class="btn btn-success" id="btnPayload">💡 Операция LED (2 с)</button>
    <button class="btn btn-active-toggle" id="btnToggleRoute">🗺️ Маршрут: ВКЛ</button>
    <button class="btn btn-active-toggle" id="btnToggleSlam">🗺️ 2D Карта SLAM</button>
    <button class="btn" id="btnToggleMotors">🎛️ Моторы (RPM): ВЫКЛ</button>
    <button class="btn" id="btnRandomize">🎲 Новая карта целей</button>
    <button class="btn" id="btnReset">🔄 Сброс</button>
    <button class="btn btn-icon" id="btnHelp" title="Подсказка управления">⌨️</button>
  </div>'''

new_hud_controls = '''  <div class="hud-controls">
    <button class="btn btn-chain" id="btnRunChain" title="Автоматический запуск полной миссии">⚡ Автомиссия ТЗ (Полная цепочка)</button>
    <button class="btn btn-primary" id="btnTakeoff">🚀 Взлет (1.2м)</button>
    <button class="btn" id="btnLand">🛬 Посадка</button>
    <button class="btn btn-success" id="btnPayload">💡 Тест LED (2с)</button>
    <button class="btn" id="btnToggleSlam">🗺️ SLAM</button>
    <button class="btn" id="btnToggleLegend">📋 Справка ТЗ</button>
    <button class="btn" id="btnToggleLabels">🏷️ Метки</button>
    <button class="btn" id="btnRandomize" title="Сгенерировать случайное поле">🎲 Новые цели</button>
    <button class="btn" id="btnReset">🔄 Сброс</button>
    <button class="btn btn-icon" id="btnHelp" title="Подсказка управления">⌨️</button>
  </div>'''

text = text.replace(old_hud_controls, new_hud_controls, 1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Pass 1 of declutter applied!")
