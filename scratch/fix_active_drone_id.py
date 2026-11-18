file_path = 'simulation_3d/index.html'

with open(file_path, 'rb') as f:
    content = f.read().decode('utf-8')

has_crlf = '\r\n' in content
c_lf = content.replace('\r\n', '\n')

old_top = """    let simSpeed = 1.0;
// (chainRunning & chainStage hoisted to top)"""

new_top = """    let simSpeed = 1.0;
    let chainRunning = false;
    let chainStage = 0;
    let activeDroneId = 1;"""

assert old_top in c_lf, "old_top not found"
c_lf = c_lf.replace(old_top, new_top)

# 2. Add activeDroneId = droneNum to setActiveDrone
old_set_active = """function setActiveDrone(droneNum) {
      if (droneNum === 1) {"""

new_set_active = """function setActiveDrone(droneNum) {
      activeDroneId = droneNum;
      if (droneNum === 1) {"""

assert old_set_active in c_lf, "old_set_active not found"
c_lf = c_lf.replace(old_set_active, new_set_active)

# 3. Guard route update inside generateRandomTargets
old_gen_route = """          if (activeDroneId === 1 && routeVisible) updateRouteLine(drone1State.waypoints);"""
new_gen_route = """          if (typeof activeDroneId !== 'undefined' && activeDroneId === 1 && typeof routeVisible !== 'undefined' && routeVisible && typeof updateRouteLine === 'function') updateRouteLine(drone1State.waypoints);"""

assert old_gen_route in c_lf, "old_gen_route not found"
c_lf = c_lf.replace(old_gen_route, new_gen_route)

output = c_lf.replace('\n', '\r\n') if has_crlf else c_lf
with open(file_path, 'wb') as f:
    f.write(output.encode('utf-8'))

print("activeDroneId defined and guarded successfully!")
