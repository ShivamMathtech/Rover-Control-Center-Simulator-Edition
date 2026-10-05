export async function api<T=any>(path:string,method='GET',data?:unknown):Promise<T>{
 const csrf=document.cookie.split('; ').find(x=>x.startsWith('rover_csrf='))?.split('=')[1]||'';
 const r=await fetch('/api'+path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:data===undefined?undefined:JSON.stringify(data)});
 const body=await r.json();if(!r.ok)throw new Error(typeof body.detail==='string'?body.detail:JSON.stringify(body.detail));return body;
}
