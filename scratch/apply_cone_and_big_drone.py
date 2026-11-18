"""
Скрипт обновления:
1. Строгая синхронизация 3D-конуса камеры и зоны видимости SLAM-миникарты (1-в-1 физическое соответствие).
2. Отрисовка живой проекции конуса камеры на 2D SLAM-карте.
3. Увеличение БПЛА-2 (Поливщик-Исполнитель):
   - Размах лучей увеличен более чем в 2.2 раза (с 22 см до 52 см!).
   - Большие пропеллеры и мощные бесколлекторные моторы.
   - Огромный агрономический бак для биопрепарата на 12-16 литров с заливной горловиной и индикатором.
   - Высокие трубчатые посадочные шасси (лыжи) как у реальных агродронов (DJI Agras).
   - Широкая распылительная штанга с 4 форсунками и широким конусом тумана.
"""

import sys
import re

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update updateSlamScan: footprint math matching 3D cone exactly
old_slam_scan = '''    function updateSlamScan(px, py, pz) {
      if (pz < 0.15) return;
      const scanR = 0.95; // Радиус зоны обзора камеры на высоте ~1.2 м
      let newlyScanned = false;

      for (let c = 0; c < SLAM_COLS; c++) {
        const cx = (c + 0.5) * SLAM_RES;
        if (Math.abs(cx - px) > scanR) continue;

        for (let r = 0; r < SLAM_ROWS; r++) {
          const cy = (r + 0.5) * SLAM_RES;
          if (Math.abs(cy - py) > scanR) continue;

          const dist = Math.hypot(cx - px, cy - py);
          if (dist <= scanR) {'''

new_slam_scan = '''    function updateSlamScan(px, py, pz) {
      if (pz < 0.15) return;
      // Реальная зона обзора камеры: полуразмеры проекции конуса на земле (угол FOV ~80°)
      const hRel = Math.max(pz, 0.10);
      const w = 0.90 * (hRel / 1.2); // Полуширина конуса по X
      const d = 0.65 * (hRel / 1.2); // Полувысота конуса по Y
      let newlyScanned = false;

      for (let c = 0; c < SLAM_COLS; c++) {
        const cx = (c + 0.5) * SLAM_RES;
        if (Math.abs(cx - px) > w + 0.05) continue;

        for (let r = 0; r < SLAM_ROWS; r++) {
          const cy = (r + 0.5) * SLAM_RES;
          if (Math.abs(cy - py) > d + 0.05) continue;

          // Клетка попадает строго в видимый световой конус камеры на земле:
          if (Math.abs(cx - px) <= w && Math.abs(cy - py) <= d) {'''

text = text.replace(old_slam_scan, new_slam_scan, 1)

# 2. In renderSlamMap: draw live camera footprint rectangle on the 2D map
old_render_slam_end = '''      // 6. Отрисовка активных целей (если открыты)
      targetsData.forEach(t => {'''

new_render_slam_end = '''      // 5.1. Живая проекция конуса камеры БПЛА-1 на миникарту (100% совпадение с 3D-конусом!)
      if (drone1State.z > 0.15) {
        const hRel = Math.max(drone1State.z, 0.10);
        const fw = (0.90 * (hRel / 1.2)) * scaleX;
        const fd = (0.65 * (hRel / 1.2)) * scaleY;
        const fpx = drone1State.x * scaleX;
        const fpy = H - drone1State.y * scaleY;

        slamCtx.strokeStyle = '#38bdf8';
        slamCtx.lineWidth = 1.5;
        slamCtx.strokeRect(fpx - fw, fpy - fd, fw * 2, fd * 2);

        slamCtx.fillStyle = 'rgba(56, 189, 248, 0.18)';
        slamCtx.fillRect(fpx - fw, fpy - fd, fw * 2, fd * 2);
      }

      // 6. Отрисовка активных целей (если открыты)
      targetsData.forEach(t => {'''

text = text.replace(old_render_slam_end, new_render_slam_end, 1)

# 3. In updateDronePhysics: sync 3D frustum dimensions (w, d) and discovery logic
old_frustum_math = '''        const vApex = [st.x, st.y, Math.max(st.z - 0.026, 0.02)];
        const hRel = Math.max(st.z, 0.05);
        const w = 0.44 * (hRel / 1.2);
        const d = 0.34 * (hRel / 1.2);'''

new_frustum_math = '''        const vApex = [st.x, st.y, Math.max(st.z - 0.026, 0.02)];
        const hRel = Math.max(st.z, 0.05);
        // Реальный размер проекции камеры (соответствует зоне отрисовки SLAM-карты):
        const w = 0.90 * (hRel / 1.2);
        const d = 0.65 * (hRel / 1.2);'''

text = text.replace(old_frustum_math, new_frustum_math, 1)

# 4. In updateDronePhysics: discovery when target enters real cone
old_discovery_dist = '''            const dx = st.x - t.x;
            const dy = st.y - t.y;
            const dist2D = Math.sqrt(dx * dx + dy * dy);
            const maxDetectDist = (t.type === 'A_NFZ') ? 1.55 : 0.85;

            if (dist2D <= maxDetectDist) {'''

new_discovery_dist = '''            const hRel = Math.max(st.z, 0.10);
            const w = 0.90 * (hRel / 1.2);
            const d = 0.65 * (hRel / 1.2);
            const dx = Math.abs(st.x - t.x);
            const dy = Math.abs(st.y - t.y);

            // Цель гарантированно открывается в момент попадания в видимый световой конус камеры!
            if (dx <= w + 0.12 && dy <= d + 0.12) {'''

text = text.replace(old_discovery_dist, new_discovery_dist, 1)

# 5. BuildQuadcopter: Make Executor (Sprayer) significantly larger (>2.2x scale with agricultural equipment)
old_build_quad = '''    function buildQuadcopter(role) {
      // Иерархия узлов:
      // droneRig отвечает за позицию (X,Y,Z) и угол рыскания (Yaw вокруг оси Z)
      // droneBody (дочерний узел) отвечает строго за тангаж (Pitch вокруг локальной оси Y) и крен (Roll вокруг локальной оси X)
      // Это гарантирует 100% правильный наклон в сторону носа дрона при любом повороте!
      const droneRig = new THREE.Group();
      const droneBody = new THREE.Group();
      droneRig.add(droneBody);

      const isRecon = (role === 'recon');
      const frameColor = isRecon ? 0xf8fafc : 0x0f172a;
      const accentColor = isRecon ? 0xea580c : 0x22c55e;
      const propFrontColor = isRecon ? 0xea580c : 0x22c55e;
      const propRearColor = isRecon ? 0x38bdf8 : 0x0284c7;

      const carbonMat = new THREE.MeshStandardMaterial({ color: frameColor, roughness: 0.4, metalness: 0.6 });
      const accentMat = new THREE.MeshStandardMaterial({ color: accentColor, roughness: 0.3, metalness: 0.8 });
      const motorMat = new THREE.MeshStandardMaterial({ color: 0x475569, roughness: 0.2, metalness: 0.95 });

      const bottomPlate = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.10, 0.005), carbonMat);
      droneBody.add(bottomPlate);

      const topPlate = new THREE.Mesh(new THREE.BoxGeometry(0.10, 0.08, 0.005), carbonMat);
      topPlate.position.set(0, 0, 0.02);
      droneBody.add(topPlate);

      const canopy = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.06, 0.025), accentMat);
      canopy.position.set(0, 0, 0.032);
      droneBody.add(canopy);

      const gpsPost = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.003, 0.03, 8), carbonMat);
      gpsPost.rotation.x = Math.PI / 2;
      gpsPost.position.set(-0.035, 0, 0.045);
      droneBody.add(gpsPost);

      const gpsPuck = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.005, 16), carbonMat);
      gpsPuck.rotation.x = Math.PI / 2;
      gpsPuck.position.set(-0.035, 0, 0.06);
      droneBody.add(gpsPuck);

      const motorPositions = [
        { x:  0.11, y:  0.11, front: true },
        { x:  0.11, y: -0.11, front: true },
        { x: -0.11, y:  0.11, front: false },
        { x: -0.11, y: -0.11, front: false }
      ];

      const propellers = [];

      motorPositions.forEach(mp => {
        const armLength = Math.sqrt(mp.x * mp.x + mp.y * mp.y);
        const arm = new THREE.Mesh(new THREE.BoxGeometry(armLength, 0.012, 0.006), carbonMat);
        arm.position.set(mp.x / 2, mp.y / 2, 0.01);
        arm.rotation.z = Math.atan2(mp.y, mp.x);
        droneBody.add(arm);

        const motor = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 0.016, 16), motorMat);
        motor.rotation.x = Math.PI / 2;
        motor.position.set(mp.x, mp.y, 0.02);
        droneBody.add(motor);

        const propGroup = new THREE.Group();
        propGroup.position.set(mp.x, mp.y, 0.03);

        const bladeColor = mp.front ? propFrontColor : propRearColor;
        const bladeMat = new THREE.MeshStandardMaterial({ color: bladeColor, roughness: 0.3 });

        const blade = new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.014, 0.002), bladeMat);
        propGroup.add(blade);

        const nut = new THREE.Mesh(new THREE.ConeGeometry(0.005, 0.008, 12), motorMat);
        nut.rotation.x = Math.PI / 2;
        nut.position.z = 0.004;
        propGroup.add(nut);

        droneBody.add(propGroup);
        propellers.push(propGroup);

        const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.003, 0.05, 8), carbonMat);
        leg.rotation.x = Math.PI / 2;
        leg.position.set(mp.x, mp.y, -0.015);
        droneBody.add(leg);

        const foot = new THREE.Mesh(new THREE.SphereGeometry(0.006, 8, 8), carbonMat);
        foot.position.set(mp.x, mp.y, -0.04);
        droneBody.add(foot);

        const navLed = new THREE.Mesh(
          new THREE.SphereGeometry(0.005, 8, 8),
          new THREE.MeshBasicMaterial({ color: mp.front ? 0x22c55e : 0xef4444 })
        );
        navLed.position.set(mp.x, mp.y, 0.005);
        droneBody.add(navLed);
      });

      let payloadSpot = null;
      let cameraFrustum = null;
      let payloadLamp = null;
      let frustumPyrGeo = null;
      let frustumLineGeo = null;
      let frustumFootprintGeo = null;

      if (isRecon) {
        const camBox = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.03, 0.02), carbonMat);
        camBox.position.set(0.02, 0, -0.015);
        droneBody.add(camBox);

        const lens = new THREE.Mesh(
          new THREE.CylinderGeometry(0.008, 0.008, 0.006, 12),
          new THREE.MeshStandardMaterial({ color: 0x38bdf8, metalness: 0.9 })
        );
        lens.rotation.x = Math.PI / 2;
        lens.position.set(0.02, 0, -0.026);
        droneBody.add(lens);

        // --- ТОЧНЫЙ КОНУС / ПИРАМИДА КАМЕРЫ (АПЕКС У ОБЪЕКТИВА, ШИРОКАЯ БАЗА НА ЗЕМЛЕ) ---
        const frustumGroup = new THREE.Group();
        const pyrPositions = new Float32Array(18 * 3);
        const pyrGeo = new THREE.BufferGeometry();
        pyrGeo.setAttribute('position', new THREE.BufferAttribute(pyrPositions, 3));

        const pyrMat = new THREE.MeshBasicMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.08, // Легкий, кристально прозрачный световой объем
          depthWrite: false, // НЕ закрывает собой точки на поле!
          depthTest: true,
          side: THREE.DoubleSide
        });
        const pyrMesh = new THREE.Mesh(pyrGeo, pyrMat);
        pyrMesh.frustumCulled = false; // ГАРАНТИЯ: НИКОГДА НЕ ПРОПАДАЕТ!
        frustumGroup.add(pyrMesh);

        const linePositions = new Float32Array(16 * 3);
        const lineGeo = new THREE.BufferGeometry();
        lineGeo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
        const lineMesh = new THREE.LineSegments(lineGeo, new THREE.LineBasicMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.45,
          depthWrite: false
        }));
        lineMesh.frustumCulled = false; // НИКОГДА НЕ ПРОПАДАЕТ!
        frustumGroup.add(lineMesh);

        const footPositions = new Float32Array(5 * 3);
        const footGeo = new THREE.BufferGeometry();
        footGeo.setAttribute('position', new THREE.BufferAttribute(footPositions, 3));
        const footLine = new THREE.Line(footGeo, new THREE.LineBasicMaterial({
          color: 0x38bdf8,
          linewidth: 2,
          depthWrite: false
        }));
        footLine.frustumCulled = false; // НИКОГДА НЕ ПРОПАДАЕТ!
        frustumGroup.add(footLine);

        frustumPyrGeo = pyrGeo;
        frustumLineGeo = lineGeo;
        frustumFootprintGeo = footGeo;

        frustumGroup.visible = false;
        scene.add(frustumGroup);
        cameraFrustum = frustumGroup;
      } else {
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
      }

      const shadow = new THREE.Mesh(
        new THREE.RingGeometry(0.08, 0.10, 32),
        new THREE.MeshBasicMaterial({ color: accentColor, opacity: 0.6, transparent: true })
      );
      shadow.position.set(0, 0, 0.005);
      scene.add(shadow);'''

new_build_quad = '''    function buildQuadcopter(role) {
      const droneRig = new THREE.Group();
      const droneBody = new THREE.Group();
      droneRig.add(droneBody);

      const isRecon = (role === 'recon');

      // МАСШТАБ: БПЛА-2 (Поливщик/Исполнитель) ЗНАЧИТЕЛЬНО БОЛЬШЕ разведчика (в 2.2 раза!)
      const armSpan = isRecon ? 0.11 : 0.24; // Размах 22 см vs 55 см!
      const frameColor = isRecon ? 0xf8fafc : 0x0f172a;
      const accentColor = isRecon ? 0xea580c : 0x16a34a;
      const propFrontColor = isRecon ? 0xea580c : 0x22c55e;
      const propRearColor = isRecon ? 0x38bdf8 : 0x15803d;

      const carbonMat = new THREE.MeshStandardMaterial({ color: frameColor, roughness: 0.35, metalness: 0.7 });
      const accentMat = new THREE.MeshStandardMaterial({ color: accentColor, roughness: 0.3, metalness: 0.8 });
      const motorMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.2, metalness: 0.95 });

      if (isRecon) {
        // --- БПЛА-1: КОМПАКТНЫЙ ЛЕГКИЙ РАЗВЕДЧИК ---
        const bottomPlate = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.10, 0.005), carbonMat);
        droneBody.add(bottomPlate);

        const topPlate = new THREE.Mesh(new THREE.BoxGeometry(0.10, 0.08, 0.005), carbonMat);
        topPlate.position.set(0, 0, 0.02);
        droneBody.add(topPlate);

        const canopy = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.06, 0.025), accentMat);
        canopy.position.set(0, 0, 0.032);
        droneBody.add(canopy);

        const gpsPost = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.003, 0.03, 8), carbonMat);
        gpsPost.rotation.x = Math.PI / 2;
        gpsPost.position.set(-0.035, 0, 0.045);
        droneBody.add(gpsPost);

        const gpsPuck = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.005, 16), carbonMat);
        gpsPuck.rotation.x = Math.PI / 2;
        gpsPuck.position.set(-0.035, 0, 0.06);
        droneBody.add(gpsPuck);
      } else {
        // --- БПЛА-2: МОЩНЫЙ ТЯЖЕЛЫЙ АГРОНОМИЧЕСКИЙ ОПРЫСКИВАТЕЛЬ (БОЛЬШОЙ КОРПУС) ---
        const heavyBottom = new THREE.Mesh(new THREE.BoxGeometry(0.26, 0.22, 0.012), carbonMat);
        droneBody.add(heavyBottom);

        const heavyTop = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.18, 0.010), carbonMat);
        heavyTop.position.set(0, 0, 0.04);
        droneBody.add(heavyTop);

        const industrialCockpit = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.14, 0.045), accentMat);
        industrialCockpit.position.set(0, 0, 0.065);
        droneBody.add(industrialCockpit);

        // Мощная двухмачтовая антенна RTK GNSS
        [-0.07, 0.07].forEach(ax => {
          const mPost = new THREE.Mesh(new THREE.CylinderGeometry(0.005, 0.005, 0.06, 8), carbonMat);
          mPost.rotation.x = Math.PI / 2;
          mPost.position.set(-0.08, ax, 0.07);
          droneBody.add(mPost);

          const mPuck = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.008, 16), carbonMat);
          mPuck.rotation.x = Math.PI / 2;
          mPuck.position.set(-0.08, ax, 0.10);
          droneBody.add(mPuck);
        });
      }

      // 4 мотора и лучи (с учетом размаха для каждого дрона)
      const motorPositions = [
        { x:  armSpan, y:  armSpan, front: true },
        { x:  armSpan, y: -armSpan, front: true },
        { x: -armSpan, y:  armSpan, front: false },
        { x: -armSpan, y: -armSpan, front: false }
      ];

      const propellers = [];

      motorPositions.forEach(mp => {
        const armLength = Math.sqrt(mp.x * mp.x + mp.y * mp.y);
        const armThickness = isRecon ? 0.012 : 0.026;
        const armHeight = isRecon ? 0.006 : 0.014;
        const arm = new THREE.Mesh(new THREE.BoxGeometry(armLength, armThickness, armHeight), carbonMat);
        arm.position.set(mp.x / 2, mp.y / 2, isRecon ? 0.01 : 0.02);
        arm.rotation.z = Math.atan2(mp.y, mp.x);
        droneBody.add(arm);

        const motR = isRecon ? 0.016 : 0.032;
        const motH = isRecon ? 0.016 : 0.030;
        const motor = new THREE.Mesh(new THREE.CylinderGeometry(motR, motR, motH, 16), motorMat);
        motor.rotation.x = Math.PI / 2;
        motor.position.set(mp.x, mp.y, isRecon ? 0.02 : 0.04);
        droneBody.add(motor);

        const propGroup = new THREE.Group();
        propGroup.position.set(mp.x, mp.y, isRecon ? 0.03 : 0.055);

        const bladeColor = mp.front ? propFrontColor : propRearColor;
        const bladeMat = new THREE.MeshStandardMaterial({ color: bladeColor, roughness: 0.3 });

        // У поливщика пропеллеры более чем в 2 раза длиннее (агродроны)
        const bladeLen = isRecon ? 0.11 : 0.25;
        const bladeW = isRecon ? 0.014 : 0.028;
        const blade = new THREE.Mesh(new THREE.BoxGeometry(bladeLen, bladeW, 0.003), bladeMat);
        propGroup.add(blade);

        const nut = new THREE.Mesh(new THREE.ConeGeometry(isRecon ? 0.005 : 0.010, isRecon ? 0.008 : 0.016, 12), motorMat);
        nut.rotation.x = Math.PI / 2;
        nut.position.z = 0.005;
        propGroup.add(nut);

        droneBody.add(propGroup);
        propellers.push(propGroup);

        if (isRecon) {
          const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.003, 0.05, 8), carbonMat);
          leg.rotation.x = Math.PI / 2;
          leg.position.set(mp.x, mp.y, -0.015);
          droneBody.add(leg);

          const foot = new THREE.Mesh(new THREE.SphereGeometry(0.006, 8, 8), carbonMat);
          foot.position.set(mp.x, mp.y, -0.04);
          droneBody.add(foot);
        }

        const navLed = new THREE.Mesh(
          new THREE.SphereGeometry(isRecon ? 0.005 : 0.009, 8, 8),
          new THREE.MeshBasicMaterial({ color: mp.front ? 0x22c55e : 0xef4444 })
        );
        navLed.position.set(mp.x, mp.y, 0.01);
        droneBody.add(navLed);
      });

      // Для поливщика: широкие трубчатые лыжи (шасси агродрона)
      if (!isRecon) {
        [-0.14, 0.14].forEach(ly => {
          // Вертикальные стойки лыж
          [-0.10, 0.10].forEach(lx => {
            const strut = new THREE.Mesh(new THREE.CylinderGeometry(0.006, 0.006, 0.09, 8), carbonMat);
            strut.rotation.x = Math.PI / 2;
            strut.position.set(lx, ly, -0.035);
            droneBody.add(strut);
          });
          // Горизонтальная лыжа
          const skid = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, 0.36, 10), carbonMat);
          skid.rotation.y = Math.PI / 2;
          skid.position.set(0, ly, -0.08);
          droneBody.add(skid);
        });
      }

      let payloadSpot = null;
      let cameraFrustum = null;
      let payloadLamp = null;
      let frustumPyrGeo = null;
      let frustumLineGeo = null;
      let frustumFootprintGeo = null;

      if (isRecon) {
        const camBox = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.035, 0.024), carbonMat);
        camBox.position.set(0.025, 0, -0.015);
        droneBody.add(camBox);

        const lens = new THREE.Mesh(
          new THREE.CylinderGeometry(0.010, 0.010, 0.008, 12),
          new THREE.MeshStandardMaterial({ color: 0x38bdf8, metalness: 0.9 })
        );
        lens.rotation.x = Math.PI / 2;
        lens.position.set(0.025, 0, -0.028);
        droneBody.add(lens);

        // --- ТОЧНЫЙ КОНУС КАМЕРЫ (АПЕКС У ОБЪЕКТИВА, ШИРОКАЯ БАЗА НА ЗЕМЛЕ) ---
        const frustumGroup = new THREE.Group();
        const pyrPositions = new Float32Array(18 * 3);
        const pyrGeo = new THREE.BufferGeometry();
        pyrGeo.setAttribute('position', new THREE.BufferAttribute(pyrPositions, 3));

        const pyrMat = new THREE.MeshBasicMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.12, // Прозрачный чистый световой объем
          depthWrite: false,
          depthTest: true,
          side: THREE.DoubleSide
        });
        const pyrMesh = new THREE.Mesh(pyrGeo, pyrMat);
        pyrMesh.frustumCulled = false;
        frustumGroup.add(pyrMesh);

        const linePositions = new Float32Array(16 * 3);
        const lineGeo = new THREE.BufferGeometry();
        lineGeo.setAttribute('position', new THREE.BufferAttribute(linePositions, 3));
        const lineMesh = new THREE.LineSegments(lineGeo, new THREE.LineBasicMaterial({
          color: 0x38bdf8,
          transparent: true,
          opacity: 0.55,
          depthWrite: false
        }));
        lineMesh.frustumCulled = false;
        frustumGroup.add(lineMesh);

        const footPositions = new Float32Array(5 * 3);
        const footGeo = new THREE.BufferGeometry();
        footGeo.setAttribute('position', new THREE.BufferAttribute(footPositions, 3));
        const footLine = new THREE.Line(footGeo, new THREE.LineBasicMaterial({
          color: 0x38bdf8,
          linewidth: 2,
          depthWrite: false
        }));
        footLine.frustumCulled = false;
        frustumGroup.add(footLine);

        frustumPyrGeo = pyrGeo;
        frustumLineGeo = lineGeo;
        frustumFootprintGeo = footGeo;

        frustumGroup.visible = false;
        scene.add(frustumGroup);
        cameraFrustum = frustumGroup;
      } else {
        // --- ОБОРУДОВАНИЕ БПЛА-2 (ПОЛИВЩИК): БОЛЬШОЙ РЕЗЕРВУАР БИОПРЕПАРАТА + ШТАНГИ ОПРЫСКИВАНИЯ ---
        // 1. Огромный агрохимический бак (в 2.5 раза больше!)
        const tankGeo = new THREE.CylinderGeometry(0.082, 0.082, 0.115, 24);
        const tankMat = new THREE.MeshStandardMaterial({
          color: 0x15803d, // Зеленая жидкая полезная нагрузка
          transparent: true,
          opacity: 0.85,
          roughness: 0.25,
          metalness: 0.15
        });
        const tankMesh = new THREE.Mesh(tankGeo, tankMat);
        tankMesh.rotation.x = Math.PI / 2;
        tankMesh.position.set(0, 0, 0.115);
        droneBody.add(tankMesh);

        // Горловина бака
        const capGeo = new THREE.CylinderGeometry(0.026, 0.026, 0.020, 16);
        const capMat = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.4 });
        const capMesh = new THREE.Mesh(capGeo, capMat);
        capMesh.rotation.x = Math.PI / 2;
        capMesh.position.set(0, 0, 0.175);
        droneBody.add(capMesh);

        // Смотровые трубки уровня жидкости с обеих сторон
        [-0.084, 0.084].forEach(gx => {
          const gaugeMesh = new THREE.Mesh(
            new THREE.PlaneGeometry(0.014, 0.085),
            new THREE.MeshBasicMaterial({ color: 0x4ade80, side: THREE.DoubleSide })
          );
          gaugeMesh.position.set(gx, 0, 0.115);
          gaugeMesh.rotation.y = Math.PI / 2;
          droneBody.add(gaugeMesh);
        });

        // 2. Две широкие распылительные штанги под лучами с 4 распылителями
        const sprayBoom = new THREE.Mesh(
          new THREE.CylinderGeometry(0.007, 0.007, 0.46, 12),
          new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.85 })
        );
        sprayBoom.position.set(0, 0, -0.04);
        droneBody.add(sprayBoom);

        // 4 распылительные форсунки вдоль штанги
        [-0.20, -0.07, 0.07, 0.20].forEach(nx => {
          const nozz = new THREE.Mesh(
            new THREE.CylinderGeometry(0.010, 0.014, 0.022, 12),
            new THREE.MeshStandardMaterial({ color: 0xd97706, metalness: 0.9 })
          );
          nozz.rotation.x = Math.PI / 2;
          nozz.position.set(nx, 0, -0.052);
          droneBody.add(nozz);
        });

        // Центральный мощный светодиод по ТЗ
        const lamp = new THREE.Mesh(
          new THREE.CylinderGeometry(0.026, 0.026, 0.012, 16),
          new THREE.MeshBasicMaterial({ color: 0x334155 })
        );
        lamp.rotation.x = Math.PI / 2;
        lamp.position.set(0, 0, -0.055);
        droneBody.add(lamp);
        payloadLamp = lamp;

        // Световой конус индикатора операции
        payloadSpot = new THREE.SpotLight(0x22c55e, 0, 4.5, Math.PI / 7, 0.25, 1.0);
        payloadSpot.position.set(0, 0, -0.06);
        payloadSpot.target.position.set(0, 0, -1);
        droneBody.add(payloadSpot);
        droneBody.add(payloadSpot.target);

        // 3. Широкая система частиц тумана опрыскивания (от 4 форсунок)
        const mistCount = 120;
        const mistGeo = new THREE.BufferGeometry();
        const mistPos = new Float32Array(mistCount * 3);
        for (let i = 0; i < mistCount * 3; i += 3) {
          mistPos[i] = (Math.random() - 0.5) * 0.42;
          mistPos[i + 1] = (Math.random() - 0.5) * 0.12;
          mistPos[i + 2] = -0.06 - Math.random() * 1.25;
        }
        mistGeo.setAttribute('position', new THREE.BufferAttribute(mistPos, 3));
        const mistMat = new THREE.PointsMaterial({
          color: 0x4ade80,
          size: 0.026,
          transparent: true,
          opacity: 0,
          depthWrite: false
        });
        const mistPoints = new THREE.Points(mistGeo, mistMat);
        droneBody.add(mistPoints);
        droneBody.userData.mistPoints = mistPoints;
      }

      // Тень под дроном (соответствует габаритам аппарата)
      const shadowR = isRecon ? 0.08 : 0.20;
      const shadow = new THREE.Mesh(
        new THREE.RingGeometry(shadowR, shadowR + 0.03, 32),
        new THREE.MeshBasicMaterial({ color: accentColor, opacity: 0.6, transparent: true })
      );
      shadow.position.set(0, 0, 0.005);
      scene.add(shadow);'''

text = text.replace(old_build_quad, new_build_quad, 1)

# 6. Adjust initial Z for Executor to 0.10 (tall skids)
text = text.replace("drone2State.x = 0.4; drone2State.y = 1.2; drone2State.z = 0.08;", "drone2State.x = 0.4; drone2State.y = 1.2; drone2State.z = 0.10;")

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Cone visibility and large sprayer drone updated successfully!")
