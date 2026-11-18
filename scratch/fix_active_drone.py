with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_set_active = """        btnSelectRecon.className = 'btn-seg active-recon';
        btnSelectExec.className = 'btn-seg';
        document.getElementById('activeDroneName').textContent = '-1 ()';
        document.getElementById('activeDroneName').style.color = '#fdba74';
        const slamCard = document.getElementById('slamMapCard');
        if (slamCard) slamCard.style.display = 'block';
      } else {
        activeDrone = drone2State;
        activeDroneObj = drone2Obj;
        btnSelectRecon.className = 'btn-seg';
        btnSelectExec.className = 'btn-seg active-exec';
        document.getElementById('activeDroneName').textContent = '-2 ()';
        document.getElementById('activeDroneName').style.color = '#86efac';"""

new_set_active = """        btnSelectRecon.className = 'btn-seg active-recon';
        btnSelectExec.className = 'btn-seg';
        document.getElementById('activeDroneName').textContent = 'БПЛА-1 (Разведчик)';
        document.getElementById('activeDroneName').style.color = '#fdba74';
      } else {
        activeDrone = drone2State;
        activeDroneObj = drone2Obj;
        btnSelectRecon.className = 'btn-seg';
        btnSelectExec.className = 'btn-seg active-exec';
        document.getElementById('activeDroneName').textContent = 'БПЛА-2 (Исполнитель)';
        document.getElementById('activeDroneName').style.color = '#86efac';"""

if old_set_active in text:
    text = text.replace(old_set_active, new_set_active, 1)
    print("Fixed setActiveDrone strings and removed auto-opening SLAM card!")
else:
    # try flexible replace
    import re
    text = re.sub(
        r"btnSelectRecon\.className\s*=\s*'btn-seg active-recon';.*?document\.getElementById\('activeDroneName'\)\.style\.color\s*=\s*'#86efac';",
        new_set_active,
        text,
        flags=re.DOTALL
    )
    print("Replaced with regex!")

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)
