file_path = 'simulation_3d/index.html'

with open(file_path, 'rb') as f:
    content = f.read().decode('utf-8')

has_crlf = '\r\n' in content
c_lf = content.replace('\r\n', '\n')

# 1. Add chainRunning and chainStage to top variables
old_top = """    let simSpeed = 1.0;"""
new_top = """    let simSpeed = 1.0;
    let chainRunning = false;
    let chainStage = 0;"""

assert old_top in c_lf, "old_top not found"
c_lf = c_lf.replace(old_top, new_top, 1)

# 2. Remove duplicate declarations lower down
old_lower_decl = """    let chainRunning = false;
    let chainStage = 0;"""

assert old_lower_decl in c_lf, "old_lower_decl not found"
c_lf = c_lf.replace(old_lower_decl, "// (chainRunning & chainStage hoisted to top)")

# 3. Guard renderSlamMap drone2State access
old_rsm_guard = """      if (chainStage >= 2 && drone2State.waypoints && drone2State.waypoints.length > 1) {"""
new_rsm_guard = """      if (chainStage >= 2 && typeof drone2State !== 'undefined' && drone2State && drone2State.waypoints && drone2State.waypoints.length > 1) {"""

assert old_rsm_guard in c_lf, "old_rsm_guard not found"
c_lf = c_lf.replace(old_rsm_guard, new_rsm_guard)

output = c_lf.replace('\n', '\r\n') if has_crlf else c_lf
with open(file_path, 'wb') as f:
    f.write(output.encode('utf-8'))

print("Hoisting and global guards fixed successfully!")
