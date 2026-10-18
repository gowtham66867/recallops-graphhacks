export async function api<T>(path:string,body?:unknown):Promise<T>{
 const response=await fetch('/api'+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 if(!response.ok){const data=await response.json().catch(()=>({detail:'The server could not complete this request.'}));throw new Error(data.detail||'Request failed');}
 return response.json();
}
