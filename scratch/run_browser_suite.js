const { spawn } = require('child_process');
const http = require('http');

async function runBrowserTest(testName, setupExpression, waitMs) {
  return new Promise((resolve, reject) => {
    const port = 9245 + Math.floor(Math.random() * 100);
    const chrome = spawn('C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', [
      '--headless=new',
      `--remote-debugging-port=${port}`,
      '--disable-gpu',
      'http://localhost:8080/index.html'
    ]);

    setTimeout(() => {
      http.get(`http://localhost:${port}/json`, (res) => {
        let raw = '';
        res.on('data', chunk => raw += chunk);
        res.on('end', () => {
          let tabs;
          try {
            tabs = JSON.parse(raw);
          } catch(e) {
            chrome.kill();
            return reject(e);
          }
          const pageTab = tabs.find(t => t.type === 'page' && t.url.includes('localhost'));
          if (!pageTab) {
            chrome.kill();
            return reject(new Error('No page tab'));
          }

          const ws = new WebSocket(pageTab.webSocketDebuggerUrl);

          ws.onopen = () => {
            ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
            ws.send(JSON.stringify({
              id: 2,
              method: 'Runtime.evaluate',
              params: { expression: setupExpression }
            }));

            setTimeout(() => {
              ws.send(JSON.stringify({
                id: 3,
                method: 'Runtime.evaluate',
                params: {
                  expression: `(() => {
                    const d1 = drone1State;
                    const d2 = drone2State;
                    return JSON.stringify({
                      test: "${testName}",
                      slamCoverage: slamCoverage.toFixed(1) + "%",
                      slamWallsCount: slamWallsCount,
                      targetsDiscovered: d1.memory.length,
                      d1_fsm: d1.fsm,
                      d1_pos: { x: d1.x.toFixed(2), y: d1.y.toFixed(2), z: d1.z.toFixed(2) },
                      d2_fsm: d2.fsm,
                      d2_pos: { x: d2.x.toFixed(2), y: d2.y.toFixed(2), z: d2.z.toFixed(2) },
                      chainStage: chainStage,
                      chainRunning: chainRunning
                    });
                  })()`,
                  returnByValue: true
                }
              }));
            }, waitMs);
          };

          ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.id === 3) {
              const resVal = msg.result.result ? JSON.parse(msg.result.result.value) : null;
              chrome.kill();
              resolve(resVal);
            }
          };
        });
      }).on('error', err => {
        chrome.kill();
        reject(err);
      });
    }, 1200);
  });
}

async function main() {
  console.log('=== ЗАПУСК СЕРИИ ТЕСТОВ НА СИМУЛЯТОРЕ ===\n');

  // Тест 1: Разведка (Recon Only) - полный прогон с ускорением 8x
  console.log('Тест 1: Полный цикл разведки БПЛА-1 (старт -> облет -> SLAM -> посадка на Home-1)...');
  try {
    const res1 = await runBrowserTest(
      'Recon Cycle',
      'simSpeed = 8.0; document.getElementById("selectRecon").click(); document.getElementById("btnTakeoff").click(); setTimeout(() => { drone1State.autoPilot = true; drone1State.autoIdx = 0; }, 500);',
      12000 // 12s * 8x = 96s simulation time
    );
    console.log('Результат Теста 1:', res1);
  } catch (e) {
    console.error('Ошибка Теста 1:', e.message);
  }

  // Тест 2: Полная цепочка (Recon -> GCS -> Executor)
  console.log('\nТест 2: Автономная цепочка двух БПЛА (Разведка 10 целей -> Валидация GCS -> 6 обработок LED -> Возврат)...');
  try {
    const res2 = await runBrowserTest(
      'Full Two-Drone Chain',
      'simSpeed = 8.0; document.getElementById("btnRunChain").click();',
      28000 // 28s * 8x = 224s simulation time
    );
    console.log('Результат Теста 2:', res2);
  } catch (e) {
    console.error('Ошибка Теста 2:', e.message);
  }

  process.exit(0);
}

main();
