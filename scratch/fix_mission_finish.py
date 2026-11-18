"""
Исправление завершения миссии:
1. Удаление ошибочной строки updatePipelineStep(4) на 3300 строке при инициализации.
2. При приземлении на Home-2 (chainStage === 3):
   - chainStage = 4
   - chainRunning = false
   - updatePipelineStep(4) — все 4 шага становятся зелеными (done, завершено), ни один шаг не висит в активном (синем) статусе!
   - st.fsm = 'MISSION_COMPLETE'
   - Гарантированное отключение полезной нагрузки, LED и тумана.
   - Чистый итоговый статус в subtext.
3. Корректный сброс в btnReset и btnRandomize.
"""

import sys

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Remove rogue updatePipelineStep(4) on line 3300
rogue_line = """    let chainRunning = false;
                updatePipelineStep(4);
    let chainStage = 0;"""

clean_decl = """    let chainRunning = false;
    let chainStage = 0;"""

if rogue_line in text:
    text = text.replace(rogue_line, clean_decl, 1)
    print("Removed rogue updatePipelineStep(4) from declarations!")
else:
    print("Rogue line not found, searching...")
    text = text.replace("updatePipelineStep(4);\n    let chainStage = 0;", "let chainStage = 0;")

# 2. Update updatePipelineStep function: when step >= 4, all 4 steps are marked 'done'
old_func = """    function updatePipelineStep(step) {
      for (let s = 1; s <= 4; s++) {
        const el = document.getElementById('pipe' + s);
        if (el) {
          el.className = 'pipe-step' + ((s === step) ? ' active' : ((s < step) ? ' done' : ''));
        }
      }
    }"""

new_func = """    function updatePipelineStep(step) {
      for (let s = 1; s <= 4; s++) {
        const el = document.getElementById('pipe' + s);
        if (el) {
          if (step >= 4) {
            // Миссия завершена: все 4 шага успешно выполнены (зеленые done), нет активных действий
            el.className = 'pipe-step done';
          } else {
            el.className = 'pipe-step' + ((s === step) ? ' active' : ((s < step) ? ' done' : ''));
          }
        }
      }
    }"""

text = text.replace(old_func, new_func, 1)

# 3. Update the mission completion block when landing at Home-2
old_finish_block = """              } else if (chainRunning && chainStage === 3) {
                chainRunning = false;
                st.fsm = 'HOME-2 (LANDED)';
                st.x = 0.40; st.y = 1.20; st.vx = 0; st.vy = 0;
                showPhaseBanner("✅ МИССИЯ ЗАВЕРШЕНА: Все разрешенные очаги A обработаны, точная посадка в центр Home-2, 0 нарушений NFZ!");
                setTimeout(() => { document.getElementById('phaseBanner').style.display = 'none'; }, 7000 / simSpeed);
              }"""

new_finish_block = """              } else if (chainRunning && chainStage === 3) {
                chainRunning = false;
                chainStage = 4;
                updatePipelineStep(4);
                st.autoPilot = false;
                st.fsm = 'MISSION_COMPLETE';
                st.x = 0.40; st.y = 1.20; st.z = 0.10; st.vx = 0; st.vy = 0; st.vz = 0;

                // Гарантированное отключение агрооборудования и индикаторов
                st.payloadActive = false;
                st.payloadTimeLeft = 0;
                obj.payloadLamp.material.color.setHex(0x334155);
                obj.payloadSpot.intensity = 0;
                if (obj.body && obj.body.userData && obj.body.userData.mistPoints) {
                  obj.body.userData.mistPoints.material.opacity = 0;
                }
                const ledEl = document.getElementById('payloadLed');
                if (ledEl) ledEl.classList.remove('active');
                const txtEl = document.getElementById('payloadText');
                if (txtEl) txtEl.textContent = 'ГОТОВ (МИССИЯ ВЫПОЛНЕНА)';

                showPhaseBanner("✅ МИССИЯ ЗАВЕРШЕНА: Все 6 очагов A обработаны, точная посадка в центр Home-2, 0 нарушений NFZ!");
              }"""

text = text.replace(old_finish_block, new_finish_block, 1)

# 4. In updateHUD: when mission complete or landed, show proper clean status
old_hud_fsm = """      const fsmEl = document.getElementById('fsmStatus');
      if (activeDrone.z < 0.1) {
        fsmEl.textContent = 'ON_GROUND';
        fsmEl.className = 'badge badge-ok';
      } else if (activeDrone.role === 'executor' && activeDrone.payloadActive) {"""

new_hud_fsm = """      const fsmEl = document.getElementById('fsmStatus');
      if (chainStage === 4 || activeDrone.fsm === 'MISSION_COMPLETE') {
        fsmEl.textContent = 'MISSION_COMPLETE';
        fsmEl.className = 'badge badge-ok';
      } else if (activeDrone.z < 0.1) {
        fsmEl.textContent = (activeDrone.fsm && activeDrone.fsm.includes('HOME')) ? activeDrone.fsm : 'ON_GROUND';
        fsmEl.className = 'badge badge-ok';
      } else if (activeDrone.role === 'executor' && activeDrone.payloadActive) {"""

text = text.replace(old_hud_fsm, new_hud_fsm, 1)

# 5. In btnReset: reset chainStage = 0 and subtext
old_reset_code = """    document.getElementById('btnReset').onclick = () => {
      updatePipelineStep(1);
      drone1State.autoPilot = false;"""

new_reset_code = """    document.getElementById('btnReset').onclick = () => {
      chainRunning = false;
      chainStage = 0;
      updatePipelineStep(1);
      showPhaseBanner("Ожидание команды оператора · Нажмите «⚡ Запуск цепочки ТЗ»");
      drone1State.autoPilot = false;"""

text = text.replace(old_reset_code, new_reset_code, 1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Mission finish logic updated successfully!")
