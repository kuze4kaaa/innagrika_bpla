const fs = require('fs');
const code = fs.readFileSync('scratch/three.min.js', 'utf8');
const root = {};
new Function('self', code).call(root, root);
const THREE = root.THREE;

const g = new THREE.Group();
g.rotation.order = 'ZYX';
console.log('Initial order:', g.rotation.order);
g.rotation.set(0, 0, 0);
console.log('Order after set(0, 0, 0):', g.rotation.order);

g.rotation.z = Math.PI / 2;
g.rotation.y = 0.3;
g.rotation.x = 0;
console.log('Euler is:', g.rotation.x, g.rotation.y, g.rotation.z, g.rotation.order);

const vNose = new THREE.Vector3(1, 0, 0);
vNose.applyEuler(g.rotation);
console.log('vNose after applyEuler:', vNose);

const vUp = new THREE.Vector3(0, 0, 1);
vUp.applyEuler(g.rotation);
console.log('vUp after applyEuler:', vUp);
