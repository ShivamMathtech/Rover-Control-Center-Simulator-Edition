import {useState} from 'react';
import {Telemetry,Waypoint} from '../types';
export function MapPanel({data,points=[],onAdd}:{data:Telemetry;points?:Waypoint[];onAdd?:(p:Waypoint)=>void}){
 const [zoom,setZoom]=useState(1);const radius=data.settings.fence_radius;const scale=250/radius*zoom;
 const xy=(x:number,y:number)=>`${300+x*scale},${300-y*scale}`;
 return <section className="panel map"><div className="panelhead"><h3>Local navigation map</h3><span>METRES FROM HOME · OFFLINE</span><button onClick={()=>setZoom(Math.min(3,zoom+0.25))} aria-label="Zoom in">+</button><button onClick={()=>setZoom(Math.max(.5,zoom-.25))} aria-label="Zoom out">−</button><button onClick={()=>setZoom(1)}>Reset</button></div>
 <svg viewBox="0 0 600 600" role="img" aria-label="Rover position and mission waypoints" onClick={e=>{if(onAdd){const r=e.currentTarget.getBoundingClientRect();const ratio=Math.min(r.width,r.height)/600;const left=r.left+(r.width-600*ratio)/2;const top=r.top+(r.height-600*ratio)/2;onAdd({x:Math.round(((e.clientX-left)/ratio-300)/scale*10)/10,y:Math.round((300-(e.clientY-top)/ratio)/scale*10)/10,wait:0})}}}>
 <defs><pattern id="grid" width={10*scale} height={10*scale} patternUnits="userSpaceOnUse"><path d={`M ${10*scale} 0 L 0 0 0 ${10*scale}`} fill="none" stroke="#233342" strokeWidth=".7"/></pattern></defs><rect width="600" height="600" fill="url(#grid)"/>
 <circle cx="300" cy="300" r={radius*scale} fill="#2c82aa08" stroke="#3d7896" strokeDasharray="6 5"/><line x1="300" y1="0" x2="300" y2="600" stroke="#304453"/><line x1="0" y1="300" x2="600" y2="300" stroke="#304453"/>
 <text x="309" y="24" fill="#7295a9">N ↑</text><text x="310" y="319" fill="#9db3c2">HOME</text><circle cx="300" cy="300" r="4" fill="#99bdc9"/>
 <polyline points={data.trail.map(p=>xy(p[0],p[1])).join(' ')} stroke="#45c5ac" strokeWidth="2" fill="none"/>
 <polyline points={points.map(p=>xy(p.x,p.y)).join(' ')} stroke="#5bafff" strokeWidth="2" strokeDasharray="6 4" fill="none"/>
 {points.map((p,i)=><g key={i}><circle cx={300+p.x*scale} cy={300-p.y*scale} r="9" fill="#224a75" stroke="#78baff"/><text x={300+p.x*scale} y={304-p.y*scale} textAnchor="middle" fill="white" fontSize="10">{i+1}</text></g>)}
 <g transform={`translate(${300+data.position.x*scale},${300-data.position.y*scale}) rotate(${data.position.heading})`}><circle r="22" fill="#4cbbff18"/><path d="M0 -15 L10 12 L0 7 L-10 12Z" fill="#77cdff" stroke="#d2efff"/></g>
 </svg><div className="mapfoot"><span>X {data.position.x.toFixed(2)} m / Y {data.position.y.toFixed(2)} m</span><span>Fence {radius} m · grid 10 m</span></div>{onAdd&&<small>Click the map to add a waypoint. All routes remain inside the geofence.</small>}</section>
}
