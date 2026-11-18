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

# Safety intersection check:
assert not route_line.intersects(b1), 'Intersection with NFZ-1!'
assert not route_line.intersects(b2), 'Intersection with NFZ-2!'

# Test 500 random seeds:
all_covered = True
for seed in range(500):
    random.seed(seed)
    targets = []
    # 2 inside NFZ
    targets.append({'id': 7, 'type': 'A_NFZ', 'x': 2.6 + random.uniform(-0.25, 0.25), 'y': 2.1 + random.uniform(-0.15, 0.15)})
    targets.append({'id': 8, 'type': 'A_NFZ', 'x': 4.4 + random.uniform(-0.15, 0.15), 'y': 1.4 + random.uniform(-0.15, 0.15)})
    
    # 6 valid A outside NFZ
    allowed_zones = [
        (0.8, 1.3, 0.5, 0.9),
        (2.0, 3.2, 0.35, 0.55),
        (0.8, 1.3, 3.2, 3.55),
        (2.0, 3.2, 3.2, 3.55),
        (4.0, 5.3, 3.2, 3.55),
        (5.3, 5.6, 2.0, 2.8)
    ]
    for i, z in enumerate(allowed_zones):
        targets.append({'id': i+1, 'type': 'A', 'x': random.uniform(z[0], z[1]), 'y': random.uniform(z[2], z[3])})
    
    # 1 B
    targets.append({'id': 9, 'type': 'B', 'x': random.uniform(0.65, 0.95), 'y': random.uniform(1.8, 2.5)})
    # 1 U
    targets.append({'id': 10, 'type': 'U', 'x': random.uniform(5.2, 5.6), 'y': random.uniform(0.6, 1.1)})

    for t in targets:
        p = Point(t['x'], t['y'])
        d = route_line.distance(p)
        max_allowed = 1.55 if t['id'] in (7, 8) else 0.85
        if d > max_allowed:
            print(f"Seed {seed}: Target {t['id']} too far: {d:.3f} m")
            all_covered = False
            break

if all_covered:
    print('ALL 500 RANDOM SEEDS: 10/10 TARGETS ARE FULLY DISCOVERED BY RECON DRONE!')
