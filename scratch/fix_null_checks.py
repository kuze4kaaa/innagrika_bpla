with open('simulation_3d/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix btnToggleRoute
old_route = '''    const btnToggleRoute = document.getElementById('btnToggleRoute');
    btnToggleRoute.onclick = () => {'''

new_route = '''    const btnToggleRoute = document.getElementById('btnToggleRoute');
    if (btnToggleRoute) {
      btnToggleRoute.onclick = () => {'''

if old_route in text:
    text = text.replace(old_route, new_route, 1)
    # also add closing bracket for if
    idx = text.find(new_route)
    end_semi = text.find('};', idx + len(new_route))
    if end_semi != -1:
        text = text[:end_semi+2] + '\n    }' + text[end_semi+2:]

# Check if btnToggleMotors has null check
old_motors = '''    const btnToggleMotors = document.getElementById('btnToggleMotors');
    btnToggleMotors.onclick = () => {'''

new_motors = '''    const btnToggleMotors = document.getElementById('btnToggleMotors');
    if (btnToggleMotors) {
      btnToggleMotors.onclick = () => {'''

if old_motors in text:
    text = text.replace(old_motors, new_motors, 1)
    idx = text.find(new_motors)
    end_semi = text.find('};', idx + len(new_motors))
    if end_semi != -1:
        text = text[:end_semi+2] + '\n    }' + text[end_semi+2:]

with open('simulation_3d/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Null checks fixed!")
