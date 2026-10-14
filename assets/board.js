export default function(component){
 const {parentElement,data,setTriggerValue}=component;
 const root=parentElement.querySelector('.board'); root.replaceChildren(); root.style.direction=data.direction;
 const send=(command)=>setTriggerValue('event',{...command,nonce:crypto.randomUUID()});
 let dragged=null;
 const text=(tag,value,className)=>{const el=document.createElement(tag);el.textContent=value; if(className)el.className=className;return el;};
 for(const [index,status] of data.statuses.entries()){
  const lane=text('section','','lane'); lane.dataset.status=status; lane.setAttribute('aria-label',data.labels[index]);
  const items=data.tasks.filter(t=>t.status===status); const heading=text('h3',data.labels[index]); heading.append(text('span',String(items.length),'count')); lane.append(heading);
  lane.ondragover=e=>{e.preventDefault();lane.classList.add('drag-over');}; lane.ondragleave=()=>lane.classList.remove('drag-over');
  lane.ondrop=e=>{e.preventDefault();e.stopPropagation();lane.classList.remove('drag-over');if(dragged)send({action:'move',id:dragged,status,before:null});};
  for(const [position,task] of items.entries()){
   const card=text('article','','task');card.draggable=true;card.tabIndex=0;card.dataset.taskId=task.id;card.setAttribute('aria-label',task.title);
   card.ondragstart=e=>{dragged=task.id;e.dataTransfer.setData('text/plain',task.id);e.dataTransfer.effectAllowed='move';card.classList.add('dragging');};
   card.ondragend=()=>{dragged=null;card.classList.remove('dragging');};
   card.ondragover=e=>{e.preventDefault();};
   card.ondrop=e=>{e.preventDefault();e.stopPropagation();if(dragged && dragged!==task.id)send({action:'move',id:dragged,status,before:task.id});};
   const project=text('div',task.project||data.inbox,'project');const dot=text('span','','dot');dot.style.background=task.color;project.prepend(dot);card.append(project,text('strong',task.title),text('small',task.detail));
   if(task.blocked)card.append(text('small',data.blocked+' · '+task.blocked));
   if(task.checks)card.append(text('small',task.checks));
   const row=text('div','','actions');
   const edit=text('button',data.details);edit.type='button';edit.onclick=()=>send({action:'edit',id:task.id});row.append(edit);
   const select=document.createElement('select');select.setAttribute('aria-label',data.move+' '+task.title);
   data.statuses.forEach((s,i)=>{const opt=text('option',data.labels[i]);opt.value=s;opt.selected=s===status;select.append(opt);});
   select.onchange=()=>send({action:'move',id:task.id,status:select.value,before:null});row.append(select);
   const up=text('button','↑');up.title=data.up;up.setAttribute('aria-label',data.up+' '+task.title);up.disabled=position===0;up.onclick=()=>send({action:'move',id:task.id,status,before:items[position-1].id});row.append(up);
   const down=text('button','↓');down.title=data.down;down.setAttribute('aria-label',data.down+' '+task.title);down.disabled=position===items.length-1;down.onclick=()=>send({action:'move',id:task.id,status,before:items[position+2]?.id||null});row.append(down);
   card.append(row);lane.append(card);
  }
  if(!items.length)lane.append(text('p',data.empty,'empty'));root.append(lane);
 }
}
