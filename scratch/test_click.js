const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9252',
  '--window-size=1280,720',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9252/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', () => {
      const tabs = JSON.parse(raw);
      const pageTab = tabs.find(t => t.type === 'page' && t.url.includes('localhost'));
      const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

      ws.onopen = () => {
        ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
        ws.send(JSON.stringify({
          id: 2,
          method: 'Runtime.evaluate',
          params: { expression: 'simSpeed = 8.0; document.getElementById("btnRunChain").click();' }
        }));

        // After recon and during executor mission:
        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 3,
            method: 'Runtime.evaluate',
            params: {
              expression: `(() => {
                const d1 = drone1State;
                const d2 = drone2State;
                const treated = targetsData.filter(t => t.treated).length;
                return JSON.stringify({
                  coverage: slamCoverage.toFixed(1) + "%",
                  reconDiscovered: d1.memory.length,
                  executorWaypointsCount: d2.waypoints.length,
                  executorFsm: d2.fsm,
                  executorPos: { x: d2.x.toFixed(2), y: d2.y.toFixed(2), z: d2.z.toFixed(2) },
                  treatedTargetsCount: treated,
                  chainStage: chainStage,
                  chainRunning: chainRunning
                });
              })()`,
              returnByValue: true
            }
          }));
          ws.send(JSON.stringify({ id: 100, method: 'Page.captureScreenshot', params: { format: 'png' } }));
        }, 18000);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === 3) {
          console.log('[INTELLIGENT MISSION TELEMETRY]:', msg.result ? msg.result.result.value : null);
        }
        if (msg.id === 100 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/screenshot_optimal_pair.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved screenshot_optimal_pair.png successfully!');
          chrome.kill();
          process.exit(0);
        }
      };
    });
  });
}, 1200);
