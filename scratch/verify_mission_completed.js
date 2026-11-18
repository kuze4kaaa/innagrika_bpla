const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

console.log('Testing mission completion state at 16x speed...');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9311',
  '--window-size=1440,850',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9311/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', () => {
      const tabs = JSON.parse(raw);
      const pageTab = tabs.find(t => t.type === 'page' && t.url.includes('localhost'));
      const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

      ws.onopen = () => {
        ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));

        // Start mission at 16x speed
        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 10,
            method: 'Runtime.evaluate',
            params: { expression: 'simSpeed = 16.0; document.getElementById("btnRunChain").click();' }
          }));
        }, 1000);

        // Periodically poll until chainRunning becomes false and chainStage === 4
        let checkInterval = setInterval(() => {
          ws.send(JSON.stringify({
            id: 20,
            method: 'Runtime.evaluate',
            params: { expression: 'JSON.stringify({ chainRunning, chainStage, fsm: activeDrone.fsm, p1: document.getElementById("pipe1").className, p2: document.getElementById("pipe2").className, p3: document.getElementById("pipe3").className, p4: document.getElementById("pipe4").className, sub: document.getElementById("pipelineSubtext").textContent });' }
          }));
        }, 1000);

        ws.onmessage = (event) => {
          const msg = JSON.parse(event.data);
          if (msg.id === 20 && msg.result && msg.result.result) {
            const data = JSON.parse(msg.result.result.value);
            console.log('Poll state:', data.chainStage, data.fsm, 'pipe classes:', data.p1, data.p2, data.p3, data.p4);
            if (!data.chainRunning && data.chainStage === 4) {
              clearInterval(checkInterval);
              console.log('MISSION FINISHED! Capturing final screenshot...');
              setTimeout(() => {
                ws.send(JSON.stringify({ id: 30, method: 'Page.captureScreenshot', params: { format: 'png' } }));
              }, 600);
            }
          }

          if (msg.id === 30 && msg.result && msg.result.data) {
            fs.writeFileSync('scratch/view_mission_completed.png', Buffer.from(msg.result.data, 'base64'));
            console.log('Saved scratch/view_mission_completed.png!');
            chrome.kill();
            process.exit(0);
          }
        };

        // Safety timeout (70s)
        setTimeout(() => {
          console.log('Timed out waiting for mission finish');
          chrome.kill();
          process.exit(1);
        }, 70000);
      };
    });
  });
}, 1500);
