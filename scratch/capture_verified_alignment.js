const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

console.log('Capturing verified alignment at 1366x768 (standard laptop resolution)...');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9280',
  '--window-size=1366,768',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9280/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', () => {
      const tabs = JSON.parse(raw);
      const pageTab = tabs.find(t => t.type === 'page' && t.url.includes('localhost'));
      const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

      ws.onopen = () => {
        ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));

        // Switch to Orbit view to see whole field
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

        setTimeout(() => {
          chrome.kill();
          process.exit(0);
        }, 3500);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === 11 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/view_aligned_1366.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved scratch/view_aligned_1366.png');
        }
      };
    });
  });
}, 1500);
