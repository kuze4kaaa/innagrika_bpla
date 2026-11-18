"""
Обновление квадрокоптеров, распыления биопрепарата, 3D-тегов дронов,
логики обновления спрайтов при обнаружении и обработке,
и пресетов камер.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update executor payload in buildQuadcopter
old_exec_payload = '''      } else {
        const lamp = new THREE.Mesh(
          new THREE.CylinderGeometry(0.018, 0.018, 0.008, 16),
          new THREE.MeshBasicMaterial({ color: 0x334155 })
        );
        lamp.rotation.x = Math.PI / 2;
        lamp.position.set(0, 0, -0.01);
        droneBody.add(lamp);
        payloadLamp = lamp;

        payloadSpot = new THREE.SpotLight(0x22c55e, 0, 4.0, Math.PI / 7, 0.4, 1.2);
        payloadSpot.position.set(0, 0, -0.02);
        payloadSpot.target.position.set(0, 0, -1);
        droneBody.add(payloadSpot);
        droneBody.add(payloadSpot.target);
      }'''

new_exec_payload = '''      } else {
        // --- ОБОРУДОВАНИЕ БПЛА-2 (ИСПОЛНИТЕЛЬ): БАК БИОПРЕПАРАТА + ФОРСУНКА ---
        // 1. Бак для жидкого препарата на верхней палубе дрона
        const tankGeo = new THREE.CylinderGeometry(0.038, 0.038, 0.048, 16);
        const tankMat = new THREE.MeshStandardMaterial({
          color: 0x15803d, // Зеленый агрохимический биопрепарат
          transparent: true,
          opacity: 0.82,
          roughness: 0.25,
          metalness: 0.1
        });
        const tankMesh = new THREE.Mesh(tankGeo, tankMat);
        tankMesh.rotation.x = Math.PI / 2;
        tankMesh.position.set(0, 0, 0.045);
        droneBody.add(tankMesh);

        // Крышка заливной горловины бака
        const capGeo = new THREE.CylinderGeometry(0.014, 0.014, 0.01, 12);
        const capMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.5 });
        const capMesh = new THREE.Mesh(capGeo, capMat);
        capMesh.rotation.x = Math.PI / 2;
        capMesh.position.set(0, 0, 0.072);
        droneBody.add(capMesh);

        // Смотровая шкала уровня жидкости
        const gaugeMesh = new THREE.Mesh(
          new THREE.PlaneGeometry(0.008, 0.035),
          new THREE.MeshBasicMaterial({ color: 0x4ade80, side: THREE.DoubleSide })
        );
        gaugeMesh.position.set(0.039, 0, 0.045);
        gaugeMesh.rotation.y = Math.PI / 2;
        droneBody.add(gaugeMesh);

        // 2. Распылительная форсунка со светодиодным индикатором под днищем
        const nozzleGeo = new THREE.CylinderGeometry(0.016, 0.022, 0.016, 16);
        const nozzleMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.8 });
        const nozzleMesh = new THREE.Mesh(nozzleGeo, nozzleMat);
        nozzleMesh.rotation.x = Math.PI / 2;
        nozzleMesh.position.set(0, 0, -0.012);
        droneBody.add(nozzleMesh);

        const lamp = new THREE.Mesh(
          new THREE.CylinderGeometry(0.018, 0.018, 0.008, 16),
          new THREE.MeshBasicMaterial({ color: 0x334155 })
        );
        lamp.rotation.x = Math.PI / 2;
        lamp.position.set(0, 0, -0.022);
        droneBody.add(lamp);
        payloadLamp = lamp;

        // Световой индикатор ТЗ (мощный фокусированный пучок на землю, R=0.04м)
        payloadSpot = new THREE.SpotLight(0x22c55e, 0, 4.0, Math.PI / 8, 0.25, 1.0);
        payloadSpot.position.set(0, 0, -0.025);
        payloadSpot.target.position.set(0, 0, -1);
        droneBody.add(payloadSpot);
        droneBody.add(payloadSpot.target);

        // 3. Система частиц микродисперсного тумана / агроспрея
        const mistCount = 60;
        const mistGeo = new THREE.BufferGeometry();
        const mistPos = new Float32Array(mistCount * 3);
        for (let i = 0; i < mistCount * 3; i += 3) {
          mistPos[i] = (Math.random() - 0.5) * 0.04;
          mistPos[i + 1] = (Math.random() - 0.5) * 0.04;
          mistPos[i + 2] = -0.02 - Math.random() * 1.15;
        }
        mistGeo.setAttribute('position', new THREE.BufferAttribute(mistPos, 3));
        const mistMat = new THREE.PointsMaterial({
          color: 0x4ade80,
          size: 0.022,
          transparent: true,
          opacity: 0,
          depthWrite: false
        });
        const mistPoints = new THREE.Points(mistGeo, mistMat);
        droneBody.add(mistPoints);
        droneBody.userData.mistPoints = mistPoints;
      }'''

text = text.replace(old_exec_payload, new_exec_payload, 1)

# 2. Add floating 3D badge for drone inside buildQuadcopter
old_drone_return = '''      return {
        group: droneRig,
        body: droneBody,
        propellers: propellers,
        payloadSpot: payloadSpot,
        payloadLamp: payloadLamp,
        cameraFrustum: cameraFrustum,
        frustumPyrGeo: frustumPyrGeo,
        frustumLineGeo: frustumLineGeo,
        frustumFootprintGeo: frustumFootprintGeo,
        shadow: shadow
      };'''

new_drone_return = '''      // 3D-плавающая бирка над дроном
      const droneTagTitle = isRecon ? 'БПЛА-1 (РАЗВЕДЧИК)' : 'БПЛА-2 (ИСПОЛНИТЕЛЬ)';
      const droneTagSub = isRecon ? '📷 Камера 4K · Съемка посевов' : '💧 Бак биопрепарата + Форсунка';
      const droneTagColor = isRecon ? '#ea580c' : '#15803d';
      const droneTagIcon = isRecon ? '🚁' : '🛸';
      const droneTagSprite = createBillboardSprite(droneTagTitle, droneTagSub, droneTagColor, droneTagIcon, 300, 78);
      droneTagSprite.position.set(0, 0, 0.22);
      droneRig.add(droneTagSprite);

      return {
        group: droneRig,
        body: droneBody,
        propellers: propellers,
        payloadSpot: payloadSpot,
        payloadLamp: payloadLamp,
        cameraFrustum: cameraFrustum,
        frustumPyrGeo: frustumPyrGeo,
        frustumLineGeo: frustumLineGeo,
        frustumFootprintGeo: frustumFootprintGeo,
        shadow: shadow,
        tagSprite: droneTagSprite
      };'''

text = text.replace(old_drone_return, new_drone_return, 1)

# 3. Update discovery and treatment handling in updateDronePhysics
old_discovery_code = '''            if (dist2D <= maxDetectDist) {
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
            }'''

new_discovery_code = '''            if (dist2D <= maxDetectDist) {
              t.discovered = true;
              let col = 0x22c55e;
              let title = `ОЧАГ A-${t.id} (СОРНЯК)`;
              let sub = '⚠️ Требуется опрыскивание 2.0с (R=0.25м)';
              let colStr = '#f97316';
              let ico = '🎯';

              if (t.type === 'B') {
                col = 0x3b82f6;
                title = 'УЧАСТОК B (КУЛЬТУРА)';
                sub = '🌿 Здоровая культура · Без химии';
                colStr = '#3b82f6';
                ico = '🌿';
              } else if (t.type === 'U') {
                col = 0xa855f7;
                title = 'УЧАСТОК U (НЕОПРЕДЕЛЕНО)';
                sub = '❓ Сомнительный спектр · Пропуск по ТЗ';
                colStr = '#a855f7';
                ico = '❓';
              } else if (t.type === 'A_NFZ') {
                col = 0xef4444;
                title = `ОЧАГ A-${t.id} (В ЗОНЕ NFZ)`;
                sub = '⛔ Влёт и обработка ЗАПРЕЩЕНЫ ТЗ!';
                colStr = '#ef4444';
                ico = '🚫';
              }

              tm.ringMesh.material.color.setHex(col);
              tm.ringMesh.material.opacity = 0.95;
              tm.dotMesh.material.color.setHex(col);
              tm.dotMesh.material.opacity = 1.0;

              if (tm.sprite) {
                tm.sprite.material.opacity = 1.0;
                tm.sprite.update(title, sub, colStr, ico);
              }

              st.memory.push(t);
              updateHUDDiscoveredCount(st.memory.length);
              showDiscoveryToast(t);

              // В реальном времени обновляем идеальный маршрут Исполнителя на основе открытых точек!
              planExecutorMissionFromMemory();
            }'''

text = text.replace(old_discovery_code, new_discovery_code, 1)

# 4. Update treatment in updateDronePhysics: mist particles and sprite update
old_treatment_code = '''      if (st.role === 'executor' && st.payloadActive) {
        st.payloadTimeLeft -= dt;
        if (st.payloadTimeLeft <= 0) {
          st.payloadActive = false;
          st.payloadTimeLeft = 0;
          obj.payloadLamp.material.color.setHex(0x334155);
          obj.payloadSpot.intensity = 0;

          // Пометить обработанный очаг в 3D (солидная зеленая метка обработки):
          const currWp = st.waypoints[st.autoIdx];
          if (currWp && currWp.targetId) {
            const tm = targetMeshes.find(m => m.data.id === currWp.targetId);
            if (tm) {
              tm.data.treated = true;
              tm.ringMesh.material.color.setHex(0x22c55e);
              tm.dotMesh.material.color.setHex(0x4ade80);
              tm.dotMesh.scale.set(3.5, 3.5, 1);
            }
          }

          if (isControlled) {
            document.getElementById('payloadLed').classList.remove('active');
            document.getElementById('payloadText').textContent = 'ГОТОВ';
          }
        } else if (isControlled) {
          document.getElementById('payloadText').textContent = `АКТИВНА (${st.payloadTimeLeft.toFixed(1)}с)`;
        }
      }'''

new_treatment_code = '''      if (st.role === 'executor' && st.payloadActive) {
        st.payloadTimeLeft -= dt;

        // Анимация частиц агрораспыления тумана
        if (obj.body.userData.mistPoints) {
          const mp = obj.body.userData.mistPoints;
          mp.material.opacity = 0.85;
          const posArr = mp.geometry.attributes.position.array;
          const mistH = Math.max(st.z, 0.1);
          for (let i = 2; i < posArr.length; i += 3) {
            posArr[i] -= 3.5 * dt;
            if (posArr[i] < -mistH) {
              posArr[i] = -0.02;
              posArr[i - 2] = (Math.random() - 0.5) * 0.04;
              posArr[i - 1] = (Math.random() - 0.5) * 0.04;
            }
          }
          mp.geometry.attributes.position.needsUpdate = true;
        }

        if (obj.tagSprite) {
          obj.tagSprite.update('БПЛА-2 (ОПРЫСКИВАНИЕ)', `💧 Внесение биопрепарата (${st.payloadTimeLeft.toFixed(1)}с)`, '#22c55e', '💡');
        }

        if (st.payloadTimeLeft <= 0) {
          st.payloadActive = false;
          st.payloadTimeLeft = 0;
          obj.payloadLamp.material.color.setHex(0x334155);
          obj.payloadSpot.intensity = 0;

          if (obj.body.userData.mistPoints) {
            obj.body.userData.mistPoints.material.opacity = 0;
          }
          if (obj.tagSprite) {
            obj.tagSprite.update('БПЛА-2 (ИСПОЛНИТЕЛЬ)', '💧 Бак биопрепарата + Форсунка', '#15803d', '🛸');
          }

          // Пометить обработанный очаг в 3D:
          const currWp = st.waypoints[st.autoIdx];
          if (currWp && currWp.targetId) {
            const tm = targetMeshes.find(m => m.data.id === currWp.targetId);
            if (tm) {
              tm.data.treated = true;
              tm.ringMesh.material.color.setHex(0x22c55e);
              tm.dotMesh.material.color.setHex(0x4ade80);
              tm.dotMesh.scale.set(3.5, 3.5, 1);
              if (tm.sprite) {
                tm.sprite.update(`ОЧАГ A-${currWp.targetId} ОБРАБОТАН!`, '✅ Биопрепарат внесен (2.0 с)', '#22c55e', '✅');
              }
            }
          }

          if (isControlled) {
            document.getElementById('payloadLed').classList.remove('active');
            document.getElementById('payloadText').textContent = 'ГОТОВ';
          }
        } else if (isControlled) {
          document.getElementById('payloadText').textContent = `АКТИВНА (${st.payloadTimeLeft.toFixed(1)}с)`;
        }
      }'''

text = text.replace(old_treatment_code, new_treatment_code, 1)

# 5. Pipeline synchronization
old_chain_code = '''      showPhaseBanner("ЭТАП 1: БПЛА-Разведчик сканирует полигон галсами (цели скрыты, сканирование в реальном времени...)");
    };'''

new_chain_code = '''      showPhaseBanner("ЭТАП 1: БПЛА-Разведчик сканирует полигон галсами (цели скрыты, сканирование в реальном времени...)");
      updatePipelineStep(1);
    };

    function updatePipelineStep(step) {
      for (let s = 1; s <= 4; s++) {
        const el = document.getElementById('pipe' + s);
        if (el) {
          el.className = 'pipe-step' + ((s === step) ? ' active' : ((s < step) ? ' done' : ''));
        }
      }
    }'''

text = text.replace(old_chain_code, new_chain_code, 1)

# Update stage transitions
text = text.replace("chainStage = 2;", "chainStage = 2;\n                updatePipelineStep(2);", 1)
text = text.replace("chainStage = 3;", "chainStage = 3;\n                  updatePipelineStep(3);", 1)
text = text.replace("chainRunning = false;", "chainRunning = false;\n                updatePipelineStep(4);", 1)

# 6. Add camera preset camCloseTarget and label toggler
cam_and_ui_bindings = '''
    // Переключение видимости 3D-меток
    const btnLabelsToggle = document.getElementById('btnToggleLabels');
    if (btnLabelsToggle) {
      btnLabelsToggle.onclick = () => {
        labelsVisible = !labelsVisible;
        allSceneLabels.forEach(s => s.visible = labelsVisible);
        btnLabelsToggle.textContent = labelsVisible ? '🏷️ 3D-Метки: ВКЛ' : '🏷️ 3D-Метки: ВЫКЛ';
        btnLabelsToggle.classList.toggle('active', labelsVisible);
      };
    }

    // Кнопка приближения к целевому очагу
    const btnCamClose = document.getElementById('camCloseTarget');
    if (btnCamClose) {
      btnCamClose.onclick = () => {
        setCameraMode('close');
        const targetA = targetMeshes.find(m => m.data.type === 'A') || targetMeshes[0];
        if (targetA) {
          controls.target.set(targetA.data.x, targetA.data.y, 0.15);
          camera.position.set(targetA.data.x + 0.6, targetA.data.y - 0.7, 0.65);
          controls.update();
        }
      };
    }
'''

# Add before window.addEventListener('resize'
text = text.replace("window.addEventListener('resize', () => {", cam_and_ui_bindings + "\n    window.addEventListener('resize', () => {", 1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Pass 3 applied successfully!")
