const fs = require('fs');
let code = fs.readFileSync('scratch/test_drone2_full.js', 'utf8');

// Modify the stuck check to only increment if speed is low or timer is 60s
code = code.replace(
  'if (st.waypointStuckTimer > 15.0) {',
  'if (st.waypointStuckTimer > 60.0) {'
);

eval(code);
