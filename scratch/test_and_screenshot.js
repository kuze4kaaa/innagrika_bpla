const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

console.log('Starting headless Chrome test...');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9250',
  '--window-size=1600,900',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9250/json', (res) => {
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

      ws.onopen = () => {
        console.log('WebSocket connected to Chrome CDP');
        ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
        ws.send(JSON.stringify({ id: 2, method: 'Log.enable' }));

        // Capture initial view after 2 seconds
        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 10,
            method: 'Page.captureScreenshot',
            params: { format: 'png' }
          }));
        }, 2000);

        // Switch to Orbit view and take isometric screenshot
        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 20,
            method: 'Runtime.evaluate',
            params: { expression: 'document.getElementById("camOrbit").click();' }
          }));
        }, 3000);

        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 21,
            method: 'Page.captureScreenshot',
            params: { format: 'png' }
          }));
        }, 4000);

        // Run full mission chain at 8x speed to verify execution & treatment
        setTimeout(() => {
          console.log('Triggering full chain mission...');
          ws.send(JSON.stringify({
            id: 30,
            method: 'Runtime.evaluate',
            params: { expression: 'simSpeed = 8.0; document.getElementById("btnRunChain").click();' }
          }));
        }, 4500);

        // Capture live mission screenshot after 8 seconds
        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 40,
            method: 'Page.captureScreenshot',
            params: { format: 'png' }
          }));
        }, 11000);

        // Finish after 14 seconds
        setTimeout(() => {
          console.log('Finished testing.');
          chrome.kill();
          process.exit(0);
        }, 13000);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        if (msg.method === 'Runtime.consoleAPICalled') {
          console.log('Console [' + msg.params.type + ']:', msg.params.args.map(a => a.value || a.description).join(' '));
        }

        if (msg.id === 10 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/view_initial.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved scratch/view_initial.png (1600x900)');
        }

        if (msg.id === 21 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/view_orbit.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved scratch/view_orbit.png (1600x900)');
        }

        if (msg.id === 40 && msg.result && msg.result.data) {
          fs.writeFileSync('scratch/view_live_mission.png', Buffer.from(msg.result.data, 'base64'));
          console.log('Saved scratch/view_live_mission.png (1600x900)');
        }
      };
    });
  });
}, 1500);
