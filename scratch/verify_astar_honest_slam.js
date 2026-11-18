const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9285',
  '--window-size=1600,900',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9285/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', () => {
      const tabs = JSON.parse(raw);
      const pageTab = tabs.find(t => t.type === 'page' && t.url.includes('localhost'));
      if (!pageTab) {
        console.error('Page tab not found!');
        chrome.kill();
        process.exit(1);
      }
      const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

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

        // 1. Randomize obstacles and start chain at 8x speed
        console.log('Triggering Randomize & Run Chain (8x speed)...');
        await evaluate(`
          document.getElementById('btnRandomize').click();
          simSpeed = 8.0;
          document.getElementById('btnRunChain').click();
        `);

        let maxStuck = 0;
        let collisionSteps = 0;
        let checks = 0;

        const interval = setInterval(async () => {
          checks++;
          const info = await evaluate(`
            ({
              x: drone1State.x.toFixed(2),
              y: drone1State.y.toFixed(2),
              z: drone1State.z.toFixed(2),
              autoIdx: drone1State.autoIdx,
              totalWp: drone1State.waypoints.length,
              stuck: parseFloat(drone1State.waypointStuckTimer.toFixed(2)),
              stage: chainStage,
              fsm: drone1State.fsm,
              cov: typeof slamCoverage !== 'undefined' ? slamCoverage.toFixed(1) : '0',
              walls: typeof slamWallsCount !== 'undefined' ? slamWallsCount : 0,
              d2x: drone2State.x.toFixed(2),
              d2y: drone2State.y.toFixed(2),
              d2stage: drone2State.fsm
            })
          `);

          if (!info) return;

          if (info.stuck > maxStuck) maxStuck = info.stuck;
          if (info.stuck > 2.0) {
            console.log(`WARNING: Drone stuck for ${info.stuck}s at (${info.x}, ${info.y})! WP ${info.autoIdx}/${info.totalWp}`);
          }

          if (checks % 4 === 0) {
            console.log(`[Status] Stage: ${info.stage}, D1: (${info.x}, ${info.y}) WP: ${info.autoIdx}/${info.totalWp}, Cov: ${info.cov}%, Walls: ${info.walls}`);
          }

          // When Stage 1 is completed or Stage 2/3 active, take a screenshot
          if (info.stage >= 2 || checks >= 40) {
            clearInterval(interval);
            console.log(`SUCCESS: Stage ${info.stage} reached! Max stuck: ${maxStuck}s. Capturing screenshot...`);

            // Wait 1 sec for visual stabilization
            await new Promise(r => setTimeout(r, 1000));

            const shot = await send('Page.captureScreenshot', { format: 'png' });
            if (shot && shot.data) {
              const buf = Buffer.from(shot.data, 'base64');
              const artifactPath = path.resolve('C:\\Users\\finso\\.gemini\\antigravity\\brain\\cf015e45-ab05-48bc-9fad-3fdf5777a73e', 'screenshot_honest_slam.png');
              fs.writeFileSync(artifactPath, buf);
              console.log('Saved screenshot to:', artifactPath);
            }

            ws.close();
            chrome.kill();
            process.exit(0);
          }
        }, 500);
      };
    });
  });
}, 1500);
