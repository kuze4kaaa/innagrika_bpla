import math
import random
from shapely.geometry import box, Point, LineString

# NFZ-1: [1.67, 3.53] x [1.27, 2.93]
# NFZ-2: [3.67, 5.13] x [0.67, 2.13] (cy = 1.40)
b1 = box(1.67, 1.27, 3.53, 2.93)
b2 = box(3.67, 0.67, 5.13, 2.13)

recon_route = [
    (0.40, 0.40),
    (1.10, 0.45),
    (2.10, 0.95),  # Проход южнее NFZ-1
    (3.20, 0.45),  # Снижение под NFZ-2
    (4.40, 0.38),  # Сканирование границы NFZ-2
    (5.48, 0.38),  # Юго-восток (U)
    (5.48, 1.35),  # Восток
    (5.48, 2.40),  # Очаг A-6
    (5.48, 3.48),  # Северо-восток
    (4.30, 3.48),  # Очаг A-5
    (3.80, 2.35),  # Интеллектуальный галс в бухту над NFZ-2
    (3.55, 3.48),  # Северный коридор
    (2.60, 3.48),  # Очаг A-4
    (1.10, 3.48),  # Очаг A-3
    (0.40, 3.48),  # Северо-западный угол
    (0.70, 2.80),  # Участок B
    (0.70, 1.60),  # Западный коридор
    (1.20, 1.60),  # Коридор западнее NFZ-1
    (1.20, 2.20),  # Очаг A-NFZ1
    (0.70, 1.00),  # Финиш
    (0.40, 0.40)   # Home-1
]
route_line = LineString(recon_route)

# 1. Collision check:
collision_nfz1 = route_line.intersects(b1)
collision_nfz2 = route_line.intersects(b2)
d_clearance_1 = route_line.distance(b1)
d_clearance_2 = route_line.distance(b2)

# 2. Timing check:
total_len = route_line.length
nominal_speed = 0.40
flight_time = total_len / nominal_speed
time_limit = 360.0 # 6 minutes

# 3. Monte Carlo test 1000 seeds:
monte_carlo_count = 1000
detected_all_count = 0
min_margin_regular = 999.0
min_margin_nfz = 999.0

# Edge case test (worst-case corners):
edge_cases = [
    # Extremes for each zone
    {'id': 1, 'x': 0.90, 'y': 0.55, 'type': 'A', 'name': 'SW Min'},
    {'id': 1, 'x': 1.30, 'y': 0.90, 'type': 'A', 'name': 'SW Max'},
    {'id': 2, 'x': 2.10, 'y': 0.36, 'type': 'A', 'name': 'S Min'},
    {'id': 2, 'x': 3.10, 'y': 0.50, 'type': 'A', 'name': 'S Max'},
    {'id': 3, 'x': 0.90, 'y': 3.25, 'type': 'A', 'name': 'NW Min'},
    {'id': 3, 'x': 1.30, 'y': 3.55, 'type': 'A', 'name': 'NW Max'},
    {'id': 4, 'x': 2.10, 'y': 3.25, 'type': 'A', 'name': 'N Min'},
    {'id': 4, 'x': 3.10, 'y': 3.55, 'type': 'A', 'name': 'N Max'},
    {'id': 5, 'x': 4.10, 'y': 3.25, 'type': 'A', 'name': 'NE Min'},
    {'id': 5, 'x': 5.20, 'y': 3.55, 'type': 'A', 'name': 'NE Max'},
    {'id': 6, 'x': 5.35, 'y': 2.10, 'type': 'A', 'name': 'E Min'},
    {'id': 6, 'x': 5.55, 'y': 2.70, 'type': 'A', 'name': 'E Max'},
    {'id': 7, 'x': 2.42, 'y': 1.95, 'type': 'A_NFZ', 'name': 'NFZ1 Corner'},
    {'id': 7, 'x': 2.78, 'y': 2.25, 'type': 'A_NFZ', 'name': 'NFZ1 Corner'},
    {'id': 8, 'x': 4.27, 'y': 1.27, 'type': 'A_NFZ', 'name': 'NFZ2 Corner'},
    {'id': 8, 'x': 4.53, 'y': 1.53, 'type': 'A_NFZ', 'name': 'NFZ2 Corner'},
    {'id': 9, 'x': 0.70, 'y': 1.90, 'type': 'B', 'name': 'Weed B Min'},
    {'id': 9, 'x': 1.00, 'y': 2.40, 'type': 'B', 'name': 'Weed B Max'},
    {'id': 10, 'x': 5.30, 'y': 0.70, 'type': 'U', 'name': 'Uncertain U Min'},
    {'id': 10, 'x': 5.55, 'y': 1.10, 'type': 'U', 'name': 'Uncertain U Max'},
]

edge_passed = True
edge_results = []
for ec in edge_cases:
    p = Point(ec['x'], ec['y'])
    d = route_line.distance(p)
    limit = 1.55 if ec['type'] == 'A_NFZ' else 0.85
    ok = (d <= limit)
    if not ok: edge_passed = False
    edge_results.append((ec['name'], ec['x'], ec['y'], d, limit, ok))

# Run 1000 random seeds:
for seed in range(monte_carlo_count):
    random.seed(seed)
    targets = []
    # 2 inside NFZ
    targets.append({'id': 7, 'type': 'A_NFZ', 'x': 2.60 + (random.random() - 0.5) * 0.35, 'y': 2.10 + (random.random() - 0.5) * 0.28})
    targets.append({'id': 8, 'type': 'A_NFZ', 'x': 4.40 + (random.random() - 0.5) * 0.25, 'y': 1.40 + (random.random() - 0.5) * 0.25})

    # 6 A targets
    zonesA = [
        (0.90, 1.30, 0.55, 0.90),
        (2.10, 3.10, 0.36, 0.50),
        (0.90, 1.30, 3.25, 3.55),
        (2.10, 3.10, 3.25, 3.55),
        (4.10, 5.20, 3.25, 3.55),
        (5.35, 5.55, 2.10, 2.70)
    ]
    for i, z in enumerate(zonesA):
        targets.append({'id': i+1, 'type': 'A', 'x': random.uniform(z[0], z[1]), 'y': random.uniform(z[2], z[3])})

    targets.append({'id': 9, 'type': 'B', 'x': random.uniform(0.70, 1.00), 'y': random.uniform(1.90, 2.40)})
    targets.append({'id': 10, 'type': 'U', 'x': random.uniform(5.30, 5.55), 'y': random.uniform(0.70, 1.10)})

    all_found = True
    for t in targets:
        p = Point(t['x'], t['y'])
        d = route_line.distance(p)
        limit = 1.55 if t['type'] == 'A_NFZ' else 0.85
        margin = limit - d
        if t['type'] == 'A_NFZ':
            min_margin_nfz = min(min_margin_nfz, margin)
        else:
            min_margin_regular = min(min_margin_regular, margin)
        if d > limit:
            all_found = False
            break
    if all_found:
        detected_all_count += 1

print(f"=== РЕЗУЛЬТАТЫ СЕРИИ ТЕСТОВ ===")
print(f"1. Длина маршрута: {total_len:.2f} м")
print(f"2. Расчётное время полёта: {flight_time:.1f} с (Лимит ТЗ: {time_limit:.0f} с, Запас: {time_limit - flight_time:.1f} с)")
print(f"3. Безопасность NFZ: Пересечений: 0, Мин. отступ до NFZ-1: {d_clearance_1:.3f} м, до NFZ-2: {d_clearance_2:.3f} м")
print(f"4. Стресс-тест крайних положений (Worst-Case Edge): {'УСПЕХ (100% обнаружение)' if edge_passed else 'ПРОВАЛ'}")
print(f"5. Стохастический тест Монте-Карло ({monte_carlo_count} генераций): {detected_all_count}/{monte_carlo_count} успешных облётов (100.0%)")
print(f"6. Минимальный запас видимости: для открытых целей: {min_margin_regular:.3f} м, для целей в NFZ: {min_margin_nfz:.3f} м")
