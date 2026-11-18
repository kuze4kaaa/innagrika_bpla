"""
Скрипт устранения накладок в верхнем баре и выравнивания нижних кнопок:
1. Верхний бар переводится на полноценный 3-колоночный flex-layout:
   - Слева: Бренд + Камеры + КНОПКИ СКОРОСТИ (всегда видны, выделены и доступны!)
   - По центру: Пайплайн этапов ТЗ (в потоке flex, БЕЗ абсолютного позиционирования, исключая наложение)
   - Справа: Переключатель бортов + телеметрия
2. Нижние кнопки:
   - Строго единая высота (height: 38px)
   - Строго одна строка (white-space: nowrap)
   - Одинаковое вертикальное центрирование (display: inline-flex; align-items: center;)
   - Идеальный, ровный, единообразный вид dock-панели!
"""

import sys

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update CSS for topbar, pipeline, speed buttons, and hud-controls
old_css_hud = '''.hud-controls {
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
    }'''

new_css_topbar_and_dock = '''
    /* --- ВЕРХНИЙ БАР (3-КОЛОНОЧНЫЙ FLEX БЕЗ НАЛОЖЕНИЙ) --- */
    .topbar {
      position: absolute;
      top: 10px;
      left: 12px;
      right: 12px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      pointer-events: none;
      z-index: 100;
    }
    .topbar-left {
      display: flex;
      align-items: center;
      gap: 8px;
      pointer-events: auto;
      flex-shrink: 0;
    }
    .topbar-center {
      display: flex;
      justify-content: center;
      align-items: center;
      flex: 1;
      min-width: 0;
      pointer-events: auto;
    }
    .topbar-right {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 6px;
      pointer-events: auto;
      flex-shrink: 0;
    }

    /* Кнопки скорости: яркие, четкие и всегда на виду */
    .speed-group {
      background: rgba(15, 23, 42, 0.92);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(56, 189, 248, 0.45);
      border-radius: 8px;
      padding: 3px;
      display: flex;
      gap: 2px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
    }
    .btn-speed {
      background: transparent;
      border: none;
      color: #94a3b8;
      padding: 5px 8px;
      font-size: 11px;
      font-weight: 700;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    .btn-speed:hover {
      color: #38bdf8;
      background: rgba(56, 189, 248, 0.15);
    }
    .btn-speed.active {
      background: #0284c7;
      color: #ffffff;
      box-shadow: 0 0 8px rgba(2, 132, 199, 0.6);
    }

    /* Пайплайн этапов по центру (в потоке flex, БЕЗ absolute) */
    .mission-pipeline-card {
      background: rgba(15, 23, 42, 0.92);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(56, 189, 248, 0.35);
      border-radius: 20px;
      padding: 4px 14px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    }

    /* --- НИЖНИЙ ДОК: СТРОГО ВЫРОВНЕННЫЕ И ОДИНАКОВЫЕ КНОПКИ --- */
    .hud-controls {
      position: absolute;
      bottom: 12px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(15, 23, 42, 0.94);
      backdrop-filter: blur(14px);
      border: 1px solid rgba(148, 163, 184, 0.25);
      border-radius: 12px;
      padding: 6px 8px;
      display: flex;
      align-items: center;
      gap: 6px;
      z-index: 100;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.7);
      white-space: nowrap;
    }
    .btn {
      height: 38px; /* Строго единая высота для всех кнопок! */
      box-sizing: border-box;
      background: #1e293b;
      color: #f1f5f9;
      border: 1px solid #334155;
      padding: 0 12px;
      border-radius: 8px;
      font-size: 11.5px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      line-height: 1;
      white-space: nowrap; /* Строго одна строка, никаких многострочных накладок! */
      transition: all 0.2s ease;
    }
    .btn:hover {
      background: #334155;
      border-color: #38bdf8;
      color: #38bdf8;
    }
    .btn-icon {
      padding: 0 10px;
      font-size: 13px;
    }
'''

text = text.replace(old_css_hud, new_css_topbar_and_dock, 1)

# Also remove old .mission-pipeline-card absolute positioning from earlier CSS
text = text.replace('''    .mission-pipeline-card {
      position: absolute;
      top: 12px;
      left: 50%;
      transform: translateX(-50%);''', '''    .mission-pipeline-card {''', 1)

# 2. Update HTML of topbar to include topbar-center with missionPipeline inside
old_topbar_full = '''  <div class="topbar">
    <div class="topbar-left">
      <div class="brand-card">
        <div class="brand-title">ИННАГРИКА 2026</div>
        <div class="brand-sub">Полигон 6 × 4 м</div>
      </div>

      <div class="cam-group">
        <button class="btn-cam-mini" id="camOrbit" title="Общий вид полигона">📐 3D Поле</button>
        <button class="btn-cam-mini active" id="camTrack" title="Слежение за дроном">🎯 Слежение</button>
        <button class="btn-cam-mini" id="camTop" title="Вид сверху">🗺️ 2D</button>
        <button class="btn-cam-mini" id="camFpv" title="Камера дрона">📷 FPV</button>
      </div>

      <div class="speed-group" title="Скорость симуляции">
        <button class="btn-speed active" id="spd1">1×</button>
        <button class="btn-speed" id="spd2">2×</button>
        <button class="btn-speed" id="spd4">4×</button>
        <button class="btn-speed" id="spd8">8×</button>
      </div>
    </div>

    <div class="topbar-right" style="display:flex; flex-direction:column; align-items:flex-end; gap:6px;">
      <div class="segmented-group">
        <button class="btn-seg active-recon" id="selectRecon">
          🚁 БПЛА-1
        </button>
        <button class="btn-seg" id="selectExec">
          🛸 БПЛА-2
        </button>
      </div>
      <div class="telemetry-card">
        <div class="telemetry-row">
          <span class="telemetry-label">АКТИВНЫЙ БОPT:</span>
          <span class="telemetry-value" id="activeDroneName" style="color:#fdba74;">БПЛА-1 (Разведчик)</span>
        </div>
        <div class="telemetry-row">
          <span class="telemetry-label">FSM СТАТУС:</span>
          <span class="badge badge-ok" id="fsmStatus">READY</span>
        </div>
        <div class="telemetry-row">
          <span class="telemetry-label">ПОЗИЦИЯ:</span>
          <span class="telemetry-value" id="coordsValue">X:0.40 Y:0.40 Z:0.08м</span>
        </div>
        <div class="telemetry-row">
          <span class="telemetry-label">СКОРОСТЬ:</span>
          <span class="telemetry-value" id="speedValue">0.00 м/с</span>
        </div>
        <div class="telemetry-row">
          <span class="telemetry-label">РАЗВЕДКА КАРТЫ:</span>
          <span class="telemetry-value" id="targetsDiscoveredValue" style="color:#38bdf8;">0 / 10 ЦЕЛЕЙ</span>
        </div>
        <div class="telemetry-row">
          <span class="telemetry-label">ОБОРУДОВАНИЕ:</span>
          <span class="telemetry-value">
            <span class="payload-indicator" id="payloadLed"></span>
            <span id="payloadText">ГОТОВ</span>
          </span>
        </div>
        <div class="altitude-track" title="Допустимый коридор высоты: 1.0 - 1.4 м">
          <div class="corridor-marker" style="left: 50%; width: 20%;"></div>
          <div class="altitude-pointer" id="altPointer" style="left: 4%;"></div>
        </div>
      </div>
    </div>
  </div>

  
  <!-- Компактный верхний бар этапов ТЗ -->
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

new_topbar_full = '''  <div class="topbar">
    <!-- ЛЕВАЯ ЧАСТЬ: Бренд + Камеры + СКОРОСТЬ (всегда на виду, без перекрытий!) -->
    <div class="topbar-left">
      <div class="brand-card">
        <div class="brand-title">ИННАГРИКА 2026</div>
        <div class="brand-sub">Полигон 6 × 4 м</div>
      </div>

      <div class="cam-group">
        <button class="btn-cam-mini" id="camOrbit" title="Общий 3D-вид полигона">📐 3D Поле</button>
        <button class="btn-cam-mini active" id="camTrack" title="Слежение за дроном">🎯 Слежение</button>
        <button class="btn-cam-mini" id="camTop" title="Вид сверху 2D">🗺️ 2D</button>
        <button class="btn-cam-mini" id="camFpv" title="Камера дрона">📷 FPV</button>
      </div>

      <div class="speed-group" title="Скорость симуляции">
        <button class="btn-speed active" id="spd1">1×</button>
        <button class="btn-speed" id="spd2">2×</button>
        <button class="btn-speed" id="spd4">4×</button>
        <button class="btn-speed" id="spd8">8×</button>
      </div>
    </div>

    <!-- ЦЕНТРАЛЬНАЯ ЧАСТЬ: Шаги миссии ТЗ (в потоке flex, НИКАКИХ наложений!) -->
    <div class="topbar-center">
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
        <div class="pipeline-subtext" id="pipelineSubtext">Ожидание команды оператора · Нажмите «⚡ Запуск цепочки»</div>
      </div>
    </div>

    <!-- ПРАВАЯ ЧАСТЬ: Выбор дрона + Телеметрия -->
    <div class="topbar-right">
      <div class="segmented-group">
        <button class="btn-seg active-recon" id="selectRecon">
          🚁 БПЛА-1
        </button>
        <button class="btn-seg" id="selectExec">
          🛸 БПЛА-2
        </button>
      </div>
      <div class="telemetry-card">
        <div class="telemetry-row">
          <span class="telemetry-label">АКТИВНЫЙ БОPT:</span>
          <span class="telemetry-value" id="activeDroneName" style="color:#fdba74;">БПЛА-1 (Разведчик)</span>
        </div>
        <div class="telemetry-row">
          <span class="telemetry-label">FSM СТАТУС:</span>
          <span class="badge badge-ok" id="fsmStatus">READY</span>
        </div>
        <div class="telemetry-row">
          <span class="telemetry-label">ПОЗИЦИЯ:</span>
          <span class="telemetry-value" id="coordsValue">X:0.40 Y:0.40 Z:0.08м</span>
        </div>
        <div class="telemetry-row">
          <span class="telemetry-label">СКОРОСТЬ:</span>
          <span class="telemetry-value" id="speedValue">0.00 м/с</span>
        </div>
        <div class="telemetry-row">
          <span class="telemetry-label">РАЗВЕДКА КАРТЫ:</span>
          <span class="telemetry-value" id="targetsDiscoveredValue" style="color:#38bdf8;">0 / 10 ЦЕЛЕЙ</span>
        </div>
        <div class="telemetry-row">
          <span class="telemetry-label">ОБОРУДОВАНИЕ:</span>
          <span class="telemetry-value">
            <span class="payload-indicator" id="payloadLed"></span>
            <span id="payloadText">ГОТОВ</span>
          </span>
        </div>
        <div class="altitude-track" title="Допустимый коридор высоты: 1.0 - 1.4 м">
          <div class="corridor-marker" style="left: 50%; width: 20%;"></div>
          <div class="altitude-pointer" id="altPointer" style="left: 4%;"></div>
        </div>
      </div>
    </div>
  </div>'''

text = text.replace(old_topbar_full, new_topbar_full, 1)

# 3. Update bottom controls: strictly one-line clean text and unified height
old_dock = '''  <div class="hud-controls">
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

new_dock = '''  <div class="hud-controls">
    <button class="btn btn-chain" id="btnRunChain" title="Автоматический запуск полной миссии ТЗ">⚡ Запуск цепочки ТЗ</button>
    <button class="btn btn-primary" id="btnTakeoff">🚀 Взлет (1.2м)</button>
    <button class="btn" id="btnLand">🛬 Посадка</button>
    <button class="btn btn-success" id="btnPayload">💡 Тест LED (2с)</button>
    <button class="btn" id="btnToggleSlam">🗺️ SLAM</button>
    <button class="btn" id="btnToggleLegend">📋 Справка ТЗ</button>
    <button class="btn" id="btnToggleLabels">🏷️ 3D-Метки</button>
    <button class="btn" id="btnRandomize" title="Сгенерировать новую расстановку">🎲 Новые цели</button>
    <button class="btn" id="btnReset">🔄 Сброс</button>
    <button class="btn btn-icon" id="btnHelp" title="Подсказка управления">⌨️</button>
  </div>'''

text = text.replace(old_dock, new_dock, 1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Topbar and bottom dock alignment fixed successfully!")
