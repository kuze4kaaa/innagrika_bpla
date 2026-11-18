with open('simulation_3d/index.html', 'rb') as f:
    data = f.read()

bad = 'if (badge) badge.textContent = ПОКРЫТИЕ: %;'.encode('utf-8')
good = 'if (badge) badge.textContent = `ПОКРЫТИЕ: ${slamCoverage.toFixed(1)}%`;'.encode('utf-8')

assert bad in data, 'bad not found'
data = data.replace(bad, good, 1)

with open('simulation_3d/index.html', 'wb') as f:
    f.write(data)

print('SUCCESS!')
