import * as THREE from 'three';
import { Agent3Assets as A } from './assets3d';

export const colors = { mint: '#8dce9c', coral: '#db8c72', blue: '#78b9d4', gold: '#e6bd68', violet: '#b59acb', white: '#dce2d6' };

export function createRobot(avatar = 'mint', player = false) {
  const g = new THREE.Group();
  const mat = A.mat(colors[avatar] || colors.mint);
  const dark = A.mat('#293b37');
  const mesh = (geo, material, x, y, z) => { const m = new THREE.Mesh(geo, material); m.position.set(x,y,z); g.add(m); return m; };
  mesh(new THREE.BoxGeometry(.86,.72,.55),mat,0,1.02,0);
  mesh(new THREE.BoxGeometry(1.13,.85,.77),mat,0,1.87,0);
  mesh(new THREE.BoxGeometry(.92,.51,.04),dark,0,1.88,.40);
  const eye = new THREE.MeshBasicMaterial({color:player?'#b4ffa0':'#d5ffe6'});
  [-1,1].forEach(s=>mesh(new THREE.BoxGeometry(.17,.12,.04),eye,s*.23,1.91,.43));
  mesh(new THREE.BoxGeometry(.24,.05,.04),eye,0,1.7,.43);
  mesh(new THREE.CylinderGeometry(.04,.04,.30,6),dark,0,2.43,0);
  mesh(new THREE.SphereGeometry(.10,8,6),eye,0,2.60,0);
  const legs = [-1,1].map(s=>mesh(new THREE.BoxGeometry(.26,.44,.37),dark,s*.24,.43,0));
  const arms = [-1,1].map(s=>mesh(new THREE.BoxGeometry(.22,.6,.29),mat,s*.6,1.03,0));
  mesh(new THREE.BoxGeometry(.27,.12,.04),eye,0,1.14,.29);
  const ring = mesh(new THREE.RingGeometry(.74,.81,40),new THREE.MeshBasicMaterial({color:player?'#d4ffab':colors[avatar],transparent:true,opacity:.7,side:THREE.DoubleSide}),0,.15,0);
  ring.rotation.x=-Math.PI/2;
  g.userData={legs,arms,ring};
  return A.withShadow(g);
}

export function addLamp(scene,x,z) {
  const g=new THREE.Group(); g.position.set(x,.4,z);
  const pole=new THREE.Mesh(new THREE.CylinderGeometry(.065,.10,3.5,8),A.mat('#48524b'));pole.position.y=1.75;g.add(pole);
  const glass=new THREE.Mesh(new THREE.BoxGeometry(.36,.50,.36),new THREE.MeshBasicMaterial({color:'#fff0b6'}));glass.position.y=3.5;g.add(glass);
  const cap=new THREE.Mesh(new THREE.ConeGeometry(.35,.25,4),A.mat('#37413a'));cap.position.y=3.87;cap.rotation.y=Math.PI/4;g.add(cap);
  scene.add(A.withShadow(g));
}