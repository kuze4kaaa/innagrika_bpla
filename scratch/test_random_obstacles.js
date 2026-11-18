const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

console.log('--- Testing Obstacle Randomization & Full Dual-Drone Chain ---');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9315',
  '--window-size=1440,850',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

setTimeout(() => {
  http.get('http://localhost:9315/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', () => {
      const tabs = JSON.parse(raw);
      const pageTab = tabs.find(t => t.url.includes('8080'));
      if (!pageTab) {
        console.error('Page tab not found');
        chrome.kill();
        process.exit(1);
      }

      const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

      let msgId = 1;
      const pending = new Map();

      function send(method, params = {}) {
        return new Promise((resolve) => {
          const id = msgId++;
          pending.set(id, resolve);
          ws.send(JSON.stringify({ id, method, params }));
        });
      }

      function evaluate(expression) {
        return send('Runtime.evaluate', { expression, returnByValue: true })
          .then(r => (r && r.result ? r.result.value : null));
      }

      ws.onmessage = (event) => {
        const resp = JSON.parse(event.data);
        if (resp.id && pending.has(resp.id)) {
          const resolve = pending.get(resp.id);
          pending.delete(resp.id);
          resolve(resp.result);
        }
      };

      ws.onopen = async () => {
        console.log('Connected to Chrome DevTools WebSocket.');

        await send('Runtime.enable');
        await new Promise(r => setTimeout(r, 1500));

        // 1. Initial positions of NFZ
        const initialNfz = await evaluate(`
          JSON.stringify(nfzZones.map(z => ({ id: z.id, cx: z.cx, cy: z.cy })))
        `);
        console.log('Initial NFZ Positions:', initialNfz);

        // 2. Click btnRandomize
        console.log('Clicking btnRandomize (Новая карта)...');
        await evaluate(`document.getElementById('btnRandomize').click()`);
        await new Promise(r => setTimeout(r, 600));

        // 3. New positions of NFZ
        const randomizedNfz = await evaluate(`
          JSON.stringify(nfzZones.map(z => ({
            id: z.id,
            cx: z.cx.toFixed(3),
            cy: z.cy.toFixed(3),
            meshX: z.mesh ? z.mesh.position.x.toFixed(3) : null,
            meshY: z.mesh ? z.mesh.position.y.toFixed(3) : null,
            groupX: z.group ? z.group.position.x.toFixed(3) : null,
            groupY: z.group ? z.group.position.y.toFixed(3) : null
          })))
        `);
        console.log('Randomized NFZ Positions & 3D Meshes:', randomizedNfz);

        // Check if targets 7 and 8 are inside NFZ
        const targetsNfzCheck = await evaluate(`
          JSON.stringify(targetsData.filter(t => t.type === 'A_NFZ').map(t => ({
            id: t.id,
            name: t.name,
            x: t.x.toFixed(3),
            y: t.y.toFixed(3)
          })))
        `);
        console.log('NFZ Target Positions (Targets 7 & 8):', targetsNfzCheck);

        // 4. Start Full Mission Chain
        console.log('Starting Full Mission Chain...');
        await evaluate(`
          // Открываем карточку 2D SLAM
          const slamCard = document.getElementById('slamMapCard');
          if (slamCard) slamCard.style.display = 'block';

          simSpeed = 8.0;
          document.getElementById('btnRunChain').click();
        `);

        // 5. Monitor mission progress
        let lastReport = 0;
        let finished = false;
        const startTime = Date.now();

        while (!finished && (Date.now() - startTime) < 90000) {
          await new Promise(r => setTimeout(r, 1000));
          const state = await evaluate(`
            ({
              chainRunning,
              chainStage,
              d1_fsm: drone1State.fsm,
              d1_cov: slamCoverage.toFixed(1),
              d1_disc: drone1State.memory ? drone1State.memory.length : 0,
              d2_fsm: drone2State.fsm,
              d2_active: drone2State.payloadActive,
              d2_treated: targetsData.filter(t => t.treated).length,
              pipe: [1,2,3,4].map(s => document.getElementById('pipe'+s).className)
            })
          `);

          if (state && Date.now() - lastReport >= 4000) {
            console.log(`[T+${((Date.now()-startTime)/1000).toFixed(0)}s] Stage ${state.chainStage} | D1: ${state.d1_fsm} (Cov: ${state.d1_cov}%, Disc: ${state.d1_disc}/10) | D2: ${state.d2_fsm} (Treated: ${state.d2_treated}/6)`);
            lastReport = Date.now();
          }

          if (state && (state.chainStage === 4 || state.d2_fsm.includes('COMPLETE') || (state.d2_fsm.includes('HOME-2') && state.d2_treated >= 6))) {
            finished = true;
            console.log('Mission chain successfully reached completion!');
            break;
          }
        }

        await new Promise(r => setTimeout(r, 2000));

        // 6. Capture screenshot
        console.log('Capturing screenshot of completed mission...');
        const screenshot = await send('Page.captureScreenshot', { format: 'png' });
        if (screenshot && screenshot.data) {
          const buf = Buffer.from(screenshot.data, 'base64');
          const outPath = 'C:\\Users\\finso\\.gemini\\antigravity\\brain\\cf015e45-ab05-48bc-9fad-3fdf5777a73e\\screenshot_randomized_nfz.png';
          fs.writeFileSync(outPath, buf);
          fs.writeFileSync('scratch/screenshot_randomized_nfz.png', buf);
          console.log('Screenshot saved to:', outPath);
        }

        // Final verification summary
        const summary = await evaluate(`
          ({
            slamCoverage: slamCoverage.toFixed(1),
            discoveredCount: drone1State.discoveredCount,
            nfzZones: nfzZones.map(z => ({ id: z.id, cx: z.cx.toFixed(2), cy: z.cy.toFixed(2) })),
            d1_fsm: drone1State.fsm,
            d2_fsm: drone2State.fsm,
            d2_treated: targetsData.filter(t => t.treated).length
          })
        `);
        console.log('=== Final Verification Summary ===', JSON.stringify(summary, null, 2));

        ws.close();
        chrome.kill();
        process.exit(0);
      };
    });
  });
}, 2000);
