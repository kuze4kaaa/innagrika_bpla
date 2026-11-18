const { spawn } = require('child_process');
const http = require('http');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9244',
  '--window-size=1280,720',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9244/json', (res) => {
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
          params: { expression: 'simSpeed = 10.0; document.getElementById("btnRunChain").click();' }
        }));

        let count = 0;
        const interval = setInterval(() => {
          count++;
          ws.send(JSON.stringify({
            id: 10 + count,
            method: 'Runtime.evaluate',
            params: {
              expression: `(() => {
                try {
                  return JSON.stringify({
                    time: ${count},
                    chainStage: typeof chainStage !== 'undefined' ? chainStage : null,
                    d1_fsm: typeof drone1State !== 'undefined' ? drone1State.fsm : null,
                    d1_mem: typeof drone1State !== 'undefined' ? drone1State.memory.length : null,
                    d2_auto: typeof drone2State !== 'undefined' ? drone2State.autoPilot : null,
                    d2_idx: typeof drone2State !== 'undefined' ? drone2State.autoIdx : null,
                    d2_wp_len: typeof drone2State !== 'undefined' ? drone2State.waypoints.length : null,
                    d2_fsm: typeof drone2State !== 'undefined' ? drone2State.fsm : null,
                    d2_pos: typeof drone2State !== 'undefined' ? [drone2State.x.toFixed(2), drone2State.y.toFixed(2), drone2State.z.toFixed(2)] : null,
                    treated: typeof targetsData !== 'undefined' ? targetsData.filter(t => t.treated).map(t => t.id) : [],
                    acceptedWps: typeof drone2State !== 'undefined' ? drone2State.waypoints.filter(w => w.action).map(w => w.targetId) : []
                  });
                } catch(e) {
                  return JSON.stringify({ error: e.message });
                }
              })()`,
              returnByValue: true
            }
          }));

          if (count >= 30) {
            clearInterval(interval);
            setTimeout(() => {
              chrome.kill();
              process.exit(0);
            }, 500);
          }
        }, 1000);
      };

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id >= 11 && msg.result && msg.result.result) {
          console.log(`[MSG ${msg.id}]:`, msg.result.result.value);
        } else if (msg.id >= 11) {
          console.log(`[MSG ${msg.id} raw]:`, msg);
        }
      };
    });
  });
}, 1500);
