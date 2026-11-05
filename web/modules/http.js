/** REST JSON local. Erros controlados e tratamento de falha de conexão. */
export async function api(path,args){
 const opts=args===undefined?{method:'GET'}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(args)};
 const resp=await fetch('/api/'+path,opts);
 let data;try{data=await resp.json()}catch{throw Error('Resposta inválida do servidor local')}
 if(!resp.ok)throw Error(data.error||`Erro HTTP ${resp.status}`);
 return data;
}