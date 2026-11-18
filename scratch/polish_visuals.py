"""
Тонкая полировка визуализации:
1. Корректировка отступа mission-phase-banner (top: 115px), чтобы не перекрывал пошаговый пайплайн.
2. Скрытие тега дрона, когда он находится на посадочной площадке (st.z < 0.15), чтобы исключить наложение на вывеску базы.
3. Идеальный ракурс камеры «3D Поле» (изометрия всего полигона 6х4 м без перекрытия переднего плана).
4. Проверка и полировка стилей.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Adjust mission-phase-banner CSS
old_banner_css = '''.mission-phase-banner {
      position: absolute;
      top: 60px;'''

new_banner_css = '''.mission-phase-banner {
      position: absolute;
      top: 114px;'''

text = text.replace(old_banner_css, new_banner_css, 1)

# 2. Adjust camOrbit click handler
old_orbit_code = '''    document.getElementById('camOrbit').onclick = () => {
      setCameraMode('orbit');
      controls.target.set(3, 2, 0.5);
    };'''

new_orbit_code = '''    document.getElementById('camOrbit').onclick = () => {
      setCameraMode('orbit');
      controls.target.set(3.0, 2.0, 0.4);
      camera.position.set(3.0, -3.2, 4.0);
      controls.update();
    };'''

text = text.replace(old_orbit_code, new_orbit_code, 1)

# 3. In animate() loop or updateDronePhysics: hide drone tag when on ground
old_drone_pos_code = '''      // 1. Позиционирование и поворот по рысканию родительского узла droneRig:
      obj.group.position.set(st.x, st.y, st.z);
      obj.group.rotation.set(0, 0, st.yaw);'''

new_drone_pos_code = '''      // 1. Позиционирование и поворот по рысканию родительского узла droneRig:
      obj.group.position.set(st.x, st.y, st.z);
      obj.group.rotation.set(0, 0, st.yaw);

      // Скрываем бирку дрона при посадке на базу (чтобы не перекрывать вывеску базы H1/H2)
      if (obj.tagSprite) {
        obj.tagSprite.visible = labelsVisible && (st.z >= 0.15);
      }'''

text = text.replace(old_drone_pos_code, new_drone_pos_code, 1)

# 4. In btnRandomize / generateRandomTargets: ensure pipeline reset
old_rand_code = '''    document.getElementById('btnRandomize').onclick = () => {
      generateRandomTargets();
      planExecutorMissionFromMemory();
    };'''

new_rand_code = '''    document.getElementById('btnRandomize').onclick = () => {
      generateRandomTargets();
      planExecutorMissionFromMemory();
      updatePipelineStep(1);
    };'''

text = text.replace(old_rand_code, new_rand_code, 1)

# 5. In btnReset: ensure pipeline step reset
old_reset_code = '''    document.getElementById('btnReset').onclick = () => {
      drone1State.autoPilot = false;'''

new_reset_code = '''    document.getElementById('btnReset').onclick = () => {
      updatePipelineStep(1);
      drone1State.autoPilot = false;'''

text = text.replace(old_reset_code, new_reset_code, 1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Polish applied successfully!")
