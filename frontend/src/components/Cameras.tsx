import {useEffect,useRef} from 'react';
import {Telemetry} from '../types';
function Camera({name,data}:{name:string;data:Telemetry}){
 const canvas=useRef<HTMLCanvasElement>(null);
 useEffect(()=>{const c=canvas.current;if(!c)return;const g=c.getContext('2d');if(!g)return;
 const w=c.width,h=c.height;g.fillStyle='#121e28';g.fillRect(0,0,w,h);
 if(data.faults.camera){g.fillStyle='#f2b968';g.font='20px monospace';g.fillText('CAMERA OFFLINE',30,120);return}
 const sky=g.createLinearGradient(0,0,0,h);sky.addColorStop(0,'#21384b');sky.addColorStop(.49,'#294253');sky.addColorStop(.5,'#202f35');sky.addColorStop(1,'#0f1d25');g.fillStyle=sky;g.fillRect(0,0,w,h);
 g.strokeStyle='#48707d';for(let i=-8;i<9;i++){g.beginPath();g.moveTo(w/2+i*13,110);g.lineTo(w/2+i*100,h);g.stroke()}
 const offset=(data.position.distance*30)%30;for(let y=120;y<h;y+=30){g.beginPath();g.moveTo(0,y+offset);g.lineTo(w,y+offset);g.stroke()}
 g.strokeStyle='#5dbdd9';g.strokeRect(w/2-12,h/2-12,24,24);g.fillStyle='#a9d1df';g.font='12px monospace';g.fillText('SYNTHETIC SCENE / NO VIDEO SOURCE',14,24);g.fillText(`${new Date(data.timestamp*1000).toLocaleTimeString()} | HDG ${data.position.heading.toFixed(0)}°`,14,h-16);
 if(data.faults.obstacle){g.strokeStyle='#ffbe66';g.strokeRect(165,110,100,90);g.fillStyle='#ffbe66';g.fillText('SIM OBSTACLE',165,105)}
 },[data,name]);
 function snapshot(){const a=document.createElement('a');a.download=`sim-${name}-${Date.now()}.png`;a.href=canvas.current!.toDataURL();a.click()}
 return <article className="camera"><header><strong>{name.toUpperCase()}</strong><span>{data.faults.camera?'OFFLINE':'SIMULATED'}</span></header><canvas ref={canvas} width="480" height="260"/><footer><small>Canvas test scene · 480×260</small><button onClick={snapshot} disabled={data.faults.camera}>Snapshot</button><button onClick={()=>canvas.current?.requestFullscreen()}>⛶</button></footer></article>
}
export function Cameras({data}:{data:Telemetry}){return <div className="camera-grid">{['front','rear','left','right'].map(name=><Camera key={name} name={name} data={data}/>)}</div>}
