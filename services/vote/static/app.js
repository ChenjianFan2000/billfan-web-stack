import {VoteClient, storedPreference, setPreference} from './api.js?v=1';
import {$, $$, node, button, toast, timeText, voteStatus, showStatus, errorMessage, setupModals, openModal, closeModal, renderConnection} from './ui.js?v=1';

const client = new VoteClient();
const page = document.body.dataset.page;
let filter = 'all', search = '', starting = false;
let bootRetry = 0, bootTimer;
let lastPlayersSignature = '', lastMessagesSignature = '';
let flightQueue = [], flightLane = 0, nextFlight = 0;
const shownMessages = new Set();
let motionPaused = storedPreference('motionPaused', matchMedia('(prefers-reduced-motion: reduce)').matches ? 'true' : 'false') === 'true';
setupModals();

const candidates = () => client.state?.contestants || [];
const votedFor = id => (client.state?.me?.votes || []).includes(id);
const current = () => candidates().find(c => c.id === client.state?.currentId);
const voteReady = c => c?.voting === 'open' && client.live && !client.pending.size && Date.now() >= client.nextVoteAt;

function adjustmentList(contestant, target) {
  target.replaceChildren();
  for (const item of contestant?.adjustments || []) target.append(node('li', '', '票数调整 ' + (item.delta > 0 ? '+' : '') + item.delta + ' · ' + item.reason));
  target.hidden = !target.childElementCount;
}

function renderCurrent() {
  if (page !== 'vote') return;
  const c = current(), voted = c && votedFor(c.id), saving = c && client.pending.has(c.id);
  $('#round-number').textContent = c ? 'NO. ' + String(c.order+1).padStart(2,'0') : 'NO. —';
  $('#performer-name').textContent = c?.name || '好戏，即将开场';
  $('#performer-group').textContent = c ? (c.group ? c.group + ' · ' : '') + showStatus(c) : '主持人选定选手后，就可以在这里投票';
  $('#voting-state').textContent = voteStatus(c);
  $('#voting-state').className = 'badge ' + (c?.voting || 'pending');
  const vote = $('#vote-button'); vote.disabled = !voteReady(c); vote.classList.toggle('voted', Boolean(voted));
  $('.vote-icon', vote).textContent = voted ? '✓' : '＋';
  $('#vote-label').textContent = saving ? '正在保存…' : !client.state ? '正在连接现场' : !c ? '等待主持人开票' : c.voting === 'locked' ? (voted ? '已投票 · 本轮已锁票' : '本轮已锁票') : c.voting === 'pending' ? '等待主持人开票' : !client.live ? '重新同步中…' : voted ? '已投票 · 点击取消' : '投 TA 一票';
  const note = $('#vote-note'); note.classList.toggle('success', Boolean(voted));
  note.textContent = !client.state ? '正在找回你的投票状态…' : !c ? '现场准备好后，你的这一票随时就位。' : saving ? '请稍候，以服务器确认结果为准' : c.voting === 'locked' ? (voted ? '这一票已保存，谢谢你的支持。' : '投票已结束，继续为下一位选手加油。') : c.voting === 'pending' ? '开票后，点击按钮即可支持这位选手。' : voted ? '你的选择已保存，锁票前可随时取消。' : '每位选手限一票，锁票前可随时修改。';
  const result = $('#released-votes'); result.hidden = !c || !c.published;
  if (c?.published) { result.replaceChildren(node('span','','现场公布'),node('strong','',c.votes ?? '—'),node('span','','票')); }
  adjustmentList(c, $('#current-adjustments'));
}

async function voteFor(c) {
  if (!voteReady(c)) return;
  const desired = !votedFor(c.id);
  try { if (await client.vote(c, desired)) toast(desired ? '这一票，已送达！' : '已取消投票，锁票前可以再支持 TA。'); }
  catch (error) { toast(errorMessage(error)); }
}
$('#vote-button')?.addEventListener('click', () => voteFor(current()));

function renderPlayers(force = false) {
  if (page !== 'players' || !client.state) return;
  const list = candidates().slice().sort((a,b) => a.order - b.order || a.name.localeCompare(b.name));
  $('#count-all').textContent = list.length;
  $('#count-performed').textContent = list.filter(c => c.status === 'performed').length;
  $('#count-mine').textContent = (client.state.me?.votes || []).length;
  const signature = JSON.stringify([list,client.state.me?.votes,client.state.currentId,client.live,[...client.pending],Date.now() < client.nextVoteAt,filter,search]);
  if (!force && signature === lastPlayersSignature) return; lastPlayersSignature = signature;
  const focused = document.activeElement?.dataset?.voteId;
  const visible = list.filter(c => (filter !== 'mine' || votedFor(c.id)) && (filter !== 'open' || c.voting === 'open') && (!search || (c.name + ' ' + c.group).toLowerCase().includes(search)));
  const container = $('#players-list'); container.replaceChildren();
  if (!visible.length) {
    const empty = node('div','empty-card');
    if (!list.length) { const img = node('img'); img.src='/assets/mascot-sign.jpg'; img.alt='旦口吉祥物'; empty.append(img,node('strong','','选手们正在候场'),node('p','','名单公布后，会自动出现在这里。')); }
    else empty.append(node('strong','',filter === 'mine' ? '你的掌声，还在路上' : '这里暂时没有选手'),node('p','',filter === 'mine' ? '投出第一票后，就可以在这里找到 TA。' : '试试其他筛选，或者等主持人开票。'));
    container.append(empty); return;
  }
  for (const c of visible) {
    const mine = votedFor(c.id), card = node('article','player-card' + (c.id === client.state.currentId ? ' current' : ''));
    const top = node('div','player-top'), text = node('div','player-text');
    top.append(node('span','player-order',String(c.order+1).padStart(2,'0')));
    text.append(node('h2','',c.name),node('p','',c.group || '未分组'));
    const badges = node('div','player-badges'); badges.append(node('span','badge ' + c.voting,voteStatus(c)),node('span','badge' + (c.id===client.state.currentId?' current':''),showStatus(c)));
    text.append(badges); top.append(text);
    if (c.published) top.append(node('span','player-result',(c.votes ?? '—') + ' 票'));
    const actions = node('div','player-actions');
    actions.append(node('span','player-my-state' + (mine?' voted':''),mine ? '✓ 我已投票' : '我还未投票'));
    const action = button(client.pending.has(c.id) ? '保存中…' : c.voting === 'locked' ? '已锁票' : c.voting === 'pending' ? '未开票' : mine ? '取消投票' : '投一票','small-vote'+(mine?' voted':''),() => voteFor(c));
    action.disabled = !voteReady(c); action.dataset.voteId = c.id;
    action.setAttribute('aria-label',c.name + '，' + action.textContent); actions.append(action);
    const adjusts = node('ul','adjustment-list'); adjustmentList(c,adjusts);
    card.append(top,actions,adjusts); container.append(card);
  }
  if (focused) $$('[data-vote-id]').find(b => b.dataset.voteId===focused)?.focus({preventScroll:true});
}

function renderChat() {
  if (page !== 'vote' || !client.state) return;
  const messages = (client.state.messages || []).slice().sort((a,b) => a.createdAt-b.createdAt);
  const signature = JSON.stringify(messages);
  if (signature !== lastMessagesSignature) {
    const initial = !lastMessagesSignature; lastMessagesSignature = signature;
    const fresh = messages.filter(m => !shownMessages.has(m.id));
    fresh.forEach(m => shownMessages.add(m.id));
    if (shownMessages.size > 500) { shownMessages.clear(); messages.forEach(m => shownMessages.add(m.id)); }
    const allowed = new Set(messages.map(m => m.id));
    $$('.danmaku-pill').forEach(pill => { if (!allowed.has(pill.dataset.messageId)) pill.remove(); });
    flightQueue = [...flightQueue.filter(m => allowed.has(m.id)),...(initial ? fresh.slice(-3) : fresh)].slice(-18);
    const list = $('#message-list'); list.replaceChildren();
    for (const message of messages.slice(-5).reverse()) {
      const li = node('li',message.highlight ? 'highlight' : '');
      const time = node('time','',timeText(message.createdAt)); time.dateTime = new Date(message.createdAt).toISOString();
      li.append(node('span','message-by',message.highlight?'主持人':'现场'),node('span','message-text',message.text),time); list.append(li);
    }
    const announcement = messages.filter(m=>m.highlight).slice(-1)[0];
    $('#admin-announcement').hidden = !announcement;
    $('#admin-announcement').textContent = announcement?.text || '';
    $('#chat-empty').hidden = Boolean(messages.length);
  }
  renderComposer();
}

function renderComposer() {
  if (page !== 'vote') return;
  const bannedUntil = client.state?.me?.bannedUntil || 0;
  const banned = bannedUntil > client.now();
  const seconds = Math.ceil(Math.max(0,client.nextMessageAt-Date.now())/1000);
  const sending = $('#message-form').dataset.sending === 'true';
  $('#send-message').disabled = !client.live || banned || seconds > 0 || sending;
  $('#send-message').textContent = sending ? '发送中' : banned ? '禁言中' : seconds ? seconds+'s' : '发送 ↗';
  $('#message-hint').textContent = banned ? '暂时无法发言，将于 ' + timeText(bannedUntil) + ' 恢复' : !client.live ? '连接恢复后就能继续发送弹幕' : '友好发言，让快乐被大家看见';
}

$('#message-input')?.addEventListener('input', () => { $('#message-count').textContent = $('#message-input').value.length+' / 80'; });
$('#message-form')?.addEventListener('submit', async event => {
  event.preventDefault();
  const input = $('#message-input'), text = input.value.trim();
  if (!text || $('#send-message').disabled) return;
  $('#message-form').dataset.sending='true'; renderComposer();
  try { await client.message(text); input.value=''; $('#message-count').textContent='0 / 80'; toast('弹幕已发送，大家都能看到。'); }
  catch (error) { if (error.retryAfterMs) client.nextMessageAt=Date.now()+error.retryAfterMs; toast(errorMessage(error)); await client.refresh().catch(()=>{}); }
  finally { $('#message-form').dataset.sending='false'; renderComposer(); }
});

function motionState() {
  if (page!=='vote') return;
  $('#danmaku-stage').classList.toggle('paused', motionPaused);
  $('#motion-toggle').setAttribute('aria-pressed',String(motionPaused));
  $('#motion-toggle').textContent=motionPaused?'开启飘动':'暂停飘动';
}
$('#motion-toggle')?.addEventListener('click',()=>{motionPaused=!motionPaused;setPreference('motionPaused',String(motionPaused));motionState();});
motionState();
if (page==='vote') setInterval(()=>{
  if(document.hidden)return;
  renderComposer();
  if(motionPaused || !flightQueue.length || Date.now()<nextFlight || $$('.danmaku-pill').length>=6)return;
  const message=flightQueue.shift(), pill=node('span','danmaku-pill'+(message.highlight?' highlight':''),message.text);
  pill.dataset.messageId=message.id;
  const hasAnnouncement=!$('#admin-announcement').hidden;
  pill.style.top=(hasAnnouncement ? [71,108][flightLane++%2] : [17,56,95][flightLane++%3])+'px';
  pill.addEventListener('animationend',()=>pill.remove(),{once:true});
  $('#danmaku-tracks').append(pill);setTimeout(()=>pill.remove(),16000);nextFlight=Date.now()+2300;
},500);

$$('[data-filter]').forEach(item=>item.addEventListener('click',()=>{
  filter=item.dataset.filter;
  $$('[data-filter]').forEach(other=>{other.classList.toggle('active',other===item);other.setAttribute('aria-pressed',String(other===item));});renderPlayers(true);
}));
$('#player-search')?.addEventListener('input',event=>{search=event.target.value.trim().toLowerCase();renderPlayers(true);});

$$('.identity-help').forEach(item=>item.addEventListener('click',()=>openModal($('#identity-dialog'))));
$('#copy-recovery').addEventListener('click',async()=>{
  if(!client.recoveryCode){toast('请等待身份同步完成后再复制。');return;}
  const url=location.origin+'/#restore='+encodeURIComponent(client.recoveryCode);
  try{await navigator.clipboard.writeText(url);toast('恢复链接已复制，请妥善保存。');}
  catch(_){$('#copy-fallback').hidden=false;$('#recovery-output').value=url;$('#recovery-output').focus();$('#recovery-output').select();}
});
function parseRecovery(text){
  const value=text.trim();
  if(value.includes('#')){try{return new URLSearchParams(new URL(value).hash.slice(1)).get('restore')||'';}catch(_){return '';}}
  return value;
}
$('#recovery-form').addEventListener('submit',async event=>{
  event.preventDefault();const code=parseRecovery($('#recovery-input').value);
  if(code.length<20||code.length>512){toast('请粘贴完整的恢复链接或恢复码。');return;}
  const submit=$('button[type="submit"]',event.target);submit.disabled=true;
  try{client.stopStream();await client.start(code);closeModal();toast('已找回原来的投票记录。');$('#recovery-input').value='';}
  catch(error){toast(errorMessage(error));client.resume();}
  finally{submit.disabled=false;}
});

function render(){
  if(client.state?.title) document.title=(page==='players'?'选手名单':'现场投票')+' · '+client.state.title;
  renderCurrent();renderPlayers();renderChat();
}
client.addEventListener('change',render);
client.addEventListener('connection',()=>{renderConnection(client);render();});
client.addEventListener('expired',()=>{if(!starting){client.stopStream();boot();}});
$('#connection').addEventListener('click',()=>{if(!client.state)boot();else client.resume();});

async function boot(code=''){
  if(starting)return;clearTimeout(bootTimer);starting=true;client.setConnection('connecting');
  try{await client.start(code);bootRetry=0;}
  catch(error){
    client.setConnection('offline');toast(errorMessage(error),7000);$('#network-banner').textContent='暂时无法连接现场。联网后会自动重试，也可以点击右上角重新连接。';if(page==='vote')$('#vote-label').textContent='等待恢复连接';
    if(!code && navigator.onLine && !document.hidden)bootTimer=setTimeout(()=>boot(),Math.min(30000,1500*2**Math.min(bootRetry++,5))*(.8+Math.random()*.4));
  }
  finally{starting=false;}
}
window.addEventListener('online',()=>{if(!client.state)boot();});
window.addEventListener('pageshow',()=>{if(!client.state)boot();});
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&!client.state)boot();});
const restore=new URLSearchParams(location.hash.slice(1)).get('restore')||'';
if(restore) history.replaceState(null,'',location.pathname+location.search);
boot(restore);
