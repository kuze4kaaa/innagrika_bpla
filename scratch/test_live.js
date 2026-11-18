const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9243',
  '--window-size=1280,720',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9243/json', (res) => {
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

        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 3,
            method: 'Runtime.evaluate',
            params: {
              expression: 'JSON.stringify({ coverage: slamCoverage.toFixed(1) + "%", memory: drone1State.memory.length, stage: chainStage, d1_fsm: drone1State.fsm, d2_fsm: drone2State.fsm, walls: slamWallsCount })',
              returnByValue: true
            }
          }));
          ws.send(JSON.stringify({ id: 100, method: 'Page.captureScreenshot', params: { format: 'png' } }));
        }, 16000);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === 3) {
          console.log('[FULL MISSION TELEMETRY]:', msg.result);
        }
        if (msg.id === 100 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/screenshot_verified.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved screenshot_verified.png successfully!');
          chrome.kill();
          process.exit(0);
        }
      };
    });
  });
}, 1500);
