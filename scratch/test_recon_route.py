import math
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

print("Checking Recon Segments against NFZ barriers:")
collision = False
for i in range(len(recon_route)-1):
    seg = LineString([recon_route[i], recon_route[i+1]])
    if seg.intersects(b1):
        print(f"Seg {i}->{i+1}: intersects NFZ-1!")
        collision = True
    if seg.intersects(b2):
        print(f"Seg {i}->{i+1}: intersects NFZ-2!")
        collision = True

if not collision:
    print("ALL RECON SEGMENTS ARE 100% COLLISION FREE!")
