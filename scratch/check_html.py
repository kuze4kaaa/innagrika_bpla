import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx1 = text.find('<div class="topbar">')
idx2 = text.find('<!-- 2D SLAM Minimap -->')
print(text[idx1:idx2])
