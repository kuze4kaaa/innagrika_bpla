const { spawn } = require('child_process');
const http = require('http');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9238',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9238/json', (res) => {
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
              expression: 'JSON.stringify({ coverage: slamCoverage.toFixed(1) + "%", memory: drone1State.memory.length, waypoints: drone2State.waypoints.length, wallsCount: slamWallsCount, stage: chainStage, d1_fsm: drone1State.fsm, d2_fsm: drone2State.fsm })',
              returnByValue: true
            }
          }));
        }, 12000); // 12s * 8x = 96 seconds of simulation!
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === 3) {
          console.log('RESULTS AFTER COMPLETE SCAN:', msg.result.result ? msg.result.result.value : msg);
          chrome.kill();
          process.exit(0);
        }
      };
    });
  });
}, 1500);
