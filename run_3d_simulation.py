"""
Скрипт запуска 3D-симуляции полигона и БПЛА (Иннагрика 2026 · Агротех АТ11-2)
Запускает локальный веб-сервер и автоматически открывает симуляцию в браузере.
"""

import argparse
import http.server
import socketserver
import webbrowser
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_PORT = 8080
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulation_3d")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        # Подавление избыточных логов запросов в терминале
        pass


class ReusableThreadingTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def parse_arguments():
    parser = argparse.ArgumentParser(description="Локальный запуск 3D-симулятора АТ11-2")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="порт веб-сервера")
    parser.add_argument("--no-browser", action="store_true", help="не открывать браузер автоматически")
    return parser.parse_args()

def main():
    args = parse_arguments()
    if not (1 <= args.port <= 65535):
        raise SystemExit("Порт должен находиться в диапазоне 1-65535")
    print("=" * 70)
    print("ЗАПУСК 3D-СИМУЛЯТОРА ПОЛИГОНА И БПЛА (ИННАГРИКА 2026 · АГРОТЕХ)")
    print("=" * 70)
    print(f"Директория симуляции: {DIRECTORY}")
    print(f"Локальный адрес: http://127.0.0.1:{args.port}")
    print("-" * 70)
    print("УПРАВЛЕНИЕ В СИМУЛЯЦИИ:")
    print("  • W / S — Полет вперед / назад (строго по курсу носа дрона)")
    print("  • A / D или Стрелки Влево/Вправо — Разворот носа (Рыскание / Yaw)")
    print("  • Z / C — Боковое смещение (крен / strafe влево-вправо)")
    print("  • Пробел / Shift (или Q / E) — Набор высоты / Снижение (ось Z)")
    print("  • L — Активация светодиодной нагрузки (БПЛА-2, коридор 1.0 - 1.4 м, 2.0 с)")
    print("  • Мышь (ЛКМ + перетаскивание) — Свободный 3D-облет камеры")
    print("  • Колесико мыши — Масштаб / Зум")
    print("  • Кнопки на экране — Взлет на 1.2 м, посадка, полная цепочка, выбор камер")
    print("=" * 70)
    if args.no_browser:
        print("Сервер запущен без открытия браузера. Для остановки нажмите Ctrl + C")
    else:
        print("Открываю браузер... Для остановки сервера нажмите Ctrl + C")
    print("=" * 70)

    url = f"http://127.0.0.1:{args.port}/index.html"
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Не удалось открыть браузер автоматически: {e}")
            print(f"Откройте вручную ссылку: {url}")

    with ReusableThreadingTCPServer(("127.0.0.1", args.port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nСервер 3D-симулятора остановлен.")

if __name__ == "__main__":
    main()
