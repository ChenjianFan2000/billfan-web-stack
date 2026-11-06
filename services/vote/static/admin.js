import {VoteClient} from './api.js?v=1';
import {$,$$,node,button,toast,timeText,dateText,voteStatus,showStatus,errorMessage,setupModals,openModal,closeModal,renderConnection} from './ui.js?v=1';

const client=new VoteClient(true);
let busy=false, selected=new Set(), activeTab='lineup', confirmedAction=null;
let contestantSignature='', messageSignature='', auditSignature='', optionsSignature='';
let authAttempt=0;
setupModals();
const contestants=()=>client.state?.contestants||[];
const getContestant=id=>contestants().find(c=>c.id===id);
const current=()=>getContestant(client.state?.currentId);
const actionNames={upsert_contestant:'保存选手',import_contestants:'批量导入',remove_contestant:'删除选手',select:'切换当前选手',open:'开启投票',lock:'锁定投票',lock_all:'全部锁票',set_status:'修改演出状态',publish:'调整票数展示',adjust:'调整票数',message:'管理员弹幕',delete_message:'删除弹幕',ban:'调整发言权限',settings:'修改活动设置'};

function updateBusy(){
  const c=current();
  $('#open-voting').disabled=busy||!client.live||!c||c.voting==='open';
  $('#open-voting').textContent=c?.voting==='locked'?'重新开票':'开启投票';
  $('#lock-voting').disabled=busy||!client.live||!c||c.voting!=='open';
  $('#lock-voting').textContent=c?.voting==='locked'?'本轮已锁票':'立即锁票';
  $('#switch-submit').disabled=busy||!client.live||!contestants().length;
  $$('.admin-panel button:not([data-local]),.modal form button[type="submit"]').forEach(b=>b.disabled=busy||!client.live);
  $('#add-contestant').disabled=busy;$('#import-contestants').disabled=busy;
}
async function act(action,values={},success='操作已同步到现场'){
  if(busy)return false;
  if(!client.live){toast('正在恢复连接，请同步完成后再操作。');return false;}
  busy=true;updateBusy();
  try{await client.action(action,values);toast(success);return true;}
  catch(error){
    if(error.code==='revision_conflict'){
      if(error.body?.state)client.accept(error.body.state);
      toast('其他管理员刚刚更新了现场。已同步最新状态，请核对后再操作。',6500);
    }else{
      await client.refresh().catch(()=>client.setConnection('reconnecting'));
      toast(errorMessage(error),5500);
    }
    return false;
  }finally{busy=false;updateBusy();renderContestants(true);}
}
function confirm(title,text,handler){
  $('#confirm-title').textContent=title;$('#confirm-text').textContent=text;
  confirmedAction=handler;openModal($('#confirm-dialog'));
}
$('#confirm-cancel').addEventListener('click',()=>{confirmedAction=null;closeModal();});
$('#confirm-submit').addEventListener('click',async()=>{
  const action=confirmedAction;confirmedAction=null;closeModal();if(action)await action();
});

function rebuildOptions(){
  const signature=JSON.stringify(contestants().map(c=>[c.id,c.name,c.group,c.order]));
  if(signature===optionsSignature)return;optionsSignature=signature;
  ['#switch-contestant','#adjust-contestant'].forEach(selector=>{
    const select=$(selector), previous=select.value;
    select.replaceChildren(new Option('请选择选手',''));
    [...contestants()].sort((a,b)=>a.order-b.order).forEach(c=>select.add(new Option(String(c.order+1).padStart(2,'0')+' · '+c.name+(c.group?' / '+c.group:''),c.id)));
    if(getContestant(previous))select.value=previous;
    else if(selector==='#switch-contestant'&&client.state.currentId)select.value=client.state.currentId;
  });
}
function renderHeader(){
  const state=client.state;if(!state)return;
  $('#event-title').textContent=state.title;document.title='现场控制台 · '+state.title;
  const c=current();
  $('#admin-current-name').textContent=c?.name||'尚未选择选手';
  $('#admin-current-group').textContent=c?((c.group?c.group+' · ':'')+'第 '+(c.order+1)+' 位'):'先导入选手，再选择当前选手';
  $('#admin-current-state').textContent=voteStatus(c);
  $('#admin-current-state').className='badge '+(c?.voting||'pending');
  $('#stat-contestants').textContent=contestants().length;
  $('#stat-open').textContent=contestants().filter(c=>c.voting==='open').length;
  $('#stat-performed').textContent=contestants().filter(c=>c.status==='performed').length;
  $('#stat-revision').textContent=state.revision;
  if(!$('#title-input').dataset.dirty)$('#title-input').value=state.title;
  rebuildOptions();updateBusy();
}
function renderContestants(force=false){
  if(!client.state)return;
  const rows=[...contestants()].sort((a,b)=>a.order-b.order), ids=new Set(rows.map(c=>c.id));
  selected=new Set([...selected].filter(id=>ids.has(id)));
  $('#select-all').checked=rows.length>0&&selected.size===rows.length;
  $('#select-all').indeterminate=selected.size>0&&selected.size<rows.length;
  const signature=JSON.stringify([rows,client.state.currentId,[...selected],busy,client.live]);
  if(!force&&signature===contestantSignature)return;contestantSignature=signature;
  const list=$('#admin-contestants');list.replaceChildren();
  if(!rows.length){list.append(node('div','empty-card','名单还空着，添加第一位选手吧。'));return;}
  for(const c of rows){
    const row=node('article','admin-contestant'),checkbox=node('input');checkbox.type='checkbox';checkbox.checked=selected.has(c.id);
    checkbox.setAttribute('aria-label','选择 '+c.name);
    checkbox.addEventListener('change',()=>{if(checkbox.checked)selected.add(c.id);else selected.delete(c.id);renderContestants(true);});
    const info=node('div'),title=node('h3','',String(c.order+1).padStart(2,'0')+' · '+c.name);
    if(c.id===client.state.currentId)title.append(node('span','badge current','当前'));
    info.append(title,node('p','',(c.group||'未分组')+' · '+showStatus(c)+' · '+voteStatus(c)+' · '+(c.published?'已公布票数':'票数隐藏')));
    const actions=node('div','admin-row-actions');
    actions.append(button('编辑','button compact',()=>editContestant(c)));
    if(c.id!==client.state.currentId)actions.append(button('设为当前','button compact',()=>act('select',{contestantId:c.id,lockPrevious:$('#lock-previous').checked},'已切换到 '+c.name)));
    actions.append(button(c.voting==='open'?'锁票':c.voting==='locked'?'重开':'开票','button compact'+(c.voting==='open'?' danger':''),()=>{
      if(c.voting==='locked')confirm('重新开启 '+c.name+' 的投票？','重新开票后，观众可以继续投票或取消之前的投票。',()=>act('open',{contestantId:c.id},'已重新开票'));
      else act(c.voting==='open'?'lock':'open',{contestantId:c.id},c.voting==='open'?'已锁票，服务器已停止接受更改':'已开启投票');
    }));
    actions.append(button(c.status==='performed'?'标记待上场':'标记已演出','button compact',()=>act('set_status',{contestantId:c.id,status:c.status==='performed'?'upcoming':'performed'},'演出状态已更新')));
    actions.append(button('删除','button compact',()=>confirm('删除 '+c.name+'？','仅可删除非当前、没有任何投票或调整记录的选手。',()=>act('remove_contestant',{contestantId:c.id},'已删除选手'))));
    $$('button',actions).forEach(b=>b.disabled=busy||!client.live);
    info.append(actions);
    const tally=node('div','admin-side-actions');tally.append(node('div','admin-vote-total',c.votes??0),node('p','raw-votes-note','原始 '+c.rawVotes+' · 调整 '+(c.adjustmentTotal>0?'+':'')+c.adjustmentTotal));
    row.append(checkbox,info,tally);list.append(row);
  }
}
function renderAdjust(){
  const target=$('#adjust-detail'),c=getContestant($('#adjust-contestant').value);target.replaceChildren();
  target.className=c?'':'empty-card';
  if(!c){target.textContent='选择一位选手查看明细。';return;}
  const summary=node('div','lineup-summary');
  [['原始票数',c.rawVotes],['调整合计',(c.adjustmentTotal>0?'+':'')+c.adjustmentTotal],['显示票数',c.votes]].forEach(([label,value])=>{
    const item=node('div');item.append(node('strong','',value),node('span','',label));summary.append(item);
  });
  target.append(summary);
  if(!c.adjustments.length){target.append(node('p','panel-description','还没有票数调整记录。'));return;}
  const list=node('ul','audit-list');
  for(const a of c.adjustments.slice().reverse()){
    const li=node('li');li.append(node('strong','',(a.delta>0?'+':'')+a.delta+' 票 · '+(a.public?'公开理由':'仅后台记录')),node('time','',dateText(a.createdAt)),node('p','',a.reason||'未填写内部备注'));
    list.append(li);
  }target.append(list);
}
function openBan(message){
  $('#ban-user').value=message.userId;$('#ban-seconds').value='300';
  $('#ban-target').textContent='观众 '+message.userId.slice(-8)+' · “'+message.text+'”';
  openModal($('#ban-dialog'));
}
function renderMessages(){
  const messages=(client.state?.messages||[]).filter(m=>!m.deleted).slice().reverse();
  const signature=JSON.stringify([messages,busy,client.live]);if(signature===messageSignature)return;messageSignature=signature;
  const list=$('#admin-messages');list.replaceChildren();
  if(!messages.length){list.append(node('div','empty-card','现场还没有弹幕，发出第一条通知吧。'));return;}
  for(const m of messages){
    const card=node('article','admin-message'+(m.highlight?' highlight':''));
    const meta=node('div','admin-message-meta');
    meta.append(node('span','',m.userId?'观众 · '+m.userId.slice(-8):(m.highlight?'主持人 · 醒目弹幕':'管理员弹幕')),node('time','',timeText(m.createdAt)));
    const actions=node('div','admin-message-actions');
    actions.append(button('删除弹幕','',()=>act('delete_message',{messageId:m.id},'弹幕已从现场移除')));
    if(m.userId){actions.append(button('禁言…','',()=>openBan(m)),button('解除禁言','',()=>act('ban',{userId:m.userId,seconds:0},'已恢复这位观众的发言权限')));}
    $$('button',actions).forEach(b=>b.disabled=busy||!client.live);
    card.append(meta,node('p','',m.text),actions);list.append(card);
  }
}
function auditDescription(item){
  const d=item.detail||{},c=getContestant(d.contestantId||d.id),name=c?.name||d.contestantId||'';
  if(item.action==='adjust')return name+' '+(d.delta>0?'+':'')+d.delta+' 票 · '+(d.public?'公开理由':'仅后台记录')+' · '+(d.reason||'无备注');
  if(item.action==='message')return (d.highlight===false?'普通弹幕':'醒目弹幕')+' · '+d.text;
  if(item.action==='ban')return '观众 '+String(d.userId||'').slice(-8)+' · '+(d.seconds?'禁言 '+Math.round(d.seconds/60)+' 分钟':'解除禁言');
  if(item.action==='import_contestants')return '新增 '+d.count+' 位选手';
  if(item.action==='upsert_contestant')return (d.contestant?.name||name)+' · '+(d.contestant?.group||'未分组');
  if(item.action==='publish')return (d.visible?'公布':'隐藏')+' '+(d.contestantIds?.length||0)+' 位选手的票数';
  if(item.action==='settings')return d.title||'';
  if(item.action==='set_status')return name+' · '+showStatus({status:d.status});
  if(item.action==='delete_message')return '已移除弹幕 '+(d.messageId||'');
  return name||'已同步到现场';
}
function renderAudit(){
  const audit=client.state?.audit||[],signature=JSON.stringify(audit);if(signature===auditSignature)return;auditSignature=signature;
  const list=$('#audit-list');list.replaceChildren();
  if(!audit.length){list.append(node('li','muted','还没有管理操作记录。'));return;}
  for(const item of audit){const li=node('li');li.append(node('strong','',actionNames[item.action]||item.action),node('time','',dateText(item.createdAt)),node('p','',auditDescription(item)));list.append(li);}
}
function render(){renderHeader();renderContestants();renderAdjust();renderMessages();renderAudit();}
client.addEventListener('change',render);
client.addEventListener('connection',()=>{renderConnection(client);updateBusy();renderContestants();renderMessages();});
client.addEventListener('expired',()=>showLogin('管理会话已结束，请重新打开专属链接或输入密码。'));
$('#connection').addEventListener('click',()=>{if(client.state&&!client.stopped)client.resume();else autoLogin();});
$$('[data-tab]').forEach(tab=>tab.addEventListener('click',()=>{
  activeTab=tab.dataset.tab;
  $$('[data-tab]').forEach(other=>{other.classList.toggle('active',other===tab);other.setAttribute('aria-pressed',String(other===tab));});
  $$('.admin-panel').forEach(panel=>panel.hidden=panel.id!=='panel-'+activeTab);
}));
$('#open-voting').addEventListener('click',()=>{const c=current();if(!c)return;if(c.voting==='locked')confirm('重新开放本轮投票？','观众将可以修改这位选手的投票，已保存的票不会清空。',()=>act('open',{contestantId:c.id},'本轮已重新开票'));else act('open',{contestantId:c.id},'本轮已开票');});
$('#lock-voting').addEventListener('click',()=>{const c=current();if(c)act('lock',{contestantId:c.id},'本轮已锁票，服务器已停止接受更改');});
$('#switch-form').addEventListener('submit',event=>{event.preventDefault();const id=$('#switch-contestant').value;if(id)act('select',{contestantId:id,lockPrevious:$('#lock-previous').checked},'当前选手已切换；请按需要开启投票');});
$('#select-all').addEventListener('change',event=>{selected=event.target.checked?new Set(contestants().map(c=>c.id)):new Set();renderContestants(true);});
async function publish(visible){
  if(!selected.size){toast('请先勾选需要操作的选手。');return;}
  await act('publish',{contestantIds:[...selected],visible},visible?'所选票数已向观众公布':'所选票数已隐藏');
}
$('#publish-selected').addEventListener('click',()=>publish(true));
$('#hide-selected').addEventListener('click',()=>publish(false));
$('#lock-all').addEventListener('click',()=>confirm('锁定全部正在进行的投票？','所有已开票选手将立即停止接受投票和取消。未开票的选手保持未开票。',()=>act('lock_all',{},'所有开票中的选手已锁票')));
function editContestant(c=null){
  $('#contestant-dialog-title').textContent=c?'编辑选手':'添加选手';
  $('#contestant-id').value=c?.id||'';$('#contestant-name').value=c?.name||'';$('#contestant-group').value=c?.group||'';
  $('#contestant-order').value=c?c.order+1:Math.max(0,...contestants().map(x=>x.order+1))+1;
  openModal($('#contestant-dialog'));
}
$('#add-contestant').addEventListener('click',()=>editContestant());
$('#contestant-form').addEventListener('submit',async event=>{
  event.preventDefault();
  const value={name:$('#contestant-name').value.trim(),group:$('#contestant-group').value.trim(),order:Number($('#contestant-order').value)-1};
  if($('#contestant-id').value)value.id=$('#contestant-id').value;
  if(await act('upsert_contestant',{contestant:value},'选手信息已保存'))closeModal();
});
$('#import-contestants').addEventListener('click',()=>openModal($('#import-dialog')));
$('#import-form').addEventListener('submit',async event=>{
  event.preventDefault();
  const lines=$('#import-input').value.split(/\r?\n/).map(line=>line.trim()).filter(Boolean);
  if(!lines.length||lines.length>100){toast('每次可以导入 1 至 100 位选手。');return;}
  const base=Math.max(-1,...contestants().map(c=>c.order))+1;
  const values=lines.map((line,index)=>{
    const parts=line.split(/\t|,|，/);return {name:parts[0].trim(),group:parts.slice(1).join(' ').trim(),order:base+index};
  });
  if(values.some(c=>!c.name||c.name.length>60||c.group.length>40)){toast('请检查名单：选手姓名最多 60 个字符，组别最多 40 个字符。');return;}
  if(await act('import_contestants',{contestants:values},'已添加 '+values.length+' 位选手')){$('#import-input').value='';closeModal();}
});
$('#adjust-contestant').addEventListener('change',renderAdjust);
$$('input[name="adjust-public"]').forEach(radio=>radio.addEventListener('change',()=>{
  const isPublic=$('input[name="adjust-public"]:checked').value==='public';
  $('#adjust-reason').required=isPublic;
  $('#adjust-reason').placeholder=isPublic?'公开调整必须填写理由，例如现场互动奖励':'可填写内部备注，仅管理员可见';
  $('#adjust-explanation').textContent=isPublic?'票数公布后，观众会同时看到调整数量和理由。所有操作都会记录在管理日志中。':'调整会计入最终显示票数，观众看不到这次调整的明细；管理日志会完整保留。';
}));
$('#adjust-form').addEventListener('submit',event=>{
  event.preventDefault();const c=getContestant($('#adjust-contestant').value),delta=Number($('#adjust-delta').value);
  if(!c||!Number.isSafeInteger(delta)||!delta){toast('请选择选手，并输入非零整数。');return;}
  const values={contestantId:c.id,delta,reason:$('#adjust-reason').value.trim(),public:$('input[name="adjust-public"]:checked').value==='public'};
  confirm('为 '+c.name+' '+(delta>0?'增加 ':'扣除 ')+Math.abs(delta)+' 票？',(values.public?'公开理由：':'仅后台记录：')+(values.reason||'无备注'),async()=>{
    if(await act('adjust',values,'票数调整已保存')){$('#adjust-delta').value='';$('#adjust-reason').value='';}
  });
});
$('#admin-message-form').addEventListener('submit',async event=>{
  event.preventDefault();const text=$('#admin-message-text').value.trim();if(!text)return;
  if(await act('message',{text,highlight:$('#admin-message-highlight').checked},'管理员弹幕已发送到全场'))$('#admin-message-text').value='';
});
$('#ban-form').addEventListener('submit',async event=>{
  event.preventDefault();const seconds=Number($('#ban-seconds').value);
  if(await act('ban',{userId:$('#ban-user').value,seconds},seconds?'禁言设置已生效':'已解除禁言'))closeModal();
});
$('#title-input').addEventListener('input',()=>$('#title-input').dataset.dirty='true');
$('#title-form').addEventListener('submit',async event=>{
  event.preventDefault();if(await act('settings',{title:$('#title-input').value.trim()},'活动名称已保存'))delete $('#title-input').dataset.dirty;
});

function showLogin(message=''){
  client.stopped=true;client.stopStream();client.setConnection('paused');
  $('#login-view').hidden=false;$('#admin-main').hidden=true;$('#logout').hidden=true;
  $('#network-banner').hidden=true;$('#login-error').hidden=!message;$('#login-error').textContent=message;
}
function showAdmin(){
  client.stopped=false;$('#login-view').hidden=true;$('#admin-main').hidden=false;$('#logout').hidden=false;
  $('#admin-password').value='';render();
}
async function login(password){
  const attempt=++authAttempt;
  $('#login-button').disabled=true;$('#login-error').hidden=true;client.stopped=false;
  try{await client.login(password);if(attempt===authAttempt)showAdmin();}
  catch(error){if(attempt===authAttempt)showLogin(errorMessage(error));}
  finally{if(attempt===authAttempt)$('#login-button').disabled=false;password='';}
}
$('#login-form').addEventListener('submit',async event=>{event.preventDefault();let password=$('#admin-password').value;$('#admin-password').value='';await login(password);password='';});
$('#logout').addEventListener('click',async()=>{
  ++authAttempt;
  client.stopped=true;client.stopStream();
  try{await client.api('/api/admin/logout',{method:'POST',body:'{}'});showLogin();toast('已退出现场控制台');}
  catch(error){toast(errorMessage(error));client.stopped=false;client.resume();}
});
async function autoLogin(){
  const attempt=++authAttempt;
  try{client.stopped=false;await client.start();if(attempt===authAttempt)showAdmin();}
  catch(error){if(attempt===authAttempt)showLogin(error.status===401?'':errorMessage(error));}
}
let key=new URLSearchParams(location.hash.slice(1)).get('key')||new URLSearchParams(location.search).get('key')||'';
if(location.hash||location.search)history.replaceState(null,'',location.pathname);
if(key){const password=key;key='';login(password);}
else autoLogin();

