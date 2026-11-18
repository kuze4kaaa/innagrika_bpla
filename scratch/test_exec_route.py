from shapely.geometry import box, LineString, Point

b1 = box(1.67, 1.27, 3.53, 2.93)
b2 = box(3.67, 0.67, 5.13, 2.13)

# Sample generated targets for test
t1 = (1.10, 0.75)
t2 = (2.60, 0.45)
t6 = (5.48, 2.40)
t5 = (4.20, 3.48)
t4 = (2.60, 3.48)
t3 = (1.10, 3.48)

exec_route = [
    (0.40, 1.20),
    t1,
    t2,
    (4.40, 0.38),
    (5.48, 0.38),
    t6,
    (5.48, 3.48),
    t5,
    t4,
    t3,
    (0.70, 2.50),
    (0.70, 1.40),
    (0.40, 1.20)
]

print("Checking Executor route collision against NFZ barriers:")
collision = False
for i in range(len(exec_route)-1):
    seg = LineString([exec_route[i], exec_route[i+1]])
    if seg.intersects(b1):
        print(f"Exec segment {i}->{i+1}: {exec_route[i]} -> {exec_route[i+1]} INTERSECTS NFZ-1!")
        collision = True
    if seg.intersects(b2):
        print(f"Exec segment {i}->{i+1}: {exec_route[i]} -> {exec_route[i+1]} INTERSECTS NFZ-2!")
        collision = True

if not collision:
    print("EXECUTOR ROUTE IS 100% COLLISION FREE!")

min_d1 = min(b1.distance(LineString([exec_route[i], exec_route[i+1]])) for i in range(len(exec_route)-1))
min_d2 = min(b2.distance(LineString([exec_route[i], exec_route[i+1]])) for i in range(len(exec_route)-1))
print(f"Clearance to NFZ-1 buffer: {min_d1:.3f} m")
print(f"Clearance to NFZ-2 buffer: {min_d2:.3f} m")
