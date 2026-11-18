with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

target = "setCameraMode('close');"
replacement = """setCamMode('orbit');
        document.querySelectorAll('.btn-cam-mini').forEach(b => b.classList.remove('active'));
        btnCamClose.classList.add('active');"""

if target in text:
    text = text.replace(target, replacement, 1)
    with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Fixed btnCamClose successfully!")
else:
    print("Target not found!")
