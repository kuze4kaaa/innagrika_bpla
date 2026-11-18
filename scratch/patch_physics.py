# -*- coding: utf-8 -*-
with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = '    function updateDronePhysics(st, obj, isControlled, dt) {\n      if (dt > 0.06) dt = 0.06;\n'
end_marker = '      } else if (st.autoPilot) {\n        const wp = st.waypoints[st.autoIdx];'

s_idx = text.find(start_marker)
e_idx = text.find(end_marker, s_idx)

print('Start index:', s_idx, 'End index:', e_idx)

if s_idx != -1 and e_idx != -1:
    new_code = '''    function updateDronePhysics(st, obj, isControlled, dt) {
      if (dt > 0.06) dt = 0.06;

      let localAx = 0, localAy = 0, yawRate = 0;

      // 1. Непрерывное сканирование поля сенсором камеры и закрашивание 2D SLAM-карты
      if (st.role === 'recon' && (st.autoPilot || st.z > 0.15)) {
        updateSlamScan(st.x, st.y, st.z);
        if (obj.cameraFrustum) obj.cameraFrustum.visible = true;
      } else if (st.role === 'recon' && st.z <= 0.12 && !st.autoPilot) {
        if (obj.cameraFrustum) obj.cameraFrustum.visible = false;
      }

      // 2. Обнаружение меток камерой БПЛА-1
      if (st.role === 'recon' && (st.autoPilot || st.z > 0.15)) {
        targetMeshes.forEach(tm => {
          const t = tm.data;
          if (!t.discovered) {
            const dx = st.x - t.x;
            const dy = st.y - t.y;
            const dist2D = Math.sqrt(dx * dx + dy * dy);
            const maxDetectDist = (t.type === 'A_NFZ') ? 1.55 : 0.85;

            if (dist2D <= maxDetectDist) {
              t.discovered = true;
              let col = 0x22c55e;
              if (t.type === 'B') col = 0x3b82f6;
              if (t.type === 'U') col = 0xa855f7;
              if (t.type === 'A_NFZ') col = 0xef4444;

              tm.ringMesh.material.color.setHex(col);
              tm.ringMesh.material.opacity = 0.95;
              tm.dotMesh.material.color.setHex(col);
              tm.dotMesh.material.opacity = 1.0;

              st.memory.push(t);
              updateHUDDiscoveredCount(st.memory.length);
              showDiscoveryToast(t);

              // В реальном времени обновляем идеальный маршрут Исполнителя на основе открытых точек!
              planExecutorMissionFromMemory();
            }
          }
        });
      }

      if (isControlled && !st.autoPilot) {
        if (controlMode === 'motor_mixer') {
          // --- Прокачанное ручное управление: 4-моторный микшер RPM (6-DOF) ---
          const u0 = motorRPM[0] / 100.0; // M1: Перед-Л (CCW)
          const u1 = motorRPM[1] / 100.0; // M2: Перед-П (CW)
          const u2 = motorRPM[2] / 100.0; // M3: Зад-П (CCW)
          const u3 = motorRPM[3] / 100.0; // M4: Зад-Л (CW)

          const mg = 9.81;
          const hoverPerMotor = mg / 4.0;
          const t0 = (u0 / 0.5) * (u0 / 0.5) * hoverPerMotor;
          const t1 = (u1 / 0.5) * (u1 / 0.5) * hoverPerMotor;
          const t2 = (u2 / 0.5) * (u2 / 0.5) * hoverPerMotor;
          const t3 = (u3 / 0.5) * (u3 / 0.5) * hoverPerMotor;
          const totalThrust = t0 + t1 + t2 + t3;

          const pitchMoment = (t2 + t3) - (t0 + t1); // Тангаж
          const rollMoment  = (t1 + t2) - (t0 + t3); // Крен
          const yawMoment   = (t0 + t2) - (t1 + t3); // Рыскание

          st.pitch += (pitchMoment * 0.15 - st.pitch) * 8.0 * dt;
          st.roll  += (-rollMoment * 0.15 - st.roll)  * 8.0 * dt;
          yawRate   = yawMoment * 2.5;

          const verticalAccel = (totalThrust * Math.cos(st.pitch) * Math.cos(st.roll) - mg);
          st.targetZ += verticalAccel * 0.35 * dt;
          if (st.targetZ < 0.08) st.targetZ = 0.08;
          if (st.targetZ > 2.4) st.targetZ = 2.4;

          localAx = totalThrust * Math.sin(st.pitch) * 0.22;
          localAy = -totalThrust * Math.sin(st.roll) * 0.22;

          const thrustEl = document.getElementById('motorThrustVal');
          if (thrustEl) thrustEl.textContent = `Тяга Fz: ${totalThrust.toFixed(2)} Н (G=9.81Н)`;
          const torqueEl = document.getElementById('motorTorqueVal');
          if (torqueEl) torqueEl.textContent = `Углы: ${(st.pitch*180/Math.PI).toFixed(1)}° / ${(st.roll*180/Math.PI).toFixed(1)}°`;

          if (obj.propellers && obj.propellers.length >= 4) {
            obj.propellers[0].rotation.z += (motorRPM[0] * 0.9) * dt;
            obj.propellers[1].rotation.z -= (motorRPM[1] * 0.9) * dt;
            obj.propellers[2].rotation.z += (motorRPM[2] * 0.9) * dt;
            obj.propellers[3].rotation.z -= (motorRPM[3] * 0.9) * dt;
          }
        } else {
          // Стандартный полетный контроллер (WASD)
          if (keys['w']) localAx += 1.4;
          if (keys['s']) localAx -= 1.4;
          if (keys['a'] || keys['arrowleft']) yawRate += 2.0;
          if (keys['d'] || keys['arrowright']) yawRate -= 2.0;
          if (keys['z']) localAy += 1.4;
          if (keys['c']) localAy -= 1.4;
          if (keys['space'] || keys['q']) st.targetZ += 0.7 * dt;
          if (keys['shiftleft'] || keys['shiftright'] || keys['e']) st.targetZ -= 0.7 * dt;
        }
'''
    text = text[:s_idx] + new_code + '      } else if (st.autoPilot) {\n        const wp = st.waypoints[st.autoIdx];' + text[e_idx + len(end_marker):]

    with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print('SUCCESSFULLY PATCHED PHYSICS!')
else:
    print('ERROR: markers not found!')
