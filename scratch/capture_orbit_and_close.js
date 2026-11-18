const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9255',
  '--window-size=1600,900',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9255/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', () => {
      const tabs = JSON.parse(raw);
      const pageTab = tabs.find(t => t.type === 'page' && t.url.includes('localhost'));
      const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

      ws.onopen = () => {
        ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));

        // Click camOrbit
        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 10,
            method: 'Runtime.evaluate',
            params: { expression: 'document.getElementById("camOrbit").click();' }
          }));
        }, 1200);

        setTimeout(() => {
          ws.send(JSON.stringify({ id: 11, method: 'Page.captureScreenshot', params: { format: 'png' } }));
        }, 2200);

        // Click camCloseTarget
        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 20,
            method: 'Runtime.evaluate',
            params: { expression: 'document.getElementById("camCloseTarget").click();' }
          }));
        }, 3200);

        setTimeout(() => {
          ws.send(JSON.stringify({ id: 21, method: 'Page.captureScreenshot', params: { format: 'png' } }));
        }, 4200);

        setTimeout(() => {
          chrome.kill();
          process.exit(0);
        }, 5500);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === 11 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/view_orbit_perfect.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved scratch/view_orbit_perfect.png');
        }
        if (msg.id === 21 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/view_target_close.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved scratch/view_target_close.png');
        }
      };
    });
  });
}, 1500);
