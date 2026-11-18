import random
from shapely.geometry import box, Point

# NFZ-1: [1.67, 3.53] x [1.27, 2.93]
# NFZ-2: [3.67, 5.13] x [0.57, 2.03]
b1 = box(1.67, 1.27, 3.53, 2.93)
b2 = box(3.67, 0.57, 5.13, 2.03)

def gen_targets(seed=None):
    if seed: random.seed(seed)
    targets = []
    # 2 inside NFZ
    targets.append({'id': 7, 'type': 'A_NFZ', 'name': 'Цель A-NFZ1 (В запрете!)', 'x': round(2.6 + random.uniform(-0.25, 0.25), 2), 'y': round(2.1 + random.uniform(-0.15, 0.15), 2), 'nfz': True})
    targets.append({'id': 8, 'type': 'A_NFZ', 'name': 'Цель A-NFZ2 (В запрете!)', 'x': round(4.4 + random.uniform(-0.15, 0.15), 2), 'y': round(1.3 + random.uniform(-0.15, 0.15), 2), 'nfz': True})
    
    # 6 valid A outside NFZ
    allowed_zones = [
        (0.8, 1.3, 0.6, 1.0),
        (2.0, 3.2, 0.35, 0.55),
        (0.8, 1.3, 3.2, 3.55),
        (2.0, 3.2, 3.2, 3.55),
        (4.0, 5.3, 3.2, 3.55),
        (5.3, 5.6, 2.2, 2.8)
    ]
    for i, z in enumerate(allowed_zones):
        x = random.uniform(z[0], z[1])
        y = random.uniform(z[2], z[3])
        targets.append({'id': i+1, 'type': 'A', 'name': f'Цель A-{i+1}', 'x': round(x, 2), 'y': round(y, 2), 'nfz': False})
    
    # 1 B (healthy)
    targets.append({'id': 9, 'type': 'B', 'name': 'Участок B (Здорово)', 'x': round(random.uniform(0.7, 1.2), 2), 'y': round(random.uniform(1.8, 2.4), 2), 'nfz': False})
    # 1 U (uncertain)
    targets.append({'id': 10, 'type': 'U', 'name': 'Участок U (Неопределено)', 'x': round(random.uniform(5.2, 5.6), 2), 'y': round(random.uniform(0.7, 1.1), 2), 'nfz': False})
    return targets

t = gen_targets(42)
for item in t:
    p = Point(item['x'], item['y'])
    in_nfz = b1.contains(p) or b2.contains(p)
    print(f"Target {item['id']} ({item['type']}): ({item['x']}, {item['y']}), inside NFZ: {in_nfz}")
