/* Cronômetro vinculado à disciplina. Rascunho local e gravação SQLite idempotente. */
const STORAGE='cm_study_timer_draft_v1';
function localDay(){
  const d=new Date();
  return [d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-');
}
function newState(){
  return {id:crypto.randomUUID(),subject:'',topic:'',method:'Teoria',elapsed:0,running:false,startedAt:0};
}
function restore(){
  try{
    const s=JSON.parse(localStorage.getItem(STORAGE)||'null');
    if(!s||typeof s.id!=='string'||!Number.isFinite(s.elapsed)||s.elapsed<0)return newState();
    // Nunca computar como estudo o período em que o navegador ficou fechado.
    return {...newState(),...s,elapsed:Math.min(s.elapsed,36000000),
            running:false,startedAt:0};
  }catch{return newState();}
}
const duration=ms=>{
  const seconds=Math.floor(ms/1000);
  return [Math.floor(seconds/3600),Math.floor(seconds%3600/60),seconds%60]
    .map(x=>String(x).padStart(2,'0')).join(':');
};
export function createStudyTimer({api,onSaved,onError,getSubjects}){
  let state=restore(),busy=false;
  let select,display,mode,start,pause,save,reset;
  function elapsed(){
    return Math.min(36000000,state.elapsed+(state.running?Math.max(0,Date.now()-state.startedAt):0));
  }
  function persist(){
    const saved={...state,elapsed:elapsed(),running:false,startedAt:0};
    localStorage.setItem(STORAGE,JSON.stringify(saved));
  }
  function update(){
    if(!display)return;
    display.textContent=duration(elapsed());
    if(select){
      const subjects=(getSubjects()||[]).map(x=>x.name);
      if(select.options.length!==subjects.length+1){
        select.replaceChildren();
        select.add(new Option('Escolha disciplina',''));
        subjects.forEach(name=>select.add(new Option(name,name)));
      }
      select.value=subjects.includes(state.subject)?state.subject:'';
      select.disabled=state.running||busy||elapsed()>0;
      if(!subjects.includes(state.subject))state.subject='';
    }
    if(mode)mode.textContent=state.running?'Contabilizando':elapsed()>0?'Pausado / a salvar':'Tempo líquido';
    start.disabled=state.running||busy;
    pause.disabled=!state.running||busy;
    save.disabled=elapsed()<60000||busy;
    reset.disabled=busy;
  }
  function settle(){
    if(state.running){
      state.elapsed=elapsed();
      state.startedAt=0;
      state.running=false;
    }
  }
  async function doSave(){
    settle();update();persist();
    const mins=Math.floor(elapsed()/60000);
    if(mins<1){onError('Estude ao menos um minuto para registrar a sessão.');return;}
    if(!state.subject){onError('Selecione uma disciplina antes de iniciar.');return;}
    busy=true;update();
    try{
      const result=await api('study-time/save',{
        session_id:state.id,subject:state.subject,minutes:mins,
        day:localDay(),method:state.method,topic:state.topic
      });
      // Somente apaga rascunho após confirmação do servidor; retries usam mesmo UUID.
      state=newState();localStorage.removeItem(STORAGE);
      update();await onSaved(result);
    }catch(error){onError('Não foi possível salvar: '+error.message+'. Seu tempo permanece disponível para tentar novamente.');}
    finally{busy=false;update();}
  }
  function command(action){
    if(busy)return;
    if(action==='start'){
      if(!state.subject){onError('Escolha a disciplina no cronômetro antes de iniciar.');return;}
      if(state.running)return;
      state.running=true;state.startedAt=Date.now();
    }
    if(action==='pause')settle();
    if(action==='reset'){
      if(state.running){onError('Pause antes de zerar.');return;}
      if(state.elapsed&&!confirm('Descartar o tempo ainda não salvo?'))return;
      state=newState();localStorage.removeItem(STORAGE);
    }
    if(action==='save'){doSave();return;}
    persist();update();
  }
  function init(){
    select=document.getElementById('timer-subject');
    display=document.getElementById('timer-display');
    mode=document.getElementById('timer-mode-text');
    start=document.getElementById('timer-start');
    pause=document.getElementById('timer-pause');
    save=document.getElementById('timer-save');
    reset=document.getElementById('timer-reset');
    select.addEventListener('change',e=>{
      if(elapsed()>0||busy)return;
      state.subject=e.target.value;
      persist();update();
    });
    [['start',start],['pause',pause],['save',save],['reset',reset]].forEach(
      ([action,btn])=>btn.addEventListener('click',()=>command(action))
    );
    // Persiste apenas rascunho pausado; retomada nunca soma o tempo fora do navegador.
    window.addEventListener('pagehide',persist);
    document.addEventListener('visibilitychange',()=>{if(document.hidden)persist();});
    setInterval(()=>{update();if(state.running)persist();},1000);
    update();
  }
  return {init,update,command};
}
