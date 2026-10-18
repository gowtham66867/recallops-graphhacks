export class ApiError extends Error {constructor(message:string,public status:number){super(message)}}
export async function api<T>(path:string,body?:unknown):Promise<T>{
 const response=await fetch('/api'+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 if(!response.ok){const data=await response.json().catch(()=>({detail:'The server could not complete this request.'}));throw new ApiError(typeof data.detail==='string'?data.detail:'Request validation failed',response.status);}
 return response.json();
}
