
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

let st = {
  x: 0.4, y: 0.4, z: 0.08,
  vx: 0, vy: 0, vz: 0,
  yaw: 0, pitch: 0, roll: 0,
  targetZ: 1.2,
  autoPilot: true,
  waypoints: plannedReconWaypoints,
  autoIdx: 0
};
const dt = 0.02;

for (let step = 0; step < 8000; step++) {
  if (!st.autoPilot) break;
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
      st.autoPilot = false;
      break;
    } else {
      st.autoIdx++;
    }
  }

  const cosY = Math.cos(st.yaw);
  const sinY = Math.sin(st.yaw);
  const worldAx = localAx * cosY - localAy * sinY;
  const worldAy = localAx * sinY + localAy * cosY;
  st.vx += worldAx * dt;
  st.vy += worldAy * dt;
  st.vx *= Math.pow(0.86, dt * 60);
  st.vy *= Math.pow(0.86, dt * 60);
  st.x += st.vx * dt;
  st.y += st.vy * dt;

  if (step % 400 === 0) {
    console.log('step ' + step + ' (t=' + (step*dt).toFixed(1) + 's): idx=' + st.autoIdx + ' pos=(' + st.x.toFixed(2) + ',' + st.y.toFixed(2) + ')');
  }
}
console.log('Done! Final autoIdx:', st.autoIdx, 'pos:', st.x.toFixed(3), st.y.toFixed(3));
