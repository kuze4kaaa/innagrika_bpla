const fs = require('fs');
let code = fs.readFileSync('scratch/test_drone2_full.js', 'utf8');
code = code.replace(
  'for (let step = 0; step < 15000; step++) {', 
  `for (let step = 0; step < 15000; step++) {
    if (drone2State.autoIdx === 2 && step % 100 === 0) {
      console.log('step=' + step + ' pos=(' + drone2State.x.toFixed(3) + ',' + drone2State.y.toFixed(3) + ') yaw=' + (drone2State.yaw*180/Math.PI).toFixed(1) + ' stuck=' + drone2State.waypointStuckTimer.toFixed(1));
    }`
);
eval(code);
