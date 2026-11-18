import sys

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's inspect the topbar HTML
old_topbar_html = '''  <div class="topbar">
    <div class="topbar-left">
      <div class="brand-card">
        <div class="brand-title">ИННАГРИКА 2026 · АТ11-2</div>
        <div class="brand-sub">Полигон 6 × 4 м · 2 зоны NFZ</div>
      </div>

      <div class="segmented-group">
        <button class="btn-seg active-recon" id="selectRecon">
          🚁 БПЛА-1 (Разведчик)
        </button>
        <button class="btn-seg" id="selectExec">
          🛸 БПЛА-2 (Исполнитель)
        </button>
      </div>

      <div class="cam-group">
        <button class="btn-cam-mini active" id="camTrack" title="Слежение за активным дроном">🎯 Слежение</button>
        <button class="btn-cam-mini" id="camOrbit" title="Изометрия полигона">📐 3D Поле</button>
        <button class="btn-cam-mini" id="camTop" title="Вид сверху (F-сетка)">🗺️ Сетка F</button>
        <button class="btn-cam-mini" id="camFpv" title="Бортовая камера">📷 FPV</button>
        <button class="btn-cam-mini" id="camCloseTarget" title="Крупный план очага A">🔍 Очаг A</button>
      </div>

      <div class="speed-group" title="Скорость симуляции">
        <button class="btn-speed active" id="spd1">1×</button>
        <button class="btn-speed" id="spd2">2×</button>
        <button class="btn-speed" id="spd4">4×</button>
        <button class="btn-speed" id="spd8">8×</button>
      </div>
    </div>'''

new_topbar_html = '''  <div class="topbar">
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
    </div>'''

text = text.replace(old_topbar_html, new_topbar_html, 1)

# Put drone switcher in topbar-right right above or next to telemetry
old_topbar_right = '''    <div class="topbar-right">
      <div class="telemetry-card">'''

new_topbar_right = '''    <div class="topbar-right" style="display:flex; flex-direction:column; align-items:flex-end; gap:6px;">
      <div class="segmented-group">
        <button class="btn-seg active-recon" id="selectRecon">
          🚁 БПЛА-1
        </button>
        <button class="btn-seg" id="selectExec">
          🛸 БПЛА-2
        </button>
      </div>
      <div class="telemetry-card">'''

text = text.replace(old_topbar_right, new_topbar_right, 1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Topbar layout streamlined!")
