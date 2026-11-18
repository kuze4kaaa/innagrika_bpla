const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');

console.log('=== STARTING AUTOMATED BROWSER QA TEST OF 3D SIMULATOR ===');

const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
  '--headless=new',
  '--remote-debugging-port=9252',
  '--window-size=1600,950',
  '--disable-gpu',
  'http://localhost:8080/index.html'
]);

const consoleLogs = [];
const pageErrors = [];

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

setTimeout(() => {
  http.get('http://localhost:9252/json', (res) => {
    let raw = '';
    res.on('data', chunk => raw += chunk);
    res.on('end', async () => {
      let tabs;
      try {
        tabs = JSON.parse(raw);
      } catch (e) {
        console.error('Failed to parse CDP JSON:', e);
        chrome.kill();
        process.exit(1);
      }

      const pageTab = tabs.find(t => t.type === 'page' && t.url.includes('localhost'));
      if (!pageTab) {
        console.error('Target page tab not found!');
        chrome.kill();
        process.exit(1);
      }

      const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

      let reqId = 100;
      const pendingCallbacks = new Map();

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        if (msg.method === 'Runtime.consoleAPICalled') {
          const text = msg.params.args.map(a => a.value !== undefined ? a.value : (a.description || '')).join(' ');
          consoleLogs.push({ type: msg.params.type, text });
        }

        if (msg.method === 'Runtime.exceptionThrown') {
          pageErrors.push(msg.params.exceptionDetails);
        }

        if (msg.id && pendingCallbacks.has(msg.id)) {
          const cb = pendingCallbacks.get(msg.id);
          pendingCallbacks.delete(msg.id);
          cb(msg.result);
        }
      };

      function sendCDP(method, params = {}) {
        return new Promise((resolve) => {
          const id = ++reqId;
          pendingCallbacks.set(id, resolve);
          ws.send(JSON.stringify({ id, method, params }));
        });
      }

      async function evalJS(expr) {
        const res = await sendCDP('Runtime.evaluate', {
          expression: expr,
          returnByValue: true
        });
        return res && res.result ? res.result.value : null;
      }

      async function takeScreenshot(filePath) {
        const res = await sendCDP('Page.captureScreenshot', { format: 'png' });
        if (res && res.data) {
          fs.writeFileSync(filePath, Buffer.from(res.data, 'base64'));
          console.log(`[SCREENSHOT] Saved: ${filePath}`);
        }
      }

      ws.onopen = async () => {
        console.log('[CDP] Connected successfully to Chrome DevTools Protocol');
        await sendCDP('Runtime.enable');
        await sendCDP('Log.enable');
        await sendCDP('Page.enable');

        await sleep(2500);

        const testReport = {
          threeJsInitialized: false,
          sceneObjectsCount: 0,
          targetsTotal: 0,
          nfzZonesTotal: 0,
          initialUI: null,
          cameraTests: {},
          takeoffTest: null,
          droneSwitchTest: null,
          payloadTest: null,
          fullMissionTest: null,
          pageErrors: [],
          consoleLogs: []
        };

        // 1. Проверка инициализации Three.js сцены и объектов
        const sceneCheck = await evalJS(`({
          loaded: typeof THREE !== 'undefined',
          sceneChildren: typeof scene !== 'undefined' ? scene.children.length : 0,
          reconPresent: typeof reconState !== 'undefined' && reconState !== null,
          execPresent: typeof execState !== 'undefined' && execState !== null,
          targetsCount: typeof targets !== 'undefined' ? targets.length : 0,
          nfzCount: typeof nfzZones !== 'undefined' ? nfzZones.length : 0
        })`);
        console.log('[TEST 1] Scene state:', JSON.stringify(sceneCheck));
        testReport.threeJsInitialized = sceneCheck ? sceneCheck.loaded : false;
        testReport.sceneObjectsCount = sceneCheck ? sceneCheck.sceneChildren : 0;
        testReport.targetsTotal = sceneCheck ? sceneCheck.targetsCount : 0;
        testReport.nfzZonesTotal = sceneCheck ? sceneCheck.nfzCount : 0;

        // 2. Исходная телеметрия
        const initialUI = await evalJS(`({
          fsmStatus: document.getElementById('fsmStatus')?.textContent,
          activeDroneName: document.getElementById('activeDroneName')?.textContent,
          coords: document.getElementById('coordsValue')?.textContent,
          speed: document.getElementById('speedValue')?.textContent,
          targetsDiscovered: document.getElementById('targetsDiscoveredValue')?.textContent,
          slamBadge: document.getElementById('slamCoverageBadge')?.textContent
        })`);
        console.log('[TEST 2] Initial Telemetry:', JSON.stringify(initialUI));
        testReport.initialUI = initialUI;
        await takeScreenshot('scratch/test_stage1_ready.png');

        // 3. Тест переключения камер
        await evalJS(`document.getElementById('camOrbit')?.click()`);
        await sleep(400);
        await takeScreenshot('scratch/test_cam_orbit.png');
        await evalJS(`document.getElementById('camTop')?.click()`);
        await sleep(400);
        await takeScreenshot('scratch/test_cam_top.png');
        await evalJS(`document.getElementById('camTrack')?.click()`);
        await sleep(400);

        // 4. Тест ручного взлета и набора высоты
        console.log('[TEST 4] Testing Manual Takeoff...');
        await evalJS(`document.getElementById('btnTakeoff')?.click();`);
        await evalJS(`simSpeed = 4.0;`);
        await sleep(2500);

        const takeoffStatus = await evalJS(`({
          fsmStatus: document.getElementById('fsmStatus')?.textContent,
          coords: document.getElementById('coordsValue')?.textContent,
          reconZ: typeof reconState !== 'undefined' ? reconState.z.toFixed(2) : null,
          reconFsm: typeof reconState !== 'undefined' ? reconState.fsm : null
        })`);
        console.log('[TEST 4] Takeoff Telemetry:', JSON.stringify(takeoffStatus));
        testReport.takeoffTest = takeoffStatus;
        await takeScreenshot('scratch/test_stage2_hover.png');

        // Посадка
        await evalJS(`document.getElementById('btnLand')?.click();`);
        await sleep(2500);

        // 5. Тест выбора БПЛА-2 и включения полезной нагрузки (LED)
        console.log('[TEST 5] Testing Drone 2 and LED Payload...');
        await evalJS(`document.getElementById('selectExec')?.click();`);
        await sleep(300);
        await evalJS(`document.getElementById('btnTakeoff')?.click();`);
        await sleep(2500);
        await evalJS(`document.getElementById('btnPayload')?.click();`);
        await sleep(600);

        const payloadStatus = await evalJS(`({
          activeDrone: document.getElementById('activeDroneName')?.textContent,
          payloadText: document.getElementById('payloadText')?.textContent,
          payloadLedClass: document.getElementById('payloadLed')?.className,
          execLedActive: typeof execState !== 'undefined' ? execState.payloadActive : null,
          execPayloadTimer: typeof execState !== 'undefined' ? execState.payloadTimeLeft.toFixed(1) : null
        })`);
        console.log('[TEST 5] Payload Telemetry:', JSON.stringify(payloadStatus));
        testReport.payloadTest = payloadStatus;
        await takeScreenshot('scratch/test_stage3_payload.png');

        await evalJS(`document.getElementById('btnLand')?.click();`);
        await sleep(2500);

        // 6. Сброс и запуск полной автоматической миссии (Автомиссия по ТЗ)
        console.log('[TEST 6] Triggering Full Autonomous Mission Chain...');
        await evalJS(`document.getElementById('btnReset')?.click();`);
        await sleep(1000);

        await evalJS(`
          simSpeed = 8.0;
          document.getElementById('btnRunChain')?.click();
        `);
        console.log('[TEST 6] Mission chain started at 8x speed...');

        // Наблюдаем за этапом 1 (Разведка)
        await sleep(4000);
        const reconPhase = await evalJS(`({
          fsm: document.getElementById('fsmStatus')?.textContent,
          pipelineSubtext: document.getElementById('pipelineSubtext')?.textContent,
          targetsDiscovered: document.getElementById('targetsDiscoveredValue')?.textContent,
          slamBadge: document.getElementById('slamCoverageBadge')?.textContent
        })`);
        console.log('[TEST 6] Reconnaissance Progress (4s):', JSON.stringify(reconPhase));
        await takeScreenshot('scratch/test_stage4_recon_mission.png');

        // Ждем завершения разведки и перехода к обработке
        await sleep(6500);
        const execPhase = await evalJS(`({
          activeDrone: document.getElementById('activeDroneName')?.textContent,
          fsm: document.getElementById('fsmStatus')?.textContent,
          pipelineSubtext: document.getElementById('pipelineSubtext')?.textContent,
          targetsDiscovered: document.getElementById('targetsDiscoveredValue')?.textContent,
          slamBadge: document.getElementById('slamCoverageBadge')?.textContent
        })`);
        console.log('[TEST 6] Execution / Treatment Phase (10s):', JSON.stringify(execPhase));
        await takeScreenshot('scratch/test_stage5_execution_mission.png');

        // Ждем завершения обработки всех 6 целей и финальной посадки
        await sleep(9000);
        const finalPhase = await evalJS(`({
          activeDrone: document.getElementById('activeDroneName')?.textContent,
          fsm: document.getElementById('fsmStatus')?.textContent,
          pipelineSubtext: document.getElementById('pipelineSubtext')?.textContent,
          targetsDiscovered: document.getElementById('targetsDiscoveredValue')?.textContent,
          slamBadge: document.getElementById('slamCoverageBadge')?.textContent,
          treatedCount: targets.filter(t => t.treated).length,
          validTargets: targets.filter(t => t.type === 'A' && !t.insideNFZ).length
        })`);
        console.log('[TEST 6] Final Mission State:', JSON.stringify(finalPhase));
        testReport.fullMissionTest = finalPhase;
        await takeScreenshot('scratch/test_stage6_mission_finished.png');

        testReport.pageErrors = pageErrors;
        testReport.consoleLogs = consoleLogs;

        fs.writeFileSync('scratch/test_report.json', JSON.stringify(testReport, null, 2), 'utf-8');
        console.log('=== ALL TESTS COMPLETED. REPORT GENERATED ===');
        chrome.kill();
        process.exit(0);
      };
    });
  });
}, 1500);
