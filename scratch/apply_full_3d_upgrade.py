"""
Полное обновление 3D-сцены:
- Почва, грядки и всходы культурных растений
- Огражденный каркас полигона с защитной сеткой и линейкой разметки координат поля F
- 3D-модели растений (сорняки A, культура B, сухой образец U)
- 3D-спрайты подписей над всеми объектами
- Оборудование в запретных зонах (шкаф автоматики NFZ-1 с маячком, метеомачта и насос NFZ-2)
- Стартовые площадки H-1 и H-2
- Бак биопрепарата на БПЛА-2, распылительная форсунка и система частиц тумана/спрея при обработке!
- Синхронизация верхнего пошагового пайплайна миссии
"""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    code = f.read()

# Let's prepare the code block that defines helpers, floor, cage, bases, equipment
scene_setup_replacement = '''
    // =========================================================================
    // 1. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ: ТЕКСТУРЫ И 3D-ПОДПИСИ (THREE.Sprite)
    // =========================================================================
    let labelsVisible = true;
    const allSceneLabels = [];

    function createBillboardSprite(title, subtitle, badgeColor, icon, width = 340, height = 96) {
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
    }

    // Процедурная текстура почвы (чернозем с органической зернистостью и бороздками)
    function createSoilTexture() {
      const canvas = document.createElement('canvas');
      canvas.width = 512;
      canvas.height = 512;
      const ctx = canvas.getContext('2d');

      ctx.fillStyle = '#261b12'; // Темный органический грунт
      ctx.fillRect(0, 0, 512, 512);

      // Зернистость почвы и комья земли
      for (let i = 0; i < 3500; i++) {
        const x = Math.random() * 512;
        const y = Math.random() * 512;
        const r = Math.random() * 2.2 + 0.4;
        const b = Math.floor(Math.random() * 30);
        ctx.fillStyle = `rgb(${34 + b}, ${24 + b * 0.8}, ${16 + b * 0.5})`;
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
      }

      // Агрономические продольные борозды
      ctx.strokeStyle = 'rgba(15, 9, 5, 0.45)';
      ctx.lineWidth = 3.5;
      for (let y = 16; y < 512; y += 32) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(512, y);
        ctx.stroke();
      }

      const tex = new THREE.CanvasTexture(canvas);
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.RepeatWrapping;
      tex.repeat.set(6, 4);
      return tex;
    }

    // Текстура желто-черной сигнальной ленты / зебры безопасности
    function createHazardTexture() {
      const canvas = document.createElement('canvas');
      canvas.width = 256;
      canvas.height = 64;
      const ctx = canvas.getContext('2d');

      ctx.fillStyle = '#eab308';
      ctx.fillRect(0, 0, 256, 64);

      ctx.fillStyle = '#0f172a';
      const stripeW = 24;
      for (let x = -64; x < 320; x += stripeW * 2) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x + stripeW, 0);
        ctx.lineTo(x + stripeW - 32, 64);
        ctx.lineTo(x - 32, 64);
        ctx.closePath();
        ctx.fill();
      }

      const tex = new THREE.CanvasTexture(canvas);
      tex.wrapS = THREE.RepeatWrapping;
      tex.wrapT = THREE.RepeatWrapping;
      tex.repeat.set(4, 1);
      return tex;
    }

    // =========================================================================
    // 2. АГРОНОМИЧЕСКОЕ ПОЛЕ, ГРЯДКИ И ПОСЕВЫ КУЛЬТУР
    // =========================================================================
    const floorGeo = new THREE.PlaneGeometry(FIELD_WIDTH, FIELD_HEIGHT);
    const floorMat = new THREE.MeshStandardMaterial({
      map: createSoilTexture(),
      roughness: 0.92,
      metalness: 0.08
    });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.position.set(FIELD_WIDTH / 2, FIELD_HEIGHT / 2, 0);
    floor.receiveShadow = true;
    scene.add(floor);

    // Грядки посевов (приподнятые земляные гряды вдоль полигона)
    const bedMat = new THREE.MeshStandardMaterial({
      color: 0x332216,
      roughness: 0.95
    });
    for (let y = 0.35; y < FIELD_HEIGHT; y += 0.42) {
      const bed = new THREE.Mesh(new THREE.BoxGeometry(FIELD_WIDTH - 0.2, 0.26, 0.015), bedMat);
      bed.position.set(FIELD_WIDTH / 2, y, 0.008);
      bed.receiveShadow = true;
      scene.add(bed);

      // Ровные ряды всходов рассады культурных растений
      for (let x = 0.35; x < FIELD_WIDTH - 0.25; x += 0.34) {
        // Пропускаем места стартовых площадок и шкафов NFZ
        if ((x < 0.9 && y < 1.6) || (x > 2.0 && x < 3.2 && y > 1.6 && y < 2.6) || (x > 3.9 && x < 4.9 && y > 0.9 && y < 1.9)) continue;
        const sprout = new THREE.Mesh(
          new THREE.ConeGeometry(0.024, 0.045, 5),
          new THREE.MeshStandardMaterial({ color: 0x22c55e, roughness: 0.7 })
        );
        sprout.rotation.x = Math.PI / 2;
        sprout.position.set(x + (Math.random() - 0.5) * 0.03, y + (Math.random() - 0.5) * 0.02, 0.025);
        scene.add(sprout);
      }
    }

    // =========================================================================
    // 3. КООРДИНАТНАЯ РАЗМЕТКА ПОЛЯ F (6 × 4 м) И НАЧАЛО КООРДИНАТ (0,0)
    // =========================================================================
    // Бело-желтый бордюр полигона
    const borderPoints = [
      new THREE.Vector3(0, 0, 0.015),
      new THREE.Vector3(FIELD_WIDTH, 0, 0.015),
      new THREE.Vector3(FIELD_WIDTH, FIELD_HEIGHT, 0.015),
      new THREE.Vector3(0, FIELD_HEIGHT, 0.015),
      new THREE.Vector3(0, 0, 0.015)
    ];
    const borderGeo = new THREE.BufferGeometry().setFromPoints(borderPoints);
    const borderLine = new THREE.Line(borderGeo, new THREE.LineBasicMaterial({ color: 0xfacc15, linewidth: 3 }));
    scene.add(borderLine);

    // Метрические деления и метки по осям X (0..6м) и Y (0..4м)
    for (let x = 1.0; x <= FIELD_WIDTH; x += 1.0) {
      const tick = new THREE.Mesh(
        new THREE.PlaneGeometry(0.02, 0.12),
        new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide })
      );
      tick.position.set(x, 0.06, 0.016);
      scene.add(tick);
    }
    for (let y = 1.0; y <= FIELD_HEIGHT; y += 1.0) {
      const tick = new THREE.Mesh(
        new THREE.PlaneGeometry(0.12, 0.02),
        new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide })
      );
      tick.position.set(0.06, y, 0.016);
      scene.add(tick);
    }

    // Начало координат поля F в углу (0,0,0)
    const axesHelper = new THREE.AxesHelper(1.2);
    axesHelper.position.set(0, 0, 0.02);
    scene.add(axesHelper);

    const originSprite = createBillboardSprite('НАЧАЛО КООРДИНАТ (0,0)', 'Система поля F: X=6м, Y=4м', '#38bdf8', '📐', 280, 80);
    originSprite.position.set(0.4, 0.1, 0.28);
    scene.add(originSprite);

    // =========================================================================
    // 4. ОГРАЖДЕННАЯ ЗОНА ДЛЯ ПОЛЕТОВ (ЛЕТНЫЙ КУПОЛ 6 × 4 × 2.5 м)
    // =========================================================================
    // 4 угловые алюминиевые ферменные стойки ограждения
    const trussMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.85, roughness: 0.25 });
    const cornerPosts = [
      { x: 0, y: 0 },
      { x: FIELD_WIDTH, y: 0 },
      { x: FIELD_WIDTH, y: FIELD_HEIGHT },
      { x: 0, y: FIELD_HEIGHT }
    ];
    cornerPosts.forEach(cp => {
      const post = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 2.5, 12), trussMat);
      post.rotation.x = Math.PI / 2;
      post.position.set(cp.x, cp.y, 1.25);
      scene.add(post);

      const foot = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.16, 0.04), trussMat);
      foot.position.set(cp.x, cp.y, 0.02);
      scene.add(foot);
    });

    // Верхний пояс ферм по периметру на высоте 2.5 м
    const topPerimeterPoints = [
      new THREE.Vector3(0, 0, 2.5),
      new THREE.Vector3(FIELD_WIDTH, 0, 2.5),
      new THREE.Vector3(FIELD_WIDTH, FIELD_HEIGHT, 2.5),
      new THREE.Vector3(0, FIELD_HEIGHT, 2.5),
      new THREE.Vector3(0, 0, 2.5)
    ];
    const topPerimeterGeo = new THREE.BufferGeometry().setFromPoints(topPerimeterPoints);
    const topPerimeterLine = new THREE.Line(topPerimeterGeo, new THREE.LineBasicMaterial({ color: 0x38bdf8, linewidth: 2 }));
    scene.add(topPerimeterLine);

    // Защитная сетка ограждения (Safety Netting wireframe, прозрачность 0.14)
    const cageGeo = new THREE.BoxGeometry(FIELD_WIDTH, FIELD_HEIGHT, 2.5);
    const cageEdges = new THREE.EdgesGeometry(cageGeo);
    const cageLine = new THREE.LineSegments(cageEdges, new THREE.LineBasicMaterial({
      color: 0x38bdf8,
      opacity: 0.28,
      transparent: true
    }));
    cageLine.position.set(FIELD_WIDTH / 2, FIELD_HEIGHT / 2, 1.25);
    scene.add(cageLine);

    // Табличка зоны соревнований на ограждении
    const cageSign = createBillboardSprite('ПОЛИГОН «ТОЧНОЕ ПОЛЕ»', 'Огражденная зона полетов 6 × 4 м · ТЗ АТ11-2', '#0284c7', '🛡️', 340, 80);
    cageSign.position.set(3.0, 4.02, 2.4);
    scene.add(cageSign);

    // =========================================================================
    // 5. СТАРТОВЫЕ ПЛОЩАДКИ (HOME-1 И HOME-2)
    // =========================================================================
    function createHelipad(x, y, label, sub, colorHex, icon, isExec = false) {
      const padGroup = new THREE.Group();
      padGroup.position.set(x, y, 0.015);

      // Приподнятая база площадки
      const baseMesh = new THREE.Mesh(
        new THREE.CylinderGeometry(0.38, 0.40, 0.02, 32),
        new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.6 })
      );
      baseMesh.rotation.x = Math.PI / 2;
      padGroup.add(baseMesh);

      // Внутренний круг с маркировкой
      const circleMesh = new THREE.Mesh(
        new THREE.CircleGeometry(0.32, 32),
        new THREE.MeshStandardMaterial({ color: colorHex, roughness: 0.4 })
      );
      circleMesh.position.z = 0.012;
      padGroup.add(circleMesh);

      // Белое кольцо разметки
      const ringMesh = new THREE.Mesh(
        new THREE.RingGeometry(0.24, 0.26, 32),
        new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide })
      );
      ringMesh.position.z = 0.014;
      padGroup.add(ringMesh);

      // Буква "H" в центре площадки
      const hStemL = new THREE.Mesh(new THREE.PlaneGeometry(0.03, 0.18), new THREE.MeshBasicMaterial({ color: 0xffffff }));
      hStemL.position.set(-0.06, 0, 0.015);
      padGroup.add(hStemL);
      const hStemR = new THREE.Mesh(new THREE.PlaneGeometry(0.03, 0.18), new THREE.MeshBasicMaterial({ color: 0xffffff }));
      hStemR.position.set(0.06, 0, 0.015);
      padGroup.add(hStemR);
      const hCross = new THREE.Mesh(new THREE.PlaneGeometry(0.12, 0.03), new THREE.MeshBasicMaterial({ color: 0xffffff }));
      hCross.position.set(0, 0, 0.015);
      padGroup.add(hCross);

      // 4 угловых посадочных огня (Runway LEDs)
      const ledMat = new THREE.MeshBasicMaterial({ color: colorHex });
      [
        { lx:  0.30, ly:  0.30 },
        { lx: -0.30, ly:  0.30 },
        { lx:  0.30, ly: -0.30 },
        { lx: -0.30, ly: -0.30 }
      ].forEach(lp => {
        const led = new THREE.Mesh(new THREE.SphereGeometry(0.014, 8, 8), ledMat);
        led.position.set(lp.lx, lp.ly, 0.02);
        padGroup.add(led);
      });

      // Рядом с H-1: вышка наземной базовой станции RTK
      if (!isExec) {
        const rtkPole = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.35, 8), trussMat);
        rtkPole.rotation.x = Math.PI / 2;
        rtkPole.position.set(-0.35, 0, 0.17);
        padGroup.add(rtkPole);

        const rtkPuck = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.02, 16), new THREE.MeshStandardMaterial({ color: 0xf8fafc }));
        rtkPuck.rotation.x = Math.PI / 2;
        rtkPuck.position.set(-0.35, 0, 0.35);
        padGroup.add(rtkPuck);
      } else {
        // Рядом с H-2: заправочная емкость биопрепарата (IBC-контейнер)
        const tankBox = new THREE.Mesh(
          new THREE.BoxGeometry(0.14, 0.14, 0.18),
          new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 0.3, transparent: true, opacity: 0.85 })
        );
        tankBox.position.set(-0.38, 0, 0.09);
        padGroup.add(tankBox);

        const tankCap = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.02, 12), new THREE.MeshBasicMaterial({ color: 0x15803d }));
        tankCap.rotation.x = Math.PI / 2;
        tankCap.position.set(-0.38, 0, 0.19);
        padGroup.add(tankCap);
      }

      scene.add(padGroup);

      // 3D-плавающая вывеска над площадкой
      const padSprite = createBillboardSprite(label, sub, colorHex, icon, 320, 84);
      padSprite.position.set(x, y + 0.35, 0.32);
      scene.add(padSprite);
    }

    createHelipad(0.40, 0.40, 'БАЗА 1: РАЗВЕДЧИК', 'Старт/посадка БПЛА-1 (Фотосъемка)', '#ea580c', '🚁', false);
    createHelipad(0.40, 1.20, 'БАЗА 2: ИСПОЛНИТЕЛЬ', 'Старт/посадка БПЛА-2 (Внесение препарата)', '#15803d', '🛸', true);

    // =========================================================================
    // 6. ТЕХНИЧЕСКОЕ ОБОРУДОВАНИЕ В ЗАПРЕТНЫХ ЗОНАХ (NFZ)
    // =========================================================================
    const nfzMeshes = [];
    const hazardTex = createHazardTexture();

    // NFZ-1: Шкаф автоматики климат-контроля и полива (в центре cx=2.6, cy=2.1)
    const z1 = nfzZones[0];
    const cabGroup = new THREE.Group();
    cabGroup.position.set(z1.cx, z1.cy, 0);

    // Металлический промышленный шкаф автоматики
    const cabMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.7, roughness: 0.35 });
    const cabMesh = new THREE.Mesh(new THREE.BoxGeometry(0.70, 0.55, 1.10), cabMat);
    cabMesh.position.set(0, 0, 0.55);
    cabMesh.castShadow = true;
    cabGroup.add(cabMesh);

    // Сенсорный экран статуса
    const screenMesh = new THREE.Mesh(
      new THREE.PlaneGeometry(0.25, 0.16),
      new THREE.MeshBasicMaterial({ color: 0x0284c7 })
    );
    screenMesh.position.set(0, -0.28, 0.75);
    cabGroup.add(screenMesh);

    // Желто-черная полоса предупреждения на шкафу
    const hazBand = new THREE.Mesh(
      new THREE.PlaneGeometry(0.68, 0.12),
      new THREE.MeshStandardMaterial({ map: hazardTex })
    );
    hazBand.position.set(0, -0.28, 0.20);
    cabGroup.add(hazBand);

    // Желтый проблесковый маячок на шкафу (мигает в animate)
    const beaconLight = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.04, 0.08, 16),
      new THREE.MeshBasicMaterial({ color: 0xfacc15 })
    );
    beaconLight.rotation.x = Math.PI / 2;
    beaconLight.position.set(0, 0, 1.15);
    cabGroup.add(beaconLight);

    // 4 защитных полосатых столбика по углам зоны
    const bollardMat = new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.5 });
    [
      { bx:  z1.w / 2 - 0.05, by:  z1.h / 2 - 0.05 },
      { bx: -z1.w / 2 + 0.05, by:  z1.h / 2 - 0.05 },
      { bx:  z1.w / 2 - 0.05, by: -z1.h / 2 + 0.05 },
      { bx: -z1.w / 2 + 0.05, by: -z1.h / 2 + 0.05 }
    ].forEach(bp => {
      const bCol = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 0.8, 10), bollardMat);
      bCol.rotation.x = Math.PI / 2;
      bCol.position.set(bp.bx, bp.by, 0.40);
      cabGroup.add(bCol);
    });

    scene.add(cabGroup);

    // NFZ-2: Метеорологическая мачта и гидронасос (cx=4.4, cy=1.4)
    const z2 = nfzZones[1];
    const mastGroup = new THREE.Group();
    mastGroup.position.set(z2.cx, z2.cy, 0);

    // Насосная гидростанция (синий бак давления)
    const pumpTank = new THREE.Mesh(
      new THREE.CylinderGeometry(0.18, 0.18, 0.45, 16),
      new THREE.MeshStandardMaterial({ color: 0x0284c7, metalness: 0.6, roughness: 0.3 })
    );
    pumpTank.rotation.x = Math.PI / 2;
    pumpTank.position.set(-0.12, 0, 0.25);
    mastGroup.add(pumpTank);

    // Вертикальная метеомачта
    const mastPole = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 1.8, 8), trussMat);
    mastPole.rotation.x = Math.PI / 2;
    mastPole.position.set(0.15, 0, 0.90);
    mastGroup.add(mastPole);

    // Анемометр на вершине мачты
    const anemometerHead = new THREE.Mesh(new THREE.SphereGeometry(0.03, 8, 8), trussMat);
    anemometerHead.position.set(0.15, 0, 1.82);
    mastGroup.add(anemometerHead);

    scene.add(mastGroup);

    // Красные световые защитные призмы NFZ и желтые буферы безопасности (+0.23м)
    nfzZones.forEach((z, idx) => {
      const geo = new THREE.BoxGeometry(z.w, z.h, NFZ_MAX_Z);
      const mat = new THREE.MeshStandardMaterial({
        color: 0xef4444,
        transparent: true,
        opacity: 0.26,
        roughness: 0.2
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(z.cx, z.cy, NFZ_MAX_Z / 2);
      scene.add(mesh);
      nfzMeshes.push({ data: z, mesh: mesh });

      // Буфер безопасности (+0.23 м: БПЛА 0.10 + запас 0.05 + погрешность 0.08)
      const bGeo = new THREE.BoxGeometry(z.w + 2 * BUFFER_INFLATION, z.h + 2 * BUFFER_INFLATION, NFZ_MAX_Z);
      const bEdges = new THREE.EdgesGeometry(bGeo);
      const bLine = new THREE.LineSegments(bEdges, new THREE.LineDashedMaterial({
        color: 0xfacc15,
        dashSize: 0.08,
        gapSize: 0.04,
        linewidth: 2
      }));
      bLine.computeLineDistances();
      bLine.position.set(z.cx, z.cy, NFZ_MAX_Z / 2);
      scene.add(bLine);

      // 3D-вывеска запретной зоны
      const nfzLabelText = (idx === 0) ? 'ЗАПРЕТНАЯ ЗОНА NFZ-1' : 'ЗАПРЕТНАЯ ЗОНА NFZ-2';
      const nfzSubText = (idx === 0) ? 'Шкаф автоматики · Влёт запрещен ТЗ' : 'Метеомачта и насос · Влёт запрещен ТЗ';
      const nfzSprite = createBillboardSprite(nfzLabelText, nfzSubText, '#ef4444', '⛔', 340, 84);
      nfzSprite.position.set(z.cx, z.cy, 1.55);
      scene.add(nfzSprite);
    });

    // =========================================================================
    // 7. ГЕНЕРАТОР 3D-МОДЕЛЕЙ РАСТЕНИЙ ПО КЛАССАМ ТЗ (A, B, U)
    // =========================================================================
    function buildPlantModel(type) {
      const pGroup = new THREE.Group();

      if (type === 'A' || type === 'A_NFZ') {
        // СОРНЯК / ОЧАГ БОЛЕЗНИ (раскидистый сорняк с пятнистыми буро-желтыми больными листьями)
        const stemMat = new THREE.MeshStandardMaterial({ color: 0x4d5320, roughness: 0.85 });
        const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.012, 0.12, 8), stemMat);
        stem.rotation.x = Math.PI / 2;
        stem.position.z = 0.06;
        pGroup.add(stem);

        const leafGeo = new THREE.PlaneGeometry(0.07, 0.026);
        const leafMatBlight = new THREE.MeshStandardMaterial({
          color: 0xca8a04, // желто-бурый пораженный цвет
          side: THREE.DoubleSide,
          roughness: 0.8
        });
        const leafMatWeed = new THREE.MeshStandardMaterial({
          color: 0x65a30d,
          side: THREE.DoubleSide,
          roughness: 0.8
        });

        for (let i = 0; i < 8; i++) {
          const ang = (i / 8) * Math.PI * 2;
          const leaf = new THREE.Mesh(leafGeo, (i % 2 === 0) ? leafMatBlight : leafMatWeed);
          leaf.rotation.z = ang;
          leaf.rotation.x = 0.35 * Math.sin(ang);
          leaf.rotation.y = 0.35 * Math.cos(ang);
          leaf.position.set(Math.cos(ang) * 0.035, Math.sin(ang) * 0.035, 0.045 + (i % 3) * 0.015);
          pGroup.add(leaf);
        }

        // Соцветие / семенная головка сорняка
        const weedHead = new THREE.Mesh(
          new THREE.DodecahedronGeometry(0.018),
          new THREE.MeshStandardMaterial({ color: 0xf59e0b, roughness: 0.6 })
        );
        weedHead.position.z = 0.12;
        pGroup.add(weedHead);

      } else if (type === 'B') {
        // ЗДОРОВАЯ КУЛЬТУРА (пышный здоровый куст томатов со спелыми плодами)
        const stemMat = new THREE.MeshStandardMaterial({ color: 0x15803d, roughness: 0.7 });
        const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.010, 0.014, 0.14, 8), stemMat);
        stem.rotation.x = Math.PI / 2;
        stem.position.z = 0.07;
        pGroup.add(stem);

        const leafGeo = new THREE.PlaneGeometry(0.08, 0.034);
        const leafMatFresh = new THREE.MeshStandardMaterial({
          color: 0x22c55e, // яркая здоровая сочная зелень
          side: THREE.DoubleSide,
          roughness: 0.6
        });

        for (let i = 0; i < 10; i++) {
          const ang = (i / 10) * Math.PI * 2;
          const leaf = new THREE.Mesh(leafGeo, leafMatFresh);
          leaf.rotation.z = ang;
          leaf.rotation.x = 0.4 * Math.sin(ang);
          leaf.rotation.y = 0.4 * Math.cos(ang);
          leaf.position.set(Math.cos(ang) * 0.04, Math.sin(ang) * 0.04, 0.05 + (i % 3) * 0.02);
          pGroup.add(leaf);
        }

        // 3 спелых плода томата
        const fruitGeo = new THREE.SphereGeometry(0.015, 10, 10);
        const fruitMat = new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.25 });
        [
          { x: 0.025, y: 0.015, z: 0.07 },
          { x: -0.020, y: 0.025, z: 0.08 },
          { x: 0.010, y: -0.025, z: 0.06 }
        ].forEach(fp => {
          const fr = new THREE.Mesh(fruitGeo, fruitMat);
          fr.position.set(fp.x, fp.y, fp.z);
          pGroup.add(fr);
        });

      } else {
        // УЧАСТОК U: СОМНИТЕЛЬНЫЙ ДЕФЕКТНЫЙ СПЕКТР / СУХОЙ СТЕБЕЛЬ
        const dryMat = new THREE.MeshStandardMaterial({ color: 0x78716c, roughness: 0.95 });
        const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.008, 0.09, 6), dryMat);
        stem.rotation.z = 0.35;
        stem.rotation.x = Math.PI / 2 + 0.2;
        stem.position.set(0.01, 0, 0.04);
        pGroup.add(stem);

        const twig = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.008, 0.006), dryMat);
        twig.position.set(-0.01, 0.01, 0.05);
        twig.rotation.z = -0.6;
        pGroup.add(twig);
      }

      return pGroup;
    }
'''

# Find the start of floorGeo and end of pad creation
start_pos = code.find('const floorGeo = new THREE.PlaneGeometry(FIELD_WIDTH, FIELD_HEIGHT);')
end_pos = code.find('// --- ДИНАМИЧЕСКИЕ РАНДОМИЗИРОВАННЫЕ ЦЕЛИ')
if start_pos != -1 and end_pos != -1:
    code = code[:start_pos] + scene_setup_replacement.strip() + '\n\n    ' + code[end_pos:]
    print("Replaced floor, cage, bases, equipment successfully!")
else:
    print("ERROR: Could not find floorGeo block!", start_pos, end_pos)
    sys.exit(1)

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(code)

print("Pass 1 finished successfully!")
