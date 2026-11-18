const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

console.log('Capturing comparison of drone sizes and real visibility cone...');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9300',
  '--window-size=1440,850',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9300/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', () => {
      const tabs = JSON.parse(raw);
      const pageTab = tabs.find(t => t.type === 'page' && t.url.includes('localhost'));
      const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

      ws.onopen = () => {
        ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));

        // 1. Zoom in on Base 1 and Base 2 to clearly show the drone size difference!
        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 10,
            method: 'Runtime.evaluate',
            params: { expression: 'controls.target.set(0.4, 0.8, 0.1); camera.position.set(0.4 - 1.2, 0.8 - 1.2, 0.85); controls.update();' }
          }));
        }, 1200);

        setTimeout(() => {
          ws.send(JSON.stringify({ id: 11, method: 'Page.captureScreenshot', params: { format: 'png' } }));
        }, 2200);

        // 2. Switch to 3D Orbit view and start recon chain at 2x speed with SLAM map opened
        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 20,
            method: 'Runtime.evaluate',
            params: { expression: 'document.getElementById("camOrbit").click(); document.getElementById("btnToggleSlam").click(); simSpeed = 2.0; document.getElementById("btnRunChain").click();' }
          }));
        }, 3000);

        // Capture live scanning with cone and minimap active
        setTimeout(() => {
          ws.send(JSON.stringify({ id: 21, method: 'Page.captureScreenshot', params: { format: 'png' } }));
        }, 5500);

        setTimeout(() => {
          chrome.kill();
          process.exit(0);
        }, 7000);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === 11 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/view_drone_sizes.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved scratch/view_drone_sizes.png (drone comparison)');
        }
        if (msg.id === 21 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/view_real_cone_scan.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved scratch/view_real_cone_scan.png (real visibility cone)');
        }
      };
    });
  });
}, 1500);
