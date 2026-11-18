const { spawn } = require('child_process');
const http = require('http');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9320',
  '--window-size=1440,850',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9320/json', (res) => {
    let raw = '';
    res.on('data', c => raw += c);
    res.on('end', () => {
      const tabs = JSON.parse(raw);
      const tab = tabs.find(t => t.url.includes('8080'));
      const ws = new WebSocket(tab.webSocketDebuggerUrl);

      let msgId = 1;
      const pending = new Map();
      function send(method, params = {}) {
        return new Promise(r => {
          const id = msgId++;
          pending.set(id, r);
          ws.send(JSON.stringify({ id, method, params }));
        });
      }
      function evaluate(expr) {
        return send('Runtime.evaluate', { expression: expr, returnByValue: true }).then(r => r && r.result ? r.result.value : null);
      }
      ws.onmessage = e => {
        const d = JSON.parse(e.data);
        if (d.id && pending.has(d.id)) {
          const cb = pending.get(d.id);
          pending.delete(d.id);
          cb(d.result);
        }
      };

      ws.onopen = async () => {
        await send('Runtime.enable');
        await new Promise(r => setTimeout(r, 1000));

        // Click randomize
        console.log('Clicking Randomize...');
        await evaluate(`document.getElementById('btnRandomize').click()`);
        await new Promise(r => setTimeout(r, 500));

        // Click Run Chain at 4x speed
        console.log('Starting Chain...');
        await evaluate(`simSpeed = 4.0; document.getElementById('btnRunChain').click();`);

        let collisions = 0;
        let lastReport = Date.now();
        const start = Date.now();

        const poll = setInterval(async () => {
          const info = await evaluate(`
            ({
              x: drone1State.x.toFixed(3),
              y: drone1State.y.toFixed(3),
              vx: drone1State.vx.toFixed(3),
              vy: drone1State.vy.toFixed(3),
              autoIdx: drone1State.autoIdx,
              totalWp: drone1State.waypoints.length,
              stuckTimer: drone1State.waypointStuckTimer.toFixed(2),
              stage: chainStage,
              fsm: drone1State.fsm,
              nfz: nfzZones.map(z => ({
                bMinX: z.barrierMinX.toFixed(2), bMaxX: z.barrierMaxX.toFixed(2),
                bMinY: z.barrierMinY.toFixed(2), bMaxY: z.barrierMaxY.toFixed(2)
              }))
            })
          `);
          if (!info) return;

          // Check if drone1 is inside barrier
          for (const z of info.nfz) {
            if (info.x > z.bMinX && info.x < z.bMaxX && info.y > z.bMinY && info.y < z.bMaxY) {
              console.log(`COLLISION DETECTED at (${info.x}, ${info.y})! WP ${info.autoIdx}/${info.totalWp}, Stuck: ${info.stuckTimer}s`);
              collisions++;
            }
          }

          if (parseFloat(info.stuckTimer) > 2.0) {
            console.log(`DRONE STUCK for ${info.stuckTimer}s at (${info.x}, ${info.y}) on WP ${info.autoIdx}/${info.totalWp}! Target was:`, await evaluate(`JSON.stringify(drone1State.waypoints[drone1State.autoIdx])`));
            clearInterval(poll);
            ws.close();
            chrome.kill();
            process.exit(0);
          }

          if (Date.now() - lastReport >= 2000) {
            console.log(`[T+${((Date.now()-start)/1000).toFixed(0)}s] (${info.x}, ${info.y}) WP ${info.autoIdx}/${info.totalWp}, FSM: ${info.fsm}`);
            lastReport = Date.now();
          }

          if (info.stage >= 2 || (Date.now() - start) > 40000) {
            console.log('Recon finished or timeout. Total collision steps:', collisions);
            clearInterval(poll);
            ws.close();
            chrome.kill();
            process.exit(0);
          }
        }, 100);
      };
    });
  });
}, 2000);
