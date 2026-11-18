import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines[980:1020], 981):
    print(f'{i}: {line.rstrip()}')
