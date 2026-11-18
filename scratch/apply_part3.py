# -*- coding: utf-8 -*-
with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update generateRandomTargets to reset SLAM grid
old_gen_targets = 'function generateRandomTargets() {\n      targetMeshes.forEach(tm => scene.remove(tm.group));\n      targetMeshes = [];\n      targetsData = [];'
new_gen_targets = '''function generateRandomTargets() {
      targetMeshes.forEach(tm => scene.remove(tm.group));
      targetMeshes = [];
      targetsData = [];

      // Сброс SLAM-сетки и покрытия при генерации новой карты
      if (typeof slamGrid !== 'undefined') {
        slamGrid.fill(0);
        slamCoverage = 0.0;
        slamWallsCount = 0;
        const covBadge = document.getElementById('slamCoverageBadge');
        if (covBadge) covBadge.textContent = 'ПОКРЫТИЕ: 0.0%';
      }'''

text = text.replace(old_gen_targets, new_gen_targets, 1)

# 2. Update setActiveDrone to automatically show 2D SLAM map when Recon is selected
old_set_active = '''    function setActiveDrone(droneNum) {
      if (droneNum === 1) {
        activeDrone = drone1State;
        activeDroneObj = drone1Obj;
        btnSelectRecon.className = 'btn-seg active-recon';
        btnSelectExec.className = 'btn-seg';
        document.getElementById('activeDroneName').textContent = 'БПЛА-1 (Разведчик)';
        document.getElementById('activeDroneName').style.color = '#fdba74';
      } else {
        activeDrone = drone2State;
        activeDroneObj = drone2Obj;
        btnSelectRecon.className = 'btn-seg';
        btnSelectExec.className = 'btn-seg active-exec';
        document.getElementById('activeDroneName').textContent = 'БПЛА-2 (Исполнитель)';
        document.getElementById('activeDroneName').style.color = '#86efac';
      }
    }'''

new_set_active = '''    function setActiveDrone(droneNum) {
      if (droneNum === 1) {
        activeDrone = drone1State;
        activeDroneObj = drone1Obj;
        btnSelectRecon.className = 'btn-seg active-recon';
        btnSelectExec.className = 'btn-seg';
        document.getElementById('activeDroneName').textContent = 'БПЛА-1 (Разведчик)';
        document.getElementById('activeDroneName').style.color = '#fdba74';
        const slamCard = document.getElementById('slamMapCard');
        if (slamCard) slamCard.style.display = 'block';
      } else {
        activeDrone = drone2State;
        activeDroneObj = drone2Obj;
        btnSelectRecon.className = 'btn-seg';
        btnSelectExec.className = 'btn-seg active-exec';
        document.getElementById('activeDroneName').textContent = 'БПЛА-2 (Исполнитель)';
        document.getElementById('activeDroneName').style.color = '#86efac';
      }
    }'''

text = text.replace(old_set_active, new_set_active, 1)

# 3. In updateDronePhysics, call updateSlamScan and implement Motor Mixer mode
old_physics_controls = '''      if (isControlled && !st.autoPilot) {
        // Ручной полет:
        // W/S - полет вперед / назад по текущему курсу носа
        if (keys['w']) localAx += 1.4;
        if (keys['s']) localAx -= 1.4;

        // A/D и стрелки влево/вправо - разворот носа по курсу (Yaw)
        if (keys['a'] || keys['arrowleft']) yawRate += 2.0;
        if (keys['d'] || keys['arrowright']) yawRate -= 2.0;

        // Z/C - боковой крен / стрейф влево-вправо:
        if (keys['z']) localAy += 1.4;
        if (keys['c']) localAy -= 1.4;

        // Space/Q - вверх, Shift/E - вниз:
        if (keys['space'] || keys['q']) st.targetZ += 0.7 * dt;
        if (keys['shiftleft'] || keys['shiftright'] || keys['e']) st.targetZ -= 0.7 * dt;
      } else if (st.autoPilot) {'''

new_physics_controls = '''      // Сканирование сенсором и заполнение SLAM-карты в реальном времени
      if (st.role === 'recon' && (st.autoPilot || st.z > 0.20)) {
        updateSlamScan(st.x, st.y, st.z);
      }

      if (isControlled && !st.autoPilot) {
        if (controlMode === 'motor_mixer') {
          // --- Прокачанное управление: Четырехмоторный микшер тяги (6-DOF) ---
          const u0 = motorRPM[0] / 100.0; // M1: Передний-Левый (CCW)
          const u1 = motorRPM[1] / 100.0; // M2: Передний-Правый (CW)
          const u2 = motorRPM[2] / 100.0; // M3: Задний-Правый (CCW)
          const u3 = motorRPM[3] / 100.0; // M4: Задний-Левый (CW)

          const mg = 9.81;
          const hoverPerMotor = mg / 4.0;
          const t0 = (u0 / 0.5) * (u0 / 0.5) * hoverPerMotor;
          const t1 = (u1 / 0.5) * (u1 / 0.5) * hoverPerMotor;
          const t2 = (u2 / 0.5) * (u2 / 0.5) * hoverPerMotor;
          const t3 = (u3 / 0.5) * (u3 / 0.5) * hoverPerMotor;
          const totalThrust = t0 + t1 + t2 + t3;

          // Дифференциальные аэродинамические моменты
          // Тангаж (Pitch): задние моторы тянут сильнее -> нос опускается -> полет вперед!
          const pitchMoment = (t2 + t3) - (t0 + t1);
          // Крен (Roll): правые моторы тянут сильнее -> левое крыло опускается -> полет влево!
          const rollMoment  = (t1 + t2) - (t0 + t3);
          // Рыскание (Yaw): реактивный момент вращения винтов
          const yawMoment   = (t0 + t2) - (t1 + t3);

          st.pitch += (pitchMoment * 0.15 - st.pitch) * 8.0 * dt;
          st.roll  += (-rollMoment * 0.15 - st.roll)  * 8.0 * dt;
          yawRate   = yawMoment * 2.5;

          // Вертикальное движение от тяги моторов
          const verticalAccel = (totalThrust * Math.cos(st.pitch) * Math.cos(st.roll) - mg);
          st.targetZ += verticalAccel * 0.35 * dt;
          if (st.targetZ < 0.08) st.targetZ = 0.08;
          if (st.targetZ > 2.4) st.targetZ = 2.4;

          // Горизонтальное ускорение от наклона вектора тяги
          localAx = totalThrust * Math.sin(st.pitch) * 0.22;
          localAy = -totalThrust * Math.sin(st.roll) * 0.22;

          // Телеметрия моторов
          const thrustEl = document.getElementById('motorThrustVal');
          if (thrustEl) thrustEl.textContent = `Тяга Fz: ${totalThrust.toFixed(2)} Н (G=9.81Н)`;
          const torqueEl = document.getElementById('motorTorqueVal');
          if (torqueEl) torqueEl.textContent = `Углы: ${(st.pitch*180/Math.PI).toFixed(1)}° / ${(st.roll*180/Math.PI).toFixed(1)}°`;

          // Вращение пропеллеров в 3D пропорционально RPM моторов
          if (obj.propellers && obj.propellers.length >= 4) {
            obj.propellers[0].rotation.z += (motorRPM[0] * 0.9) * dt;
            obj.propellers[1].rotation.z -= (motorRPM[1] * 0.9) * dt;
            obj.propellers[2].rotation.z += (motorRPM[2] * 0.9) * dt;
            obj.propellers[3].rotation.z -= (motorRPM[3] * 0.9) * dt;
          }
        } else {
          // Стандартный полетный контроллер (WASD):
          if (keys['w']) localAx += 1.4;
          if (keys['s']) localAx -= 1.4;
          if (keys['a'] || keys['arrowleft']) yawRate += 2.0;
          if (keys['d'] || keys['arrowright']) yawRate -= 2.0;
          if (keys['z']) localAy += 1.4;
          if (keys['c']) localAy -= 1.4;
          if (keys['space'] || keys['q']) st.targetZ += 0.7 * dt;
          if (keys['shiftleft'] || keys['shiftright'] || keys['e']) st.targetZ -= 0.7 * dt;
        }
      } else if (st.autoPilot) {'''

text = text.replace(old_physics_controls, new_physics_controls, 1)

# 4. In updateDronePhysics, update GCS handover phase 2 banner to mention 100% SLAM survey & obstacles
old_gcs_phase = "showPhaseBanner(`Фаза 2 (GCS): Расчет карты (${drone1State.memory.length}/10 целей). 2 цели в NFZ отсеяны, 2 сорняка отсеяны. Принято ${acceptedCount} очагов A. Подготовка маршрута Исполнителя!`);"
new_gcs_phase = "showPhaseBanner(`Фаза 2 (GCS): 100% территории обследовано! Фигуры стен и внутренние объемы заблокированы. Принято ${acceptedCount} валидных очагов Класса A. Передача данных БПЛА-2!`);"

text = text.replace(old_gcs_phase, new_gcs_phase, 1)

# 5. Add UI Event Listeners for Motor Controls and SLAM Toggle before 'btnToggleRoute.onclick'
motor_and_slam_listeners = '''    // --- Слушатели управления 4 моторами (RPM) ---
    function updateMotorUI() {
      for (let i = 0; i < 4; i++) {
        const slider = document.getElementById(`m${i+1}Slider`);
        const valSpan = document.getElementById(`m${i+1}Val`);
        if (slider) slider.value = motorRPM[i];
        if (valSpan) valSpan.textContent = `${motorRPM[i]}% (${(motorRPM[i] * 120).toFixed(0)})`;
      }
    }

    for (let i = 0; i < 4; i++) {
      const slider = document.getElementById(`m${i+1}Slider`);
      if (slider) {
        slider.oninput = (e) => {
          motorRPM[i] = parseInt(e.target.value);
          updateMotorUI();
        };
      }
    }

    const btnHover50 = document.getElementById('btnHover50');
    if (btnHover50) btnHover50.onclick = () => { motorRPM.fill(50); updateMotorUI(); };

    const btnThrotUp = document.getElementById('btnThrotUp');
    if (btnThrotUp) btnThrotUp.onclick = () => {
      for (let i = 0; i < 4; i++) motorRPM[i] = Math.min(motorRPM[i] + 5, 100);
      updateMotorUI();
    };

    const btnThrotDn = document.getElementById('btnThrotDn');
    if (btnThrotDn) btnThrotDn.onclick = () => {
      for (let i = 0; i < 4; i++) motorRPM[i] = Math.max(motorRPM[i] - 5, 0);
      updateMotorUI();
    };

    const btnStopMotors = document.getElementById('btnStopMotors');
    if (btnStopMotors) btnStopMotors.onclick = () => { motorRPM.fill(0); updateMotorUI(); };

    const btnNoseDown = document.getElementById('btnNoseDown');
    if (btnNoseDown) btnNoseDown.onclick = () => {
      motorRPM[0] = Math.max(motorRPM[0] - 4, 0);
      motorRPM[1] = Math.max(motorRPM[1] - 4, 0);
      motorRPM[2] = Math.min(motorRPM[2] + 4, 100);
      motorRPM[3] = Math.min(motorRPM[3] + 4, 100);
      updateMotorUI();
    };

    const btnNoseUp = document.getElementById('btnNoseUp');
    if (btnNoseUp) btnNoseUp.onclick = () => {
      motorRPM[0] = Math.min(motorRPM[0] + 4, 100);
      motorRPM[1] = Math.min(motorRPM[1] + 4, 100);
      motorRPM[2] = Math.max(motorRPM[2] - 4, 0);
      motorRPM[3] = Math.max(motorRPM[3] - 4, 0);
      updateMotorUI();
    };

    const btnRollL = document.getElementById('btnRollL');
    if (btnRollL) btnRollL.onclick = () => {
      motorRPM[0] = Math.max(motorRPM[0] - 4, 0);
      motorRPM[3] = Math.max(motorRPM[3] - 4, 0);
      motorRPM[1] = Math.min(motorRPM[1] + 4, 100);
      motorRPM[2] = Math.min(motorRPM[2] + 4, 100);
      updateMotorUI();
    };

    const btnRollR = document.getElementById('btnRollR');
    if (btnRollR) btnRollR.onclick = () => {
      motorRPM[0] = Math.min(motorRPM[0] + 4, 100);
      motorRPM[3] = Math.min(motorRPM[3] + 4, 100);
      motorRPM[1] = Math.max(motorRPM[1] - 4, 0);
      motorRPM[2] = Math.max(motorRPM[2] - 4, 0);
      updateMotorUI();
    };

    const btnToggleMotors = document.getElementById('btnToggleMotors');
    const motorPanel = document.getElementById('motorPanel');
    if (btnToggleMotors) {
      btnToggleMotors.onclick = () => {
        if (controlMode === 'flight_controller') {
          controlMode = 'motor_mixer';
          btnToggleMotors.textContent = '🎛️ Моторы (RPM): ВКЛ';
          btnToggleMotors.className = 'btn btn-active-toggle';
          if (motorPanel) motorPanel.style.display = 'block';
          if (motorRPM.every(v => v === 0)) {
            motorRPM.fill(50);
            updateMotorUI();
          }
        } else {
          controlMode = 'flight_controller';
          btnToggleMotors.textContent = '🎛️ Моторы (RPM): ВЫКЛ';
          btnToggleMotors.className = 'btn';
          if (motorPanel) motorPanel.style.display = 'none';
        }
      };
    }

    const motorCloseBtn = document.getElementById('motorCloseBtn');
    if (motorCloseBtn) {
      motorCloseBtn.onclick = () => {
        controlMode = 'flight_controller';
        if (btnToggleMotors) {
          btnToggleMotors.textContent = '🎛️ Моторы (RPM): ВЫКЛ';
          btnToggleMotors.className = 'btn';
        }
        if (motorPanel) motorPanel.style.display = 'none';
      };
    }

    // --- Переключение 2D SLAM-карты ---
    const btnToggleSlam = document.getElementById('btnToggleSlam');
    const slamMapCard = document.getElementById('slamMapCard');
    if (btnToggleSlam && slamMapCard) {
      btnToggleSlam.onclick = () => {
        if (slamMapCard.style.display === 'none') {
          slamMapCard.style.display = 'block';
          btnToggleSlam.className = 'btn btn-active-toggle';
          btnToggleSlam.textContent = '🗺️ 2D Карта SLAM: ВКЛ';
        } else {
          slamMapCard.style.display = 'none';
          btnToggleSlam.className = 'btn';
          btnToggleSlam.textContent = '🗺️ 2D Карта SLAM: ВЫКЛ';
        }
      };
    }
'''

text = text.replace('const btnToggleRoute = document.getElementById(\'btnToggleRoute\');',
                    motor_and_slam_listeners + '\n    const btnToggleRoute = document.getElementById(\'btnToggleRoute\');', 1)

# 6. In animate(), call renderSlamMap()
old_anim_render = '''      updateCamera();
      updateHUD();
      renderer.render(scene, camera);'''

new_anim_render = '''      updateCamera();
      updateHUD();
      if (typeof renderSlamMap === 'function') {
        renderSlamMap();
      }
      renderer.render(scene, camera);'''

text = text.replace(old_anim_render, new_anim_render, 1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Applied Part 3 (SLAM scan, Motor mixer physics, UI listeners, animate render)!')
