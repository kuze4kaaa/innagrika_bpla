"""
Скрипт обновления:
1. generateRandomTargets(): создание 3D-растений, кругов допуска R=0.25м, пятна r=0.04м и плавающих 3D-спрайтов.
2. buildQuadcopter('executor'): бак биопрепарата, форсунка и система частиц распыления тумана.
3. Логика обнаружения (Recon) и обработки (Executor) с обновлением 3D-спрайтов.
4. Пресеты камер (3D Поле, Сетка F, Очаг A крупно).
5. Кнопка скрытия/показа 3D-подписей и синхронизация пошагового бара миссии.
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update generateRandomTargets
new_generate_targets = '''    function generateRandomTargets() {
      // Удаляем старые меши и спрайты целей со сцены
      targetMeshes.forEach(tm => {
        scene.remove(tm.group);
        if (tm.sprite) {
          scene.remove(tm.sprite);
          const sIdx = allSceneLabels.indexOf(tm.sprite);
          if (sIdx !== -1) allSceneLabels.splice(sIdx, 1);
        }
      });
      targetMeshes = [];
      targetsData = [];

      // Сброс SLAM-сетки и покрытия при генерации новой карты
      if (typeof slamGrid !== 'undefined') {
        slamGrid.fill(0);
        slamCoverage = 0.0;
        slamWallsCount = 0;
        const covBadge = document.getElementById('slamCoverageBadge');
        if (covBadge) covBadge.textContent = 'ПОКРЫТИЕ: 0.0%';
      }

      // 2 очага намеренно внутри запретных зон NFZ (по ТЗ: проверка валидатора GCS):
      targetsData.push({
        id: 7,
        type: 'A_NFZ',
        name: 'Очаг A-7 (Внутри зоны NFZ-1)',
        x: 2.60 + (Math.random() - 0.5) * 0.35,
        y: 2.10 + (Math.random() - 0.5) * 0.28,
        discovered: false,
        treated: false
      });
      targetsData.push({
        id: 8,
        type: 'A_NFZ',
        name: 'Очаг A-8 (Внутри зоны NFZ-2)',
        x: 4.40 + (Math.random() - 0.5) * 0.25,
        y: 1.40 + (Math.random() - 0.5) * 0.25,
        discovered: false,
        treated: false
      });

      // 6 очагов класса A в разрешенных агрономических зонах:
      const zonesA = [
        { xMin: 0.90, xMax: 1.30, yMin: 0.55, yMax: 0.90, name: 'Очаг A-1 (Юго-Запад)' },
        { xMin: 2.10, xMax: 3.10, yMin: 0.36, yMax: 0.50, name: 'Очаг A-2 (Юг)' },
        { xMin: 0.90, xMax: 1.30, yMin: 3.25, yMax: 3.55, name: 'Очаг A-3 (Северо-Запад)' },
        { xMin: 2.10, xMax: 3.10, yMin: 3.25, yMax: 3.55, name: 'Очаг A-4 (Север)' },
        { xMin: 4.10, xMax: 5.20, yMin: 3.25, yMax: 3.55, name: 'Очаг A-5 (Северо-Восток)' },
        { xMin: 5.35, xMax: 5.55, yMin: 2.10, yMax: 2.70, name: 'Очаг A-6 (Восток)' }
      ];

      zonesA.forEach((z, idx) => {
        targetsData.push({
          id: idx + 1,
          type: 'A',
          name: z.name,
          x: z.xMin + Math.random() * (z.xMax - z.xMin),
          y: z.yMin + Math.random() * (z.yMax - z.yMin),
          discovered: false,
          treated: false
        });
      });

      // 1 здоровый участок B (томаты/культура):
      targetsData.push({
        id: 9,
        type: 'B',
        name: 'Участок B-9 (Здоровая культура)',
        x: 0.70 + Math.random() * 0.30,
        y: 1.90 + Math.random() * 0.50,
        discovered: false,
        treated: false
      });

      // 1 сомнительный участок U (неопределенная текстура/дефект):
      targetsData.push({
        id: 10,
        type: 'U',
        name: 'Участок U-10 (Неопределенный спектр)',
        x: 5.30 + Math.random() * 0.25,
        y: 0.70 + Math.random() * 0.40,
        discovered: false,
        treated: false
      });

      // Создание 3D-объектов на полигоне:
      targetsData.forEach(t => {
        const tGroup = new THREE.Group();
        tGroup.position.set(t.x, t.y, 0.012);

        // Земляной кругляш под растением
        const soilBed = new THREE.Mesh(
          new THREE.CircleGeometry(0.28, 24),
          new THREE.MeshStandardMaterial({ color: 0x1e150f, roughness: 0.95 })
        );
        tGroup.add(soilBed);

        // 1. Рабочая область цели по ТЗ: R = 0.25 м
        const ringMat = new THREE.MeshBasicMaterial({
          color: 0x64748b,
          transparent: true,
          opacity: 0.25,
          side: THREE.DoubleSide
        });
        const ring = new THREE.Mesh(new THREE.RingGeometry(0.23, 0.25, 32), ringMat);
        ring.position.z = 0.002;
        tGroup.add(ring);

        // 2. Условный радиус воздействия / пятно форсунки по ТЗ: r = 0.04 м
        const dotMat = new THREE.MeshBasicMaterial({ color: 0x64748b, transparent: true, opacity: 0.45 });
        const dot = new THREE.Mesh(new THREE.CircleGeometry(0.04, 16), dotMat);
        dot.position.z = 0.003;
        tGroup.add(dot);

        // 3. Реалистичная 3D-модель растения по классу (сорняк A, культура B, сухой стебель U)
        const plant = buildPlantModel(t.type);
        tGroup.add(plant);

        scene.add(tGroup);

        // 4. Плавающая 3D-вывеска (Billboard Sprite) над растением:
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
        scene.add(sprite);

        targetMeshes.push({
          data: t,
          group: tGroup,
          ringMesh: ring,
          dotMesh: dot,
          plantMesh: plant,
          sprite: sprite
        });
      });

      if (typeof drone1State !== 'undefined') drone1State.memory = [];
      updateHUDDiscoveredCount(0);
    }
'''

# Find generateRandomTargets and replace through nfzMeshes
idx_gen_start = text.find('function generateRandomTargets()')
idx_gen_end = text.find('// --- МОДЕЛИРОВАНИЕ ДВУХ БПЛА ---')

if idx_gen_start != -1 and idx_gen_end != -1:
    text = text[:idx_gen_start] + new_generate_targets.strip() + '\n\n    ' + text[idx_gen_end:]
    print("generateRandomTargets updated successfully!")
else:
    print("ERROR finding generateRandomTargets block!", idx_gen_start, idx_gen_end)
    sys.exit(1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Pass 2 finished!")
