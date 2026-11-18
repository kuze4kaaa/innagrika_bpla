const { spawn } = require('child_process');
const http = require('http');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9237',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9237/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', () => {
      const tabs = JSON.parse(raw);
      const pageTab = tabs.find(t => t.type === 'page' && t.url.includes('localhost'));
      const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

      ws.onopen = () => {
        ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
        setTimeout(() => {
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
              expression: 'JSON.stringify({ coverage: slamCoverage.toFixed(1) + "%", memory: drone1State.memory.length, waypoints: drone2State.waypoints.length, wallsCount: slamWallsCount, d1_pos: [drone1State.x.toFixed(2), drone1State.y.toFixed(2)] })',
              returnByValue: true
            }
          }));
        }, 5000);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === 3) {
          console.log('RESULTS FROM BROWSER:', msg.result.result ? msg.result.result.value : msg);
          chrome.kill();
          process.exit(0);
        }
      };
    });
  });
}, 1500);
