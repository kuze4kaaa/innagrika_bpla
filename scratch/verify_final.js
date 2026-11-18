const { spawn } = require('child_process');
const http = require('http');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9245',
  '--window-size=1280,720',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9245/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', () => {
      const tabs = JSON.parse(raw);
      const pageTab = tabs.find(t => t.type === 'page' && t.url.includes('localhost'));
      const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

      ws.onopen = () => {
        ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
        ws.send(JSON.stringify({
          id: 2,
          method: 'Runtime.evaluate',
          params: { expression: 'simSpeed = 8.0; document.getElementById("btnRunChain").click();' }
        }));

        setTimeout(() => {
          ws.send(JSON.stringify({
            id: 3,
            method: 'Runtime.evaluate',
            params: {
              expression: 'JSON.stringify({ treatedCount: targetMeshes.filter(m => m.data.treated).length, targets: targetMeshes.map(m => ({ id: m.data.id, type: m.data.type, treated: m.data.treated })) })',
              returnByValue: true
            }
          }));
        }, 32000);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id === 3) {
          console.log('[BROWSER VERIFICATION RESULT]:', msg.result.result ? msg.result.result.value : msg);
          chrome.kill();
          process.exit(0);
        }
      };
    });
  });
}, 1500);
