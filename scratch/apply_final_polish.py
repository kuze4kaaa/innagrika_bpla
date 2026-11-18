with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update updatePipelineStep
old_fn = """    function updatePipelineStep(step) {
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

new_fn = """    function updatePipelineStep(step) {
      for (let s = 1; s <= 4; s++) {
        const el = document.getElementById('pipe' + s);
        if (el) {
          if (step >= 4) {
            // Миссия завершена: все 4 шага успешно выполнены (зеленые done), ни один шаг не активен
            el.className = 'pipe-step done';
          } else {
            el.className = 'pipe-step' + ((s === step) ? ' active' : ((s < step) ? ' done' : ''));
          }
        }
      }
      const p4Span = document.querySelector('#pipe4 span');
      if (p4Span) {
        p4Span.textContent = (step >= 4) ? '🏁 4. Завершено' : '🏁 4. Финиш';
      }
    }"""

if old_fn in content:
    content = content.replace(old_fn, new_fn)
    print("Replaced updatePipelineStep")
else:
    print("updatePipelineStep not matched, checking...")

# 2. Check isFinalLandingWp landing logic
old_landing = """          } else if (isFinalLandingWp) {
            // Строгое вертикальное приземление точно в центр Home площадки
            st.x += (wp.x - st.x) * 12.0 * dt;
            st.y += (wp.y - st.y) * 12.0 * dt;
            st.vx = 0;
            st.vy = 0;
            st.yaw += (0 - st.yaw) * 8.0 * dt;
            st.targetZ = 0.08;

            if (Math.abs(st.z - 0.08) < 0.02) {"""

new_landing = """          } else if (isFinalLandingWp) {
            // Строгое вертикальное приземление точно в центр Home площадки
            const groundZ = (st.role === 'executor') ? 0.10 : 0.08;
            st.x += (wp.x - st.x) * 12.0 * dt;
            st.y += (wp.y - st.y) * 12.0 * dt;
            st.vx = 0;
            st.vy = 0;
            st.yaw += (0 - st.yaw) * 8.0 * dt;
            st.targetZ = groundZ;

            if (st.z <= groundZ + 0.035) {"""

if old_landing in content:
    content = content.replace(old_landing, new_landing)
    print("Replaced isFinalLandingWp")
else:
    print("old_landing not matched")

# 3. Update btnRunChain text
old_runchain = """      showPhaseBanner("ЭТАП 1: БПЛА-Разведчик сканирует полигон галсами (цели скрыты, сканирование в реальном времени...)");
      updatePipelineStep(1);
    };"""

new_runchain = """      const btnRun = document.getElementById('btnRunChain');
      if (btnRun) btnRun.textContent = '⏳ Выполняется...';
      showPhaseBanner("ЭТАП 1: БПЛА-Разведчик сканирует полигон галсами (цели скрыты, сканирование в реальном времени...)");
      updatePipelineStep(1);
    };"""

if old_runchain in content:
    content = content.replace(old_runchain, new_runchain)
    print("Replaced runchain button text")

# 4. Update finish text & button
old_finish = """                const txtEl = document.getElementById('payloadText');
                if (txtEl) txtEl.textContent = 'ГОТОВ (МИССИЯ ВЫПОЛНЕНА)';

                showPhaseBanner("✅ МИССИЯ ЗАВЕРШЕНА: Все 6 очагов A обработаны, точная посадка в центр Home-2, 0 нарушений NFZ!");"""

new_finish = """                const txtEl = document.getElementById('payloadText');
                if (txtEl) txtEl.textContent = 'ВЫКЛ (МИССИЯ ВЫПОЛНЕНА)';

                const btnRun = document.getElementById('btnRunChain');
                if (btnRun) btnRun.textContent = '✅ Миссия завершена';

                showPhaseBanner("✅ МИССИЯ ЗАВЕРШЕНА: Все 6 очагов A обработаны, точная посадка в центр Home-2, 0 нарушений NFZ!");"""

if old_finish in content:
    content = content.replace(old_finish, new_finish)
    print("Replaced finish button text")

# 5. Update reset
old_reset = """      updatePipelineStep(1);
      showPhaseBanner("Ожидание команды оператора · Нажмите «⚡ Запуск цепочки ТЗ»");"""

new_reset = """      updatePipelineStep(1);
      const btnRun = document.getElementById('btnRunChain');
      if (btnRun) btnRun.textContent = '⚡ Запуск цепочки ТЗ';
      const p4Span = document.querySelector('#pipe4 span');
      if (p4Span) p4Span.textContent = '🏁 4. Финиш';
      showPhaseBanner("Ожидание команды оператора · Нажмите «⚡ Запуск цепочки ТЗ»");"""

if old_reset in content:
    content = content.replace(old_reset, new_reset)
    print("Replaced reset button text")

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Saved simulation_3d/index.html")
