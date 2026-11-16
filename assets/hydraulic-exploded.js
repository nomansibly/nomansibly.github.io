import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

/*
 * Hydraulic rotational teaching rig — illustrative exploded assembly.
 * Geometry is constructed from primitives because the source SolidWorks
 * assembly is not present in the public portfolio repository.
 * It is NOT a dimensional reconstruction or tolerance model.
 */
const viewer = document.getElementById("viewer");
const loading = document.getElementById("loading");
const fallback = document.getElementById("fallback");
const slider = document.getElementById("explode-range");
const sliderOutput = document.getElementById("explode-value");
const resetButton = document.getElementById("reset-view");
const turntableButton = document.getElementById("turntable");
const partTitle = document.getElementById("part-title");
const partDescription = document.getElementById("part-description");
const partSpec = document.getElementById("part-spec");
const buttons = [...document.querySelectorAll("[data-part]")];
const partData = {
  guard: { title: "TRANSPARENT SAFETY GUARD", description: "Clear protective panels around the rotating upper assembly, represented here as separate transparent pieces.", spec: "Documented build: 3 mm Plexiglass + wire gauze." },
  gear: { title: "UPPER GEAR TRANSMISSION", description: "The upper rotating gear and smaller mating gear are separated to show a simplified transmission relationship.", spec: "Documented fabrication: S355 laser-cut gears; specified ±0.1 mm tolerance. Teeth shown are illustrative." },
  shaft: { title: "VERTICAL SHAFT & BEARING", description: "The upright shaft passes through a support bearing to the upper rotating platform. Axis and bearing locations are schematic.", spec: "A central vertical shaft and supported rotating assembly are visible in the project photographs." },
  drive: { title: "LOWER DRIVE & FLYWHEEL", description: "The lower power-transmission path and flywheel hub are shown separately from the frame for inspection.", spec: "Documented flywheel hub: 27 mm bore with weight plates." },
  frame: { title: "WELDED SUPPORT FRAME", description: "A rigid frame supports the upper rotating mechanism and lower drive components.", spec: "Documented construction: 40 × 40 × 3 mm RHS steel, MIG welded; diagram not to scale." },
  sensor: { title: "SENSORS & CONTROLLER", description: "Inductive RPM pickup and simplified control/instrumentation shapes show how the rig was monitored.", spec: "Documented equipment: inductive RPM sensor, pressure transducers and Parker IQAN MD4 with soft-start / E-stop." }
};
const movements = {
  frame: new THREE.Vector3(0, -0.23, 0),
  guard: new THREE.Vector3(0, 1.58, 0),
  gear: new THREE.Vector3(0.76, 0.28, -1.07),
  shaft: new THREE.Vector3(0, 1.02, 0.08),
  drive: new THREE.Vector3(1.28, -0.08, 0.63),
  sensor: new THREE.Vector3(1.45, 0.68, 0.85)
};
const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
let renderer, camera, controls, scene, sceneRoot, selected = null, outline = null;
let visible = true, running = false, turntable = false, desiredExplode = 0, currentExplode = 0;
let raycaster, frameClock, pointerStart = null, resizeObserver, intersectionObserver;
const partGroups = {};
const hitTargets = [];
const v3 = (x,y,z) => new THREE.Vector3(x,y,z);
const mats = {
  frame: new THREE.MeshStandardMaterial({color:0x3c4653,metalness:.72,roughness:.39}),
  platform: new THREE.MeshStandardMaterial({color:0x252e39,metalness:.64,roughness:.42}),
  steel: new THREE.MeshStandardMaterial({color:0x8896a3,metalness:.76,roughness:.25}),
  bearing: new THREE.MeshStandardMaterial({color:0x53616a,metalness:.55,roughness:.37}),
  gear: new THREE.MeshStandardMaterial({color:0xd1d7dc,metalness:.82,roughness:.26}),
  brass: new THREE.MeshStandardMaterial({color:0xc9a26a,metalness:.72,roughness:.27}),
  body: new THREE.MeshStandardMaterial({color:0x203241,metalness:.27,roughness:.56}),
  acrylic: new THREE.MeshPhysicalMaterial({color:0x7bc0d2,metalness:0,roughness:.11,transparent:true,opacity:.18,side:THREE.DoubleSide,depthWrite:false}),
  edge: new THREE.MeshStandardMaterial({color:0x8cb4c3,metalness:.65,roughness:.3}),
  accent: new THREE.MeshStandardMaterial({color:0xff728f,metalness:.32,roughness:.42}),
  sensor: new THREE.MeshStandardMaterial({color:0x58c6c9,metalness:.34,roughness:.4})
};
function addPart(id) {
  const group = new THREE.Group();
  group.name = id;
  partGroups[id] = group;
  sceneRoot.add(group);
  return group;
}
function mesh(parent, geometry, material, part, xyz, rotation) {
  const m = new THREE.Mesh(geometry, material);
  if(xyz) m.position.set(...xyz);
  if(rotation) m.rotation.set(...rotation);
  m.userData.part = part;
  parent.add(m);
  hitTargets.push(m);
  return m;
}
function box(parent, part, size, xyz, material, rotation) {
  return mesh(parent,new THREE.BoxGeometry(...size),material,part,xyz,rotation);
}
function cylinder(parent,part,radius,height,xyz,material,axis="y",segments=30) {
  const rot=axis==="x"?[0,0,Math.PI/2]:axis==="z"?[Math.PI/2,0,0]:undefined;
  return mesh(parent,new THREE.CylinderGeometry(radius,radius,height,segments),material,part,xyz,rot);
}
function beam(parent,part,start,end,size,material) {
  const a=v3(...start),b=v3(...end),direction=b.clone().sub(a);
  const piece=mesh(parent,new THREE.BoxGeometry(size,direction.length(),size),material,part);
  piece.position.copy(a).add(b).multiplyScalar(.5);
  piece.quaternion.setFromUnitVectors(v3(0,1,0),direction.normalize());
  return piece;
}
function gear(parent,part,x,y,z,radius,teeth,material) {
  const assembly=new THREE.Group();
  assembly.position.set(x,y,z);parent.add(assembly);
  const base=mesh(assembly,new THREE.CylinderGeometry(radius*.88,radius*.88,.13,48),material,part,[0,0,0]);
  cylinder(assembly,part,radius*.25,.19,[0,.02,0],mats.bearing);
  for(let i=0;i<teeth;i++){
    const a=i*2*Math.PI/teeth;
    box(assembly,part,[radius*.22,.12,radius*.15],[Math.cos(a)*radius*.91,0,Math.sin(a)*radius*.91],material,[0,-a,0]);
  }
  for(let j=0;j<6;j++){
    const a=j*Math.PI/3;
    cylinder(assembly,part,.055,.14,[Math.cos(a)*radius*.54,.025,Math.sin(a)*radius*.54],mats.bearing);
  }
  return base;
}
function buildFrame() {
  const g=addPart("frame");
  for(const z of [-1.18,1.18])box(g,"frame",[3.65,.13,.13],[0,.10,z],mats.frame);
  for(const x of [-1.77,1.77])box(g,"frame",[.13,.13,2.5],[x,.10,0],mats.frame);
  for(const x of [-1.64,1.64])for(const z of [-1.09,1.09]){
    box(g,"frame",[.13,1.88,.13],[x,1.1,z],mats.frame);
    box(g,"frame",[.22,.055,.22],[x,.025,z],mats.platform);
  }
  for(const z of [-1.06,1.06]){
    beam(g,"frame",[-1.65,.24,z],[.65,2.07,z],.115,mats.frame);
    beam(g,"frame",[1.65,.24,z],[.4,2.07,z],.11,mats.frame);
  }
  box(g,"frame",[3.42,.14,2.35],[0,2.07,0],mats.platform);
  for(const x of [-1.51,1.51])box(g,"frame",[.09,.04,2.2],[x,2.16,0],mats.steel);
  for(const z of [-.99,.99])box(g,"frame",[3.1,.035,.08],[0,2.16,z],mats.steel);
  box(g,"frame",[1.9,.055,1.08],[.0,.29,.31],mats.platform);
  return g;
}
function buildGuard() {
  const g=addPart("guard");
  for(const x of [-1.32,1.32]){
    box(g,"guard",[.036,1.08,2.06],[x,2.8,0],mats.acrylic);
    for(const z of [-1,1])box(g,"guard",[.037,1.1,.037],[x,2.8,z],mats.edge);
  }
  for(const z of [-1.01,1.01]){
    box(g,"guard",[2.64,1.09,.035],[0,2.8,z],mats.acrylic);
    for(const y of [2.25,3.35])box(g,"guard",[2.64,.035,.035],[0,y,z],mats.edge);
  }
  box(g,"guard",[2.67,.034,2.09],[0,3.36,0],mats.acrylic);
  for(const x of [-1.32,1.32])for(const y of [2.25,3.35])box(g,"guard",[.038,.038,2.04],[x,y,0],mats.edge);
  return g;
}
function buildGear() {
  const g=addPart("gear");
  gear(g,"gear",-.1,2.3,-.14,.67,40,mats.gear);
  gear(g,"gear",.82,2.3,-.14,.29,18,mats.brass);
  cylinder(g,"gear",.29,.065,[.82,2.39,-.14],mats.bearing);
  return g;
}
function buildShaft() {
  const g=addPart("shaft");
  cylinder(g,"shaft",.083,1.28,[-.1,2.76,-.14],mats.steel);
  cylinder(g,"shaft",.215,.18,[-.1,2.36,-.14],mats.bearing);
  cylinder(g,"shaft",.13,.10,[-.1,3.42,-.14],mats.brass);
  for(let j=0;j<4;j++){
    const angle=j*Math.PI/2;
    cylinder(g,"shaft",.025,.06,[-.1+.155*Math.cos(angle),2.44,-.14+.155*Math.sin(angle)],mats.steel);
  }
  return g;
}
function buildDrive() {
  const g=addPart("drive");
  cylinder(g,"drive",.10,3.46,[0,.55,.68],mats.steel,"x");
  for(const x of [-1.0,.95]) {
    box(g,"drive",[.25,.27,.33],[x,.32,.68],mats.bearing);
    cylinder(g,"drive",.23,.18,[x,.55,.68],mats.steel,"x");
  }
  cylinder(g,"drive",.36,.15,[-1.76,.55,.68],mats.gear,"x");
  cylinder(g,"drive",.17,.27,[-1.88,.55,.68],mats.bearing,"x");
  cylinder(g,"drive",.25,.85,[1.47,.55,.68],mats.body,"x");
  cylinder(g,"drive",.29,.07,[1.02,.55,.68],mats.brass,"x");
  for(let i=0;i<6;i++){
    const a=i*Math.PI/3;
    cylinder(g,"drive",.035,.22,[-1.77,.55+Math.cos(a)*.27,.68+Math.sin(a)*.27],mats.steel,"x",12);
  }
  return g;
}
function buildSensor() {
  const g=addPart("sensor");
  box(g,"sensor",[.42,.28,.42],[1.10,2.31,.70],mats.body);
  cylinder(g,"sensor",.065,.34,[.90,2.3,.70],mats.sensor,"x");
  box(g,"sensor",[.63,.37,.48],[1.37,.59,-.56],mats.body);
  box(g,"sensor",[.37,.16,.014],[1.37,.67,-.31],mats.sensor);
  for(let i=0;i<3;i++)box(g,"sensor",[.06,.038,.015],[1.22+i*.15,.50,-.30],i===0?mats.accent:mats.steel);
  cylinder(g,"sensor",.105,.18,[.80,.65,-.55],mats.bearing);
  cylinder(g,"sensor",.05,.22,[.80,.82,-.55],mats.brass);
  return g;
}
function setSelected(id) {
  selected=id in partData?id:null;
  buttons.forEach(button=>button.setAttribute("aria-pressed",String(button.dataset.part===selected)));
  if(outline){scene.remove(outline);outline.geometry.dispose();outline.material.dispose();outline=null}
  if(!selected){
    partTitle.textContent="SELECT A COMPONENT";
    partDescription.textContent="Choose a part in the list or click the model to see what it does.";
    partSpec.textContent="Real hardware references remain available below.";
  } else {
    const p=partData[selected];
    partTitle.textContent=p.title;partDescription.textContent=p.description;partSpec.textContent=p.spec;
    outline=new THREE.BoxHelper(partGroups[selected],0x72e9e4);
    outline.material.transparent=true;outline.material.opacity=.72;
    outline.material.depthTest=false;outline.renderOrder=15;
    scene.add(outline);
  }
}
function buildScene() {
  scene=new THREE.Scene();
  sceneRoot=new THREE.Group();
  scene.add(sceneRoot);
  scene.add(new THREE.HemisphereLight(0xc7e7f0,0x263548,2.0));
  const key=new THREE.DirectionalLight(0xfff5e8,3.1);key.position.set(4,8,7);scene.add(key);
  const rim=new THREE.DirectionalLight(0x69d8e2,2);rim.position.set(-4,4,-6);scene.add(rim);
  const rose=new THREE.DirectionalLight(0xe66e89,.8);rose.position.set(-3,2,5);scene.add(rose);
  const grid=new THREE.GridHelper(10,20,0x34788a,0x234255);grid.position.y=-.09;
  grid.material.transparent=true;grid.material.opacity=.27;scene.add(grid);
  const shadow=new THREE.Mesh(new THREE.CircleGeometry(2.55,48),new THREE.MeshBasicMaterial({color:0x000d16,transparent:true,opacity:.18,depthWrite:false}));
  shadow.rotation.x=-Math.PI/2;shadow.position.y=-.06;scene.add(shadow);
  buildFrame();buildGuard();buildGear();buildShaft();buildDrive();buildSensor();
}
function resize() {
  if(!renderer||!camera||!viewer)return;
  const w=Math.max(1,viewer.clientWidth),h=Math.max(1,viewer.clientHeight);
  renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();
}
function renderLoop() {
  if(!visible||document.hidden){running=false;return}
  const dt=Math.min(.05,frameClock.getDelta());
  const t=reduced?1:Math.min(1,dt*8.8);
  currentExplode=THREE.MathUtils.lerp(currentExplode,desiredExplode,t);
  for(const [name,group] of Object.entries(partGroups)){
    const target=movements[name].clone().multiplyScalar(currentExplode);
    group.position.lerp(target,t);
  }
  if(outline)outline.update();
  controls.autoRotate=turntable&&!reduced;
  controls.update();
  renderer.render(scene,camera);
  requestAnimationFrame(renderLoop);
}
function ensureLoop() {
  if(running||!visible||document.hidden||!renderer)return;
  running=true;frameClock.getDelta();requestAnimationFrame(renderLoop);
}
function onPick(event) {
  if(!raycaster||!renderer)return;
  const r=renderer.domElement.getBoundingClientRect();
  const pointer=new THREE.Vector2(((event.clientX-r.left)/r.width)*2-1,-((event.clientY-r.top)/r.height)*2+1);
  raycaster.setFromCamera(pointer,camera);
  const hit=raycaster.intersectObjects(hitTargets,false).find(x=>x.object.userData.part);
  if(hit)setSelected(hit.object.userData.part);
}
function showFallback(error) {
  console.warn("Hydraulic exploded model is unavailable:",error);
  if(loading){loading.hidden=true;loading.style.display="none"}
  if(fallback){fallback.hidden=false;fallback.style.display="flex"}
}
function main() {
  try{
    renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:"high-performance"});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.8));
    renderer.outputColorSpace=THREE.SRGBColorSpace;
    renderer.toneMapping=THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure=1.12;
    renderer.setClearColor(0x000000,0);
    renderer.domElement.setAttribute("aria-label","Rotatable 3D schematic of hydraulic rotational test bench");
    renderer.domElement.setAttribute("role","img");
    viewer.insertBefore(renderer.domElement,loading);
    camera=new THREE.PerspectiveCamera(43,1,.1,75);
    camera.position.set(6.1,4.25,6.6);
    controls=new OrbitControls(camera,renderer.domElement);
    controls.target.set(0,1.63,0);
    controls.enableDamping=!reduced;
    controls.dampingFactor=.065;
    controls.minDistance=3.7;controls.maxDistance=12.5;
    controls.minPolarAngle=.19;controls.maxPolarAngle=Math.PI/2+.19;
    controls.enablePan=false;controls.autoRotateSpeed=.7;
    controls.update();
    buildScene();raycaster=new THREE.Raycaster();frameClock=new THREE.Clock();
    resize();
    loading.hidden=true;loading.style.display="none";
    window.__hydraulic3dReady=true;
    buttons.forEach(button=>button.addEventListener("click",()=>setSelected(button.dataset.part)));
    slider.addEventListener("input",()=>{
      desiredExplode=Number(slider.value)/100;
      sliderOutput.textContent=slider.value+"%";
      if(reduced){currentExplode=desiredExplode;for(const [name,group] of Object.entries(partGroups)){group.position.copy(movements[name]).multiplyScalar(desiredExplode)}}
      ensureLoop();
    });
    resetButton.addEventListener("click",()=>{
      slider.value="0";sliderOutput.textContent="0%";desiredExplode=0;
      camera.position.set(6.1,4.25,6.6);controls.target.set(0,1.63,0);
      turntable=false;turntableButton.setAttribute("aria-pressed","false");
      turntableButton.textContent="▶ TURNTABLE";setSelected(null);controls.update();ensureLoop();
    });
    turntableButton.addEventListener("click",()=>{
      turntable=!turntable;
      turntableButton.setAttribute("aria-pressed",String(turntable));
      turntableButton.textContent=turntable?"■ STOP ROTATION":"▶ TURNTABLE";
      ensureLoop();
    });
    if(reduced){turntableButton.disabled=true;turntableButton.title="Animation disabled by reduced-motion preference"}
    renderer.domElement.addEventListener("pointerdown",(e)=>{pointerStart={x:e.clientX,y:e.clientY}});
    renderer.domElement.addEventListener("pointerup",(e)=>{
      if(!pointerStart)return;
      const diff=Math.hypot(e.clientX-pointerStart.x,e.clientY-pointerStart.y);
      pointerStart=null;if(diff<6)onPick(e);
    });
    renderer.domElement.addEventListener("pointercancel",()=>{pointerStart=null});
    if(window.ResizeObserver){resizeObserver=new ResizeObserver(resize);resizeObserver.observe(viewer)}
    else window.addEventListener("resize",resize);
    if(window.IntersectionObserver){
      intersectionObserver=new IntersectionObserver(entries=>{visible=entries.some(entry=>entry.isIntersecting);ensureLoop()},{threshold:0});
      intersectionObserver.observe(viewer);
    }
    document.addEventListener("visibilitychange",()=>{if(!document.hidden)ensureLoop()});
    setSelected(null);ensureLoop();
  }catch(error){showFallback(error)}
}
main();
