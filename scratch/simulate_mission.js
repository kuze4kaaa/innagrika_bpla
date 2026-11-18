// Headless test of the simulation logic
const THREE = require('./three.min.js');

const FIELD_WIDTH = 6.0;
const FIELD_HEIGHT = 4.0;
const NOMINAL_ALT = 1.2;
const MAX_SPEED = 0.4;
const BUFFER_INFLATION = 0.23;
const DRONE_RADIUS = 0.10;

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

// Generate targets
let targetsData = [];
targetsData.push({ id: 7, type: 'A_NFZ', x: 2.6, y: 2.1, discovered: false, treated: false });
targetsData.push({ id: 8, type: 'A_NFZ', x: 4.4, y: 1.4, discovered: false, treated: false });
targetsData.push({ id: 1, type: 'A', x: 1.10, y: 0.70, discovered: false, treated: false });
targetsData.push({ id: 2, type: 'A', x: 2.50, y: 0.45, discovered: false, treated: false });
targetsData.push({ id: 3, type: 'A', x: 1.10, y: 3.40, discovered: false, treated: false });
targetsData.push({ id: 4, type: 'A', x: 2.60, y: 3.40, discovered: false, treated: false });
targetsData.push({ id: 5, type: 'A', x: 4.50, y: 3.40, discovered: false, treated: false });
targetsData.push({ id: 6, type: 'A', x: 5.45, y: 2.40, discovered: false, treated: false });
targetsData.push({ id: 9, type: 'B', x: 0.80, y: 2.10, discovered: false, treated: false });
targetsData.push({ id: 10, type: 'U', x: 5.40, y: 0.85, discovered: false, treated: false });

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
  memory: []
};

let collisionHits = 0;
const dt = 0.02;

// Run Recon simulation
for (let step = 0; step < 5000; step++) {
  if (!drone1State.autoPilot) break;
  const st = drone1State;
  const wp = st.waypoints[st.autoIdx];
  const isFinalLandingWp = (st.autoIdx === st.waypoints.length - 1);
  const dx = wp.x - st.x;
  const dy = wp.y - st.y;
  const dist = Math.sqrt(dx * dx + dy * dy);

  let acceptDist = isFinalLandingWp ? 0.03 : 0.16;
  let localAx = 0, localAy = 0;

  if (dist > acceptDist) {
    const targetYaw = Math.atan2(dy, dx);
    let diffYaw = targetYaw - st.yaw;
    while (diffYaw > Math.PI) diffYaw -= 2 * Math.PI;
    while (diffYaw < -Math.PI) diffYaw += 2 * Math.PI;
    st.yaw += diffYaw * 4.0 * dt;

    const cosH = Math.cos(st.yaw);
    const sinH = Math.sin(st.yaw);
    const speedFactor = isFinalLandingWp ? 0.70 : 0.95;
    localAx = (dx * cosH + dy * sinH) / dist * speedFactor;
    localAy = (-dx * sinH + dy * cosH) / dist * speedFactor;
    st.targetZ = wp.z;
  } else {
    if (isFinalLandingWp) {
      st.x += (wp.x - st.x) * 12.0 * dt;
      st.y += (wp.y - st.y) * 12.0 * dt;
      st.vx = 0; st.vy = 0;
      st.targetZ = 0.08;
      if (Math.abs(st.z - 0.08) < 0.02) {
        st.x = wp.x; st.y = wp.y; st.z = 0.08;
        st.autoPilot = false;
        break;
      }
    } else {
      st.autoIdx++;
    }
  }

  const errZ = st.targetZ - st.z;
  st.vz += errZ * 3.5 * dt;
  st.vz *= Math.pow(0.85, dt * 60);
  st.z += st.vz * dt;

  const cosY = Math.cos(st.yaw);
  const sinY = Math.sin(st.yaw);
  const worldAx = localAx * cosY - localAy * sinY;
  const worldAy = localAx * sinY + localAy * cosY;
  st.vx += worldAx * dt;
  st.vy += worldAy * dt;
  st.vx *= Math.pow(0.86, dt * 60);
  st.vy *= Math.pow(0.86, dt * 60);

  let nextX = st.x + st.vx * dt;
  let nextY = st.y + st.vy * dt;

  // Collision check
  nfzZones.forEach(z => {
    if (nextX > z.barrierMinX && nextX < z.barrierMaxX &&
        nextY > z.barrierMinY && nextY < z.barrierMaxY) {
      collisionHits++;
    }
  });

  st.x = nextX;
  st.y = nextY;

  // Camera discovery
  targetsData.forEach(t => {
    if (!t.discovered) {
      const d2D = Math.sqrt((st.x - t.x)**2 + (st.y - t.y)**2);
      const maxDetect = (t.type === 'A_NFZ') ? 1.55 : 0.65;
      if (d2D <= maxDetect) {
        t.discovered = true;
        st.memory.push(t);
      }
    }
  });
}

console.log('--- RECON SIMULATION RESULT ---');
console.log('Recon Discovered Targets count:', drone1State.memory.length, '/ 10');
console.log('Collision Hits with NFZ barriers:', collisionHits);
console.log('Recon Final Landing Position:', drone1State.x.toFixed(3), drone1State.y.toFixed(3), drone1State.z.toFixed(3));
console.log('Recon Landing Error from Home-1 (0.4, 0.4):',
  Math.sqrt((drone1State.x - 0.4)**2 + (drone1State.y - 0.4)**2).toFixed(4), 'm');
