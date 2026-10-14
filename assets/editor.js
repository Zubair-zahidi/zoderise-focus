export default function(component){
 const {parentElement,data,setStateValue}=component;
 const input=parentElement.querySelector('textarea');const label=parentElement.querySelector('label');const status=parentElement.querySelector('.state');
 label.textContent=data.label;input.setAttribute('aria-label',data.label);input.dir=data.direction;
 input.maxLength=200000;
 const storage='zoderise-draft:'+data.identity;
 let timer=null;
 const emit=()=>{clearTimeout(timer);setStateValue('body',input.value);status.textContent=data.saving;};
 if(input.dataset.token!==data.token){
  input.dataset.token=data.token;input.value=data.body;
  try{const local=JSON.parse(localStorage.getItem(storage));if(local && local.updated>data.updated && !data.force){input.value=local.body;emit();}}catch(e){}
 }
 input.oninput=()=>{try{localStorage.setItem(storage,JSON.stringify({body:input.value,updated:Date.now()/1000}));}catch(e){}status.textContent=data.saving;clearTimeout(timer);timer=setTimeout(emit,750);};
 input.onblur=()=>{if(input.value!==data.body)emit();};
 status.textContent=input.value===data.body?data.saved:data.saving;
 return()=>{clearTimeout(timer);};
}
