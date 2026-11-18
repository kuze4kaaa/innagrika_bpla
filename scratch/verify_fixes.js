const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9235',
  '--window-size=1280,720',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9235/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', () => {
      const tabs = JSON.parse(raw);
      const pageTab = tabs.find(t => t.type === 'page' && t.url.includes('localhost'));
      const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

      ws.onopen = () => {
        ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
        setTimeout(() => {
          // Set speed to 8x and run chain
          ws.send(JSON.stringify({
            id: 2,
            method: 'Runtime.evaluate',
            params: { expression: 'simSpeed = 8.0; document.getElementById("btnRunChain").click();' }
          }));
        }, 800);

        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 3,
            method: 'Runtime.evaluate',
            params: {
              expression: 'JSON.stringify({ coverage: slamCoverage.toFixed(1) + "%", memory: drone1State.memory.length, execWp: drone2State.waypoints.length, d1Pos: [drone1State.x.toFixed(2), drone1State.y.toFixed(2)], coneVisible: drone1Obj.cameraFrustum.visible })',
              returnByValue: true
            }
          }));
          ws.send(JSON.stringify({ id: 100, method: 'Page.captureScreenshot', params: { format: 'png' } }));
        }, 5000);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === 3 && msg.result && msg.result.value) {
          console.log('LIVE TELEMETRY AFTER FLIGHT:', msg.result.value);
        }
        if (msg.id === 100 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/screenshot_verified.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved screenshot to scratch/screenshot_verified.png');
          chrome.kill();
          process.exit(0);
        }
      };
    });
  });
}, 1500);
