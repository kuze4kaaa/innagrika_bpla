const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

console.log('Capturing clean view...');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9260',
  '--window-size=1600,900',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9260/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', () => {
      const tabs = JSON.parse(raw);
      const pageTab = tabs.find(t => t.type === 'page' && t.url.includes('localhost'));
      const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

      ws.onopen = () => {
        ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));

        // 1. Initial view (Clean, decluttered)
        setTimeout(() => {
          ws.send(JSON.stringify({ id: 10, method: 'Page.captureScreenshot', params: { format: 'png' } }));
        }, 1200);

        // 2. Switch to 3D Orbit view
        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 20,
            method: 'Runtime.evaluate',
            params: { expression: 'document.getElementById("camOrbit").click();' }
          }));
        }, 2200);

        setTimeout(() => {
          ws.send(JSON.stringify({ id: 21, method: 'Page.captureScreenshot', params: { format: 'png' } }));
        }, 3200);

        // 3. Trigger full chain mission to see live flight
        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 30,
            method: 'Runtime.evaluate',
            params: { expression: 'simSpeed = 8.0; document.getElementById("btnRunChain").click();' }
          }));
        }, 4000);

        setTimeout(() => {
          ws.send(JSON.stringify({ id: 31, method: 'Page.captureScreenshot', params: { format: 'png' } }));
        }, 8000);

        setTimeout(() => {
          chrome.kill();
          process.exit(0);
        }, 10000);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === 10 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/clean_initial.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved scratch/clean_initial.png');
        }
        if (msg.id === 21 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/clean_orbit.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved scratch/clean_orbit.png');
        }
        if (msg.id === 31 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/clean_live.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved scratch/clean_live.png');
        }
      };
    });
  });
}, 1500);
