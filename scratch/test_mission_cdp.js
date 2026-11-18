const { spawn } = require('child_process');
const http = require('http');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9231',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9231/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', () => {
      const tabs = JSON.parse(raw);
      const pageTab = tabs.find(t => t.type === 'page' && t.url.includes('localhost'));
      const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

      ws.onopen = () => {
        ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
        setTimeout(() => {
          // Set speed to 8x and trigger mission chain
          ws.send(JSON.stringify({
            id: 2,
            method: 'Runtime.evaluate',
            params: { expression: 'simSpeed = 8.0; document.getElementById("btnRunChain").click();' }
          }));
        }, 1000);

        setTimeout(() => {
          // Query state
          ws.send(JSON.stringify({
            id: 3,
            method: 'Runtime.evaluate',
            params: {
              expression: 'JSON.stringify({ coverage: slamCoverage.toFixed(1) + "%", discovered: drone1State.memory.length, stage: chainStage, d1_fsm: drone1State.fsm, d2_fsm: drone2State.fsm, walls: slamWallsCount })'
            }
          }));
        }, 7000);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === 3 && msg.result && msg.result.value) {
          console.log('MISSION STATUS:', msg.result.value);
          chrome.kill();
          process.exit(0);
        }
      };
    });
  });
}, 2000);
