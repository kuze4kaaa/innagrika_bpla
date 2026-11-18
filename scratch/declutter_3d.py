"""
Скрипт очистки 3D-пространства от нагромождения:
1. Удаление originSprite, cageSign, padSprite, nfzSprite, droneTagSprite.
2. Замена текстовых простыней над целями на миниатюрные элегантные пины (микро-бейдж A1, A2, B, U, NFZ) с depthTest: true.
3. Интеграция pipelineSubtext и привязка кнопок вызова модальных окон (Справка ТЗ, SLAM).
"""

import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update createBillboardSprite to createMicroPin (sleek tiny round pill)
old_sprite_func = '''    function createBillboardSprite(title, subtitle, badgeColor, icon, width = 340, height = 96) {
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');

      function draw(t, sub, col, ico) {
        ctx.clearRect(0, 0, width, height);

        // Полупрозрачная темная подложка
        ctx.fillStyle = 'rgba(15, 23, 42, 0.90)';
        ctx.strokeStyle = col;
        ctx.lineWidth = 3.5;
        const r = 12;
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(4, 4, width - 8, height - 8, r);
        } else {
          ctx.rect(4, 4, width - 8, height - 8);
        }
        ctx.fill();
        ctx.stroke();

        // Верхняя акцентная полоска
        ctx.fillStyle = col;
        ctx.fillRect(16, 6, width - 32, 3);

        // Иконка и заголовок
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 20px "Segoe UI", Roboto, sans-serif';
        ctx.fillText(`${ico} ${t}`, 16, 40);

        // Описание / подпись
        ctx.fillStyle = '#94a3b8';
        ctx.font = '14px "Segoe UI", Roboto, sans-serif';
        ctx.fillText(sub, 16, 72);
      }

      draw(title, subtitle, badgeColor, icon);

      const texture = new THREE.CanvasTexture(canvas);
      texture.minFilter = THREE.LinearFilter;
      const mat = new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        depthTest: false,
        depthWrite: false
      });
      const sprite = new THREE.Sprite(mat);
      sprite.scale.set(width / 340 * 0.90, height / 340 * 0.90, 1);

      sprite.update = (newTitle, newSub, newCol, newIco) => {
        draw(newTitle, newSub, newCol, newIco);
        texture.needsUpdate = true;
      };

      allSceneLabels.push(sprite);
      sprite.visible = labelsVisible;
      return sprite;
    }'''

new_sprite_func = '''    // Аккуратный микро-пин над целевыми участками (компактный и не заслоняющий сцену)
    function createMicroPin(label, colorHex, icon = '🎯') {
      const canvas = document.createElement('canvas');
      canvas.width = 160;
      canvas.height = 54;
      const ctx = canvas.getContext('2d');

      function drawPin(lbl, col, ico) {
        ctx.clearRect(0, 0, 160, 54);

        // Капсульная подложка
        ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
        ctx.strokeStyle = col;
        ctx.lineWidth = 3;
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(4, 4, 152, 46, 23);
        } else {
          ctx.rect(4, 4, 152, 46);
        }
        ctx.fill();
        ctx.stroke();

        // Текст микро-пина
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 20px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${ico} ${lbl}`, 80, 27);
      }

      drawPin(label, colorHex, icon);

      const tex = new THREE.CanvasTexture(canvas);
      tex.minFilter = THREE.LinearFilter;
      const mat = new THREE.SpriteMaterial({
        map: tex,
        transparent: true,
        depthTest: true, // ВАЖНО: не перекрывает объекты на переднем плане!
        depthWrite: false
      });
      const sprite = new THREE.Sprite(mat);
      sprite.scale.set(0.24, 0.08, 1.0); // Маленький масштаб в мировых координатах

      sprite.update = (newLabel, newCol, newIco) => {
        drawPin(newLabel, newCol, newIco);
        tex.needsUpdate = true;
      };

      allSceneLabels.push(sprite);
      sprite.visible = labelsVisible;
      return sprite;
    }'''

text = text.replace(old_sprite_func, new_sprite_func, 1)

# 2. Remove originSprite, cageSign
text = re.sub(r'const originSprite = createBillboardSprite\(.*?\);\s*originSprite\.position\.set\(.*?\);\s*scene\.add\(originSprite\);', '', text, flags=re.DOTALL)
text = re.sub(r'const cageSign = createBillboardSprite\(.*?\);\s*cageSign\.position\.set\(.*?\);\s*scene\.add\(cageSign\);', '', text, flags=re.DOTALL)

# 3. Remove padSprite inside createHelipad
text = re.sub(r'const padSprite = createBillboardSprite\(.*?\);\s*padSprite\.position\.set\(.*?\);\s*scene\.add\(padSprite\);', '', text, flags=re.DOTALL)

# 4. Remove nfzSprite inside nfzZones.forEach
text = re.sub(r'const nfzLabelText = .*?;\s*const nfzSubText = .*?;\s*const nfzSprite = createBillboardSprite\(.*?\);\s*nfzSprite\.position\.set\(.*?\);\s*scene\.add\(nfzSprite\);', '', text, flags=re.DOTALL)

# 5. Remove droneTagSprite inside buildQuadcopter
text = re.sub(r'// 3D-плавающая бирка над дроном.*?droneRig\.add\(droneTagSprite\);', '', text, flags=re.DOTALL)
text = text.replace('tagSprite: droneTagSprite,', '')
text = text.replace('tagSprite: droneTagSprite', '')

# 6. Update target sprites in generateRandomTargets to use createMicroPin
old_target_sprite_block = '''        // 4. Плавающая 3D-вывеска (Billboard Sprite) над растением:
        let initialTitle = `ОЧАГ A-${t.id} (СОРНЯК)`;
        let initialSub = '⚠️ Требуется опрыскивание 2.0с (R=0.25м)';
        let initialColor = '#f97316';
        let initialIcon = '🎯';

        if (t.type === 'A_NFZ') {
          initialTitle = `ОЧАГ A-${t.id} (В ЗОНЕ NFZ)`;
          initialSub = '⛔ Влёт и обработка ЗАПРЕЩЕНЫ ТЗ!';
          initialColor = '#ef4444';
          initialIcon = '🚫';
        } else if (t.type === 'B') {
          initialTitle = 'УЧАСТОК B (КУЛЬТУРА)';
          initialSub = '🌿 Здоровые томаты · Без химии';
          initialColor = '#3b82f6';
          initialIcon = '🌿';
        } else if (t.type === 'U') {
          initialTitle = 'УЧАСТОК U (ДЕФЕКТ/СУХОСТОЙ)';
          initialSub = '❓ Сомнительный спектр · Пропуск по ТЗ';
          initialColor = '#a855f7';
          initialIcon = '❓';
        }

        const sprite = createBillboardSprite(initialTitle, initialSub, initialColor, initialIcon, 340, 88);
        sprite.position.set(t.x, t.y, 0.32);
        // До разведки делаем метку приглушенной
        sprite.material.opacity = 0.45;
        scene.add(sprite);'''

new_target_sprite_block = '''        // 4. Компактный микро-пин над растением (высота всего 0.16м, не загораживает обзор):
        let pinText = `A-${t.id}`;
        let pinColor = '#f97316';
        let pinIcon = '🎯';

        if (t.type === 'A_NFZ') {
          pinText = `NFZ-${t.id}`;
          pinColor = '#ef4444';
          pinIcon = '🚫';
        } else if (t.type === 'B') {
          pinText = 'Культура B';
          pinColor = '#3b82f6';
          pinIcon = '🌿';
        } else if (t.type === 'U') {
          pinText = 'Объект U';
          pinColor = '#a855f7';
          pinIcon = '❓';
        }

        const sprite = createMicroPin(pinText, pinColor, pinIcon);
        sprite.position.set(t.x, t.y, 0.16);
        sprite.material.opacity = 0.35; // До разведки приглушен
        scene.add(sprite);'''

text = text.replace(old_target_sprite_block, new_target_sprite_block, 1)

# 7. Update discovery sprite update
old_disc_sprite = '''              if (tm.sprite) {
                tm.sprite.material.opacity = 1.0;
                tm.sprite.update(title, sub, colStr, ico);
              }'''

new_disc_sprite = '''              if (tm.sprite) {
                tm.sprite.material.opacity = 1.0;
                let shortLbl = `A-${t.id}`;
                if (t.type === 'B') shortLbl = 'Культура B';
                if (t.type === 'U') shortLbl = 'Объект U';
                if (t.type === 'A_NFZ') shortLbl = `NFZ-${t.id}`;
                tm.sprite.update(shortLbl, colStr, ico);
              }'''

text = text.replace(old_disc_sprite, new_disc_sprite, 1)

# 8. Update treatment sprite update
old_treat_sprite = '''              if (tm.sprite) {
                tm.sprite.update(`ОЧАГ A-${currWp.targetId} ОБРАБОТАН!`, '✅ Биопрепарат внесен (2.0 с)', '#22c55e', '✅');
              }'''

new_treat_sprite = '''              if (tm.sprite) {
                tm.sprite.update(`A-${currWp.targetId} ГОТОВО`, '#22c55e', '✅');
              }'''

text = text.replace(old_treat_sprite, new_treat_sprite, 1)

# 9. Remove drone tag update references if any
text = text.replace("if (obj.tagSprite) {", "if (false) {")

# 10. Update showPhaseBanner to update pipelineSubtext cleanly
old_banner_func = '''    function showPhaseBanner(text) {
      const b = document.getElementById('phaseBanner');
      document.getElementById('phaseText').textContent = text;
      b.style.display = 'block';
    }'''

new_banner_func = '''    function showPhaseBanner(text) {
      const sub = document.getElementById('pipelineSubtext');
      if (sub) sub.textContent = text;
    }'''

text = text.replace(old_banner_func, new_banner_func, 1)

# 11. Wire up buttons: toggleLegend, closeLegend, toggleSlam, toggleLabels
button_wiring = '''
    // Переключение окна справки ТЗ
    const legendCard = document.getElementById('sceneLegend');
    const btnToggleLegend = document.getElementById('btnToggleLegend');
    const legendCloseBtn = document.getElementById('legendCloseBtn');
    if (btnToggleLegend && legendCard) {
      btnToggleLegend.onclick = () => {
        const isShown = (legendCard.style.display === 'block');
        legendCard.style.display = isShown ? 'none' : 'block';
        btnToggleLegend.classList.toggle('btn-active-toggle', !isShown);
      };
    }
    if (legendCloseBtn && legendCard) {
      legendCloseBtn.onclick = () => {
        legendCard.style.display = 'none';
        if (btnToggleLegend) btnToggleLegend.classList.remove('btn-active-toggle');
      };
    }

    // Переключение 2D карты SLAM
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
    }
'''

# Insert button wiring before animate()
text = text.replace('function animate() {', button_wiring + '\n    function animate() {', 1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Pass 2 of declutter applied successfully!")
