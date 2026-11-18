const fs = require('fs');
let code = fs.readFileSync('scratch/test_drone2_full.js', 'utf8');

// Replace stuck timer and speed calculation
code = code.replace(
  `      const speedFactor = (wp.action || isFinalLandingWp) ? 0.70 : 0.95;
      localAx = (dx * cosH + dy * sinH) / dist * speedFactor;
      localAy = (-dx * sinH + dy * cosH) / dist * speedFactor;`,
  `      const baseSpeed = (wp.action || isFinalLandingWp) ? 0.75 : 1.1;
      const speedFactor = dist > 0.4 ? Math.min(1.8, dist * 1.5) : baseSpeed;
      localAx = (dx * cosH + dy * sinH) / dist * speedFactor;
      localAy = (-dx * sinH + dy * cosH) / dist * speedFactor;`
);

code = code.replace(
  'if (st.waypointStuckTimer > 15.0) {',
  'if (st.waypointStuckTimer > 45.0) {'
);

eval(code);
