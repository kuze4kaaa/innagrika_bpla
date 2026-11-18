const FIELD_WIDTH = 6.0;
const FIELD_HEIGHT = 4.0;
const NOMINAL_ALT = 1.2;
const MAX_SPEED = 0.4;
const BUFFER_INFLATION = 0.23;
const DRONE_RADIUS = 0.10;
const NFZ_MAX_Z = 2.5;

const nfzZones = [
  { id: 1, cx: 2.6, cy: 2.1, w: 1.2, h: 1.0 },
  { id: 2, cx: 4.4, cy: 1.40, w: 0.8, h: 0.8 }
];

nfzZones.forEach(z => {
  z.barrierMinX = z.cx - (z.w / 2 + BUFFER_INFLATION) - DRONE_RADIUS;
  z.barrierMaxX = z.cx + (z.w / 2 + BUFFER_INFLATION) + DRONE_RADIUS;
  z.barrierMinY = z.cy - (z.h / 2 + BUFFER_INFLATION) - DRONE_RADIUS;
  z.barrierMaxY = z.cy + (z.h / 2 + BUFFER_INFLATION) + DRONE_RADIUS;
});

// Create targets exactly as generateRandomTargets()
let targetsData = [];
targetsData.push({ id: 7, type: 'A_NFZ', name: 'Очаг A-7', x: 2.60, y: 2.10, discovered: false, treated: false });
targetsData.push({ id: 8, type: 'A_NFZ', name: 'Очаг A-8', x: 4.40, y: 1.40, discovered: false, treated: false });

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
    x: (z.xMin + z.xMax) / 2,
    y: (z.yMin + z.yMax) / 2,
    discovered: false,
    treated: false
  });
});
targetsData.push({ id: 9, type: 'B', name: 'Участок B-9', x: 0.85, y: 2.15, discovered: false, treated: false });
targetsData.push({ id: 10, type: 'U', name: 'Участок U-10', x: 5.42, y: 0.90, discovered: false, treated: false });

const plannedReconWaypoints = [
  { x: 0.40, y: 0.40, z: 1.2 },
  { x: 1.10, y: 0.45, z: 1.2 },
  { x: 2.10, y: 0.95, z: 1.2 },
  { x: 3.20, y: 0.45, z: 1.2 },
  { x: 4.40, y: 0.38, z: 1.2 },
  { x: 5.48, y: 0.38, z: 1.2 },
  { x: 5.48, y: 1.35, z: 1.2 },
  { x: 5.48, y: 2.40, z: 1.2 },
  { x: 5.48, y: 3.48, z: 1.2 },
  { x: 4.30, y: 3.48, z: 1.2 },
  { x: 3.80, y: 2.35, z: 1.2 },
  { x: 3.55, y: 3.48, z: 1.2 },
  { x: 2.60, y: 3.48, z: 1.2 },
  { x: 1.10, y: 3.48, z: 1.2 },
  { x: 0.40, y: 3.48, z: 1.2 },
  { x: 0.70, y: 2.80, z: 1.2 },
  { x: 0.70, y: 1.60, z: 1.2 },
  { x: 1.20, y: 1.60, z: 1.2 },
  { x: 1.20, y: 2.20, z: 1.2 },
  { x: 0.70, y: 1.00, z: 1.2 },
  { x: 0.40, y: 0.40, z: 1.2 },
  { x: 0.40, y: 0.40, z: 0.08 }
];

let drone1State = {
  role: 'recon',
  x: 0.4, y: 0.4, z: 0.08,
  vx: 0, vy: 0, vz: 0,
  yaw: 0, pitch: 0, roll: 0,
  targetZ: 1.2,
  autoPilot: true,
  waypoints: plannedReconWaypoints,
  autoIdx: 0,
  waypointStuckTimer: 0,
  memory: []
};

let drone2State = {
  role: 'executor',
  x: 0.4, y: 1.2, z: 0.08,
  vx: 0, vy: 0, vz: 0,
  yaw: 0, pitch: 0, roll: 0,
  targetZ: 0.08,
  autoPilot: false,
  payloadActive: false,
  payloadTimeLeft: 0,
  actionDone: false,
  stabilizeTimer: 0,
  waypoints: [],
  autoIdx: 0,
  waypointStuckTimer: 0
};

function planExecutorMissionFromMemory() {
  const memory = (drone1State.memory && drone1State.memory.length > 0) ? drone1State.memory : [];
  const acceptedTargets = [];

  memory.forEach(t => {
    let insideNFZ = false;
    nfzZones.forEach(z => {
      if (t.x >= z.barrierMinX && t.x <= z.barrierMaxX &&
          t.y >= z.barrierMinY && t.y <= z.barrierMaxY) {
        insideNFZ = true;
      }
    });

    if (t.type === 'A' && !insideNFZ && !t.nfz) {
      acceptedTargets.push(t);
    }
  });

  if (acceptedTargets.length === 0) {
    drone2State.waypoints = [{ x: 0.40, y: 1.20, z: 1.2 }];
    return 0;
  }

  const tSW = acceptedTargets.find(t => t.x < 1.8 && t.y < 1.5);
  const tS  = acceptedTargets.find(t => t.x >= 1.8 && t.x < 3.8 && t.y < 1.0);
  const tE  = acceptedTargets.find(t => t.x > 5.0 && t.y >= 1.5 && t.y <= 3.0);
  const tNE = acceptedTargets.find(t => t.x >= 3.8 && t.y > 3.0);
  const tN  = acceptedTargets.find(t => t.x >= 1.8 && t.x < 3.8 && t.y > 3.0);
  const tNW = acceptedTargets.find(t => t.x < 1.8 && t.y > 3.0);

  const waypoints = [
    { x: 0.40, y: 1.20, z: 1.2 }
  ];

  if (tSW) waypoints.push({ x: tSW.x, y: tSW.y, z: 1.2, action: true, targetId: tSW.id });
  if (tS)  waypoints.push({ x: tS.x,  y: tS.y,  z: 1.2, action: true, targetId: tS.id });

  if (tE || tNE || tN) {
    waypoints.push({ x: 4.40, y: 0.38, z: 1.2 });
    waypoints.push({ x: 5.48, y: 0.38, z: 1.2 });
  }

  if (tE)  waypoints.push({ x: tE.x,  y: tE.y,  z: 1.2, action: true, targetId: tE.id });

  if (tNE || tN || tNW) {
    waypoints.push({ x: 5.48, y: 3.48, z: 1.2 });
  }

  if (tNE) waypoints.push({ x: tNE.x, y: tNE.y, z: 1.2, action: true, targetId: tNE.id });
  if (tN)  waypoints.push({ x: tN.x,  y: tN.y,  z: 1.2, action: true, targetId: tN.id });
  if (tNW) waypoints.push({ x: tNW.x, y: tNW.y, z: 1.2, action: true, targetId: tNW.id });

  waypoints.push({ x: 0.70, y: 2.50, z: 1.2 });
  waypoints.push({ x: 0.70, y: 1.40, z: 1.2 });
  waypoints.push({ x: 0.40, y: 1.20, z: 1.2 });
  waypoints.push({ x: 0.40, y: 1.20, z: 0.08 });

  drone2State.waypoints = waypoints;
  return acceptedTargets.length;
}

function updatePhysics(st, dt) {
  let localAx = 0, localAy = 0;

  if (st.role === 'recon' && (st.autoPilot || st.z > 0.15)) {
    targetsData.forEach(t => {
      if (!t.discovered) {
        const dx = st.x - t.x;
        const dy = st.y - t.y;
        const dist2D = Math.sqrt(dx * dx + dy * dy);
        const maxDetectDist = (t.type === 'A_NFZ') ? 1.55 : 0.85;
        if (dist2D <= maxDetectDist) {
          t.discovered = true;
          st.memory.push(t);
        }
      }
    });
  }

  if (st.autoPilot && st.waypoints.length > 0 && st.autoIdx < st.waypoints.length) {
    const wp = st.waypoints[st.autoIdx];
    const isFinalLandingWp = (st.autoIdx === st.waypoints.length - 1);
    const dx = wp.x - st.x;
    const dy = wp.y - st.y;
    const dist = Math.sqrt(dx * dx + dy * dy);

    let acceptDist = 0.16;
    if (wp.action) acceptDist = 0.06;
    if (isFinalLandingWp) acceptDist = 0.03;

    if (dist > acceptDist) {
      st.waypointStuckTimer += dt;
      const targetYaw = Math.atan2(dy, dx);
      let diffYaw = targetYaw - st.yaw;
      while (diffYaw > Math.PI) diffYaw -= 2 * Math.PI;
      while (diffYaw < -Math.PI) diffYaw += 2 * Math.PI;
      st.yaw += diffYaw * 4.0 * dt;

      const cosH = Math.cos(st.yaw);
      const sinH = Math.sin(st.yaw);
      const speedFactor = (wp.action || isFinalLandingWp) ? 0.70 : 0.95;
      localAx = (dx * cosH + dy * sinH) / dist * speedFactor;
      localAy = (-dx * sinH + dy * cosH) / dist * speedFactor;
      st.targetZ = wp.z;

      if (st.waypointStuckTimer > 15.0) {
        console.log(`[STUCK TIMEOUT] ${st.role} wpIdx=${st.autoIdx} wp=(${wp.x}, ${wp.y}) dist=${dist.toFixed(3)} acceptDist=${acceptDist}`);
        st.autoIdx++;
        st.waypointStuckTimer = 0;
      }
    } else {
      st.waypointStuckTimer = 0;
      if (wp.action && st.role === 'executor') {
        st.vx = 0; st.vy = 0;
        if (st.stabilizeTimer < 1.0) {
          st.stabilizeTimer += dt;
        } else if (st.payloadTimeLeft <= 0 && !st.actionDone) {
          st.payloadActive = true;
          st.payloadTimeLeft = 2.0;
          st.actionDone = true;
          console.log(`[PAYLOAD TRIGGERED] Target ID: ${wp.targetId} at (${wp.x.toFixed(2)}, ${wp.y.toFixed(2)})`);
        } else if (st.payloadTimeLeft > 0) {
          // payload active
        } else {
          st.actionDone = false;
          st.stabilizeTimer = 0;
          st.autoIdx++;
        }
      } else if (isFinalLandingWp) {
        st.x += (wp.x - st.x) * 12.0 * dt;
        st.y += (wp.y - st.y) * 12.0 * dt;
        st.vx = 0; st.vy = 0;
        st.targetZ = 0.08;
        if (Math.abs(st.z - 0.08) < 0.02) {
          st.x = wp.x; st.y = wp.y; st.z = 0.08;
          st.autoPilot = false;
        }
      } else {
        st.autoIdx++;
      }
    }
  }

  const errZ = st.targetZ - st.z;
  st.vz += errZ * 3.5 * dt;
  st.vz *= Math.pow(0.85, dt * 60);
  st.z += st.vz * dt;
  if (st.z < 0.08) { st.z = 0.08; st.vz = 0; }

  const cosY = Math.cos(st.yaw);
  const sinY = Math.sin(st.yaw);
  const worldAx = localAx * cosY - localAy * sinY;
  const worldAy = localAx * sinY + localAy * cosY;

  st.vx += worldAx * dt;
  st.vy += worldAy * dt;

  const currentSpeed = Math.sqrt(st.vx * st.vx + st.vy * st.vy);
  if (currentSpeed > MAX_SPEED) {
    st.vx = (st.vx / currentSpeed) * MAX_SPEED;
    st.vy = (st.vy / currentSpeed) * MAX_SPEED;
  }
  st.vx *= Math.pow(0.86, dt * 60);
  st.vy *= Math.pow(0.86, dt * 60);

  let nextX = st.x + st.vx * dt;
  let nextY = st.y + st.vy * dt;

  if (st.z < NFZ_MAX_Z) {
    nfzZones.forEach(z => {
      if (nextX > z.barrierMinX && nextX < z.barrierMaxX &&
          nextY > z.barrierMinY && nextY < z.barrierMaxY) {
        const dLeft = Math.abs(st.x - z.barrierMinX);
        const dRight = Math.abs(st.x - z.barrierMaxX);
        const dBottom = Math.abs(st.y - z.barrierMinY);
        const dTop = Math.abs(st.y - z.barrierMaxY);
        const minSide = Math.min(dLeft, dRight, dBottom, dTop);
        if (minSide === dLeft) { nextX = z.barrierMinX; if (st.vx > 0) st.vx = 0; }
        else if (minSide === dRight) { nextX = z.barrierMaxX; if (st.vx < 0) st.vx = 0; }
        else if (minSide === dBottom) { nextY = z.barrierMinY; if (st.vy > 0) st.vy = 0; }
        else { nextY = z.barrierMaxY; if (st.vy < 0) st.vy = 0; }
      }
    });
  }

  st.x = nextX;
  st.y = nextY;

  if (st.role === 'executor' && st.payloadActive) {
    st.payloadTimeLeft -= dt;
    if (st.payloadTimeLeft <= 0) {
      st.payloadActive = false;
      st.payloadTimeLeft = 0;
      const currWp = st.waypoints[st.autoIdx];
      if (currWp && currWp.targetId) {
        const tm = targetsData.find(m => m.id === currWp.targetId);
        if (tm) {
          tm.treated = true;
          console.log(`[TREATED MARKED] Target ID: ${tm.id}`);
        }
      }
    }
  }
}

const dt = 0.02;
// 1. Run Recon Drone
for (let step = 0; step < 10000; step++) {
  if (!drone1State.autoPilot) break;
  updatePhysics(drone1State, dt);
}

console.log('Recon complete. Memory count:', drone1State.memory.length);
drone1State.memory.forEach(m => console.log('  Discovered:', m.id, m.type, m.name));

const acceptedCount = planExecutorMissionFromMemory();
console.log('Executor planned waypoints:', drone2State.waypoints.length, 'Accepted targets:', acceptedCount);
drone2State.waypoints.forEach((wp, idx) => console.log(`  WP #${idx}: (${wp.x.toFixed(2)}, ${wp.y.toFixed(2)}, ${wp.z}) ${wp.action ? '[ACTION ID=' + wp.targetId + ']' : ''}`));

drone2State.autoPilot = true;
drone2State.autoIdx = 0;
drone2State.targetZ = 1.2;

for (let step = 0; step < 15000; step++) {
  if (!drone2State.autoPilot) break;
  updatePhysics(drone2State, dt);
}

console.log('Executor finished. Treated count:', targetsData.filter(t => t.treated).length);
targetsData.forEach(t => console.log(`Target ${t.id} (${t.type}): discovered=${t.discovered}, treated=${t.treated}`));
