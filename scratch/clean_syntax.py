import sys

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update line 2933 btnToggleSlam
old_slam_toggle = '''    // --- Переключение 2D SLAM-карты ---
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
    }'''

new_slam_toggle = '''    // --- Переключение 2D SLAM-карты ---
    const btnToggleSlam = document.getElementById('btnToggleSlam');
    const slamMapCard = document.getElementById('slamMapCard');
    if (btnToggleSlam && slamMapCard) {
      btnToggleSlam.onclick = () => {
        const isClosed = (slamMapCard.style.display === 'none' || slamMapCard.style.display === '');
        slamMapCard.style.display = isClosed ? 'block' : 'none';
        btnToggleSlam.classList.toggle('btn-active-toggle', isClosed);
      };
    }'''

text = text.replace(old_slam_toggle, new_slam_toggle, 1)

# 2. Clean up lines 3655 to 3735
old_block_end = '''    // Переключение 2D карты SLAM
    const slamCard = document.getElementById('slamMapCard');
    const btnToggleSlam = document.getElementById('btnToggleSlam');
    if (btnToggleSlam && slamCard) {
      btnToggleSlam.onclick = () => {
        const isShown = (slamCard.style.display === 'block');
        slamCard.style.display = isShown ? 'none' : 'block';
        btnToggleSlam.classList.toggle('btn-active-toggle', !isShown);
      };
    }

    // Переключение 3D микро-меток
    const btnLabelsToggle = document.getElementById('btnToggleLabels');
    if (btnLabelsToggle) {
      btnLabelsToggle.onclick = () => {
        labelsVisible = !labelsVisible;
        allSceneLabels.forEach(s => s.visible = labelsVisible);
        btnLabelsToggle.classList.toggle('btn-active-toggle', labelsVisible);
      };
    }'''

text = text.replace(old_block_end, '', 1)

# 3. Clean up duplicate btnLabelsToggle after animate
old_labels_dup = '''    // Переключение видимости 3D-меток
    const btnLabelsToggle = document.getElementById('btnToggleLabels');
    if (btnLabelsToggle) {
      btnLabelsToggle.onclick = () => {
        labelsVisible = !labelsVisible;
        allSceneLabels.forEach(s => s.visible = labelsVisible);
        btnLabelsToggle.textContent = labelsVisible ? '🏷️ 3D-Метки: ВКЛ' : '🏷️ 3D-Метки: ВЫКЛ';
        btnLabelsToggle.classList.toggle('active', labelsVisible);
      };
    }'''

text = text.replace(old_labels_dup, '', 1)

# Ensure btnToggleLabels is wired cleanly before animate
clean_wiring = '''    // Переключение видимости 3D микро-меток
    const btnLabelsToggle = document.getElementById('btnToggleLabels');
    if (btnLabelsToggle) {
      btnLabelsToggle.onclick = () => {
        labelsVisible = !labelsVisible;
        allSceneLabels.forEach(s => s.visible = labelsVisible);
        btnLabelsToggle.classList.toggle('btn-active-toggle', labelsVisible);
      };
    }'''

# Insert clean_wiring right after legendCloseBtn
old_legend_close = '''    if (legendCloseBtn && legendCard) {
      legendCloseBtn.onclick = () => {
        legendCard.style.display = 'none';
        if (btnToggleLegend) btnToggleLegend.classList.remove('btn-active-toggle');
      };
    }'''

text = text.replace(old_legend_close, old_legend_close + '\n\n' + clean_wiring, 1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Syntax and duplicate cleanup finished!")
