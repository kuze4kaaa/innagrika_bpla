const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const tmpDir = path.join(process.env.TEMP || 'C:\\Temp', 'chrome_test_' + Date.now());

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9299',
  '--window-size=1600,900',
  '--use-gl=angle',
  '--use-angle=swiftshader',
  `--user-data-dir=${tmpDir}`,
  'http://localhost:8080/index.html'
]);

function connectWithRetry(retries = 10) {
  const req = http.get('http://127.0.0.1:9299/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', () => {
      let tabs;
      try { tabs = JSON.parse(raw); } catch (e) { return setTimeout(() => connectWithRetry(retries - 1), 500); }
      const pageTab = tabs.find(t => t.type === 'page');
      if (!pageTab) {
        if (retries > 0) return setTimeout(() => connectWithRetry(retries - 1), 500);
        console.error('Page tab not found!');
        chrome.kill();
        process.exit(1);
      }
      setupDebugger(pageTab.webSocketDebuggerUrl);
    });
  });
  req.on('error', (err) => {
    if (retries > 0) {
      setTimeout(() => connectWithRetry(retries - 1), 600);
    } else {
      console.error('Failed to connect to Chrome:', err.message);
      chrome.kill();
      process.exit(1);
    }
  });
}

function setupDebugger(wsUrl) {
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('Connected to Chrome CDP');
    ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
    ws.send(JSON.stringify({ id: 10, method: 'Log.enable' }));

    // 1. Open SLAM minimap, randomize, and run chain
    setTimeout(() => {
      console.log('Triggering SLAM, Randomize & Run Chain...');
      ws.send(JSON.stringify({
        id: 2,
        method: 'Runtime.evaluate',
        params: {
          expression: `
            // Ensure SLAM panel is open
            const slamPnl = document.getElementById('slamMapCard');
            if (slamPnl) slamPnl.style.display = 'block';
            document.getElementById('btnRandomize').click();
            simSpeed = 8.0;
            document.getElementById('btnRunChain').click();
            'OK';
          `
        }
      }));
    }, 1200);

    // 2. Poll status every 1.5 second
    let timer = 0;
    const poll = setInterval(() => {
      timer += 1.5;
      ws.send(JSON.stringify({
        id: 100 + Math.round(timer),
        method: 'Runtime.evaluate',
        params: {
          returnByValue: true,
          expression: `
            ({
              stuck: drone1State.waypointStuckTimer.toFixed(1),
              stage: chainStage,
              autoIdx: drone1State.autoIdx,
              totalWp: drone1State.waypoints.length,
              cov: typeof slamCoverage !== 'undefined' ? slamCoverage.toFixed(1) : '0',
              pos: '(' + drone1State.x.toFixed(2) + ', ' + drone1State.y.toFixed(2) + ')'
            })
          `
        }
      }));

      if (timer >= 18.0) {
        clearInterval(poll);
        console.log('Mission progress check complete. Taking screenshot...');
        ws.send(JSON.stringify({ id: 999, method: 'Page.captureScreenshot', params: { format: 'png' } }));
      }
    }, 1500);
  };

  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.method === 'Runtime.exceptionThrown') {
      console.error('PAGE RUNTIME EXCEPTION:', d.params.exceptionDetails.text, d.params.exceptionDetails.exception ? d.params.exceptionDetails.exception.description : '');
    }
    if (d.id === 2) {
      console.log('Result of Click command:', JSON.stringify(d));
    }
    if (d.id && d.id > 100 && d.id < 999) {
      console.log(`[T+${d.id - 100}s] Eval res:`, JSON.stringify(d.result));
    }
    if (d.id === 999 && d.result && d.result.data) {
      const buf = Buffer.from(d.result.data, 'base64');
      const dest = 'C:\\Users\\finso\\.gemini\\antigravity\\brain\\cf015e45-ab05-48bc-9fad-3fdf5777a73e\\screenshot_honest_slam.png';
      fs.writeFileSync(dest, buf);
      console.log('Saved screenshot successfully to:', dest);
      chrome.kill();
      try { fs.rmSync(tmpDir, { recursive: true, force: true }); } catch(_) {}
      process.exit(0);
    }
  };
}

setTimeout(() => connectWithRetry(15), 1000);
