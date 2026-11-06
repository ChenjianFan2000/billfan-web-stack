/**
 * Non-visual integration checks: actual HTML/ES modules run in JSDOM, with a
 * deliberately in-memory fetch/SSE fake. No browser, networking, or screenshots.
 * Run from this directory: npm ci && npm test
 */
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
import {JSDOM, VirtualConsole} from 'jsdom';

const ROOT=fileURLToPath(new URL('../../services/vote/static/',import.meta.url));
const ORIGIN='https://vote.billfan.cn';
const PASSWORD='test-only-dom-password';
const TOKEN='v'.repeat(43);
const clone=value=>JSON.parse(JSON.stringify(value));
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const errors=[];
process.on('unhandledRejection',error=>errors.push(error?.stack||String(error)));

async function until(predicate,label,timeout=3500){
  const end=Date.now()+timeout;
  while(Date.now()<end){if(predicate())return;await pause(10);}
  throw new Error('DOM wait timed out: '+label);
}

class MockApi {
  constructor(options={}){
    this.calls=[];this.streams=new Set();this.admin=Boolean(options.admin);
    this.revision=5;this.clock=Date.now();this.currentId='c_1';this.title='旦口喜剧大赛';
    this.me={id:'u_one',votes:options.votes||[],version:1,bannedUntil:0};
    this.contestants=[
      {id:'c_1',name:'姜饼',group:'新人组',order:0,status:'performing',voting:'open',epoch:1,published:false,rawVotes:2,adjustmentTotal:0,adjustments:[]},
      {id:'c_2',name:'小鱼',group:'公开组',order:1,status:'performed',voting:'locked',epoch:3,published:true,rawVotes:11,adjustmentTotal:1,adjustments:[{id:'a_1',delta:1,reason:'现场互动奖励',public:true,createdAt:this.clock}]},
      {id:'c_3',name:'阿北',group:'新人组',order:2,status:'upcoming',voting:'pending',epoch:0,published:false,rawVotes:0,adjustmentTotal:0,adjustments:[]}
    ];
    this.messages=[];this.audit=[];this.closed=false;
  }
  state(admin=false){
    return clone({revision:this.revision,streamId:'mock-process',serverTime:++this.clock,title:this.title,currentId:this.currentId,
      contestants:this.contestants.map(c=>({id:c.id,name:c.name,group:c.group,order:c.order,status:c.status,voting:c.voting,epoch:c.epoch,published:c.published,
        votes:admin||c.published?Math.max(0,c.rawVotes+c.adjustmentTotal):null,
        adjustments:admin?c.adjustments:c.published?c.adjustments.filter(a=>a.public).map(({public:_,...a})=>a):[],
        ...(admin?{rawVotes:c.rawVotes,adjustmentTotal:c.adjustmentTotal}:{})})),
      messages:this.messages.filter(m=>admin||!m.deleted).map(m=>admin?m:{id:m.id,text:m.text,highlight:m.highlight,createdAt:m.createdAt}),
      limits:{voteMs:50,messageMs:50,maxMessageLength:80},...(admin?{audit:this.audit}:{})});
  }
  snapshot(){return {...this.state(),me:clone(this.me)};}
  json(value,status=200){return new Response(JSON.stringify(value),{status,headers:{'content-type':'application/json'}});}
  fail(code,message,status=409,extra={}){return this.json({error:{code,message},...extra},status);}
  emit(type,data,admin=false){
    const frame=new TextEncoder().encode('event: '+type+'\ndata: '+JSON.stringify(data)+'\n\n');
    for(const item of this.streams){if(item.admin===admin&&!item.closed)item.controller.enqueue(frame);}
  }
  updateControl(){this.emit('state',this.state());this.emit('admin_state',this.state(true),true);}
  stream(admin,signal){
    const item={admin,closed:false,controller:null};
    const body=new ReadableStream({
      start:controller=>{
        item.controller=controller;this.streams.add(item);
        const initial=admin?this.state(true):this.snapshot();
        controller.enqueue(new TextEncoder().encode('event: '+(admin?'admin_state':'snapshot')+'\ndata: '+JSON.stringify(initial)+'\n\n'));
      },
      cancel:()=>{item.closed=true;this.streams.delete(item);}
    });
    const stop=()=>{if(!item.closed){item.closed=true;try{item.controller.close();}catch(_){}this.streams.delete(item);}};
    if(signal?.aborted)stop();else signal?.addEventListener('abort',stop,{once:true});
    return new Response(body,{status:200,headers:{'content-type':'text/event-stream'}});
  }
  async fetch(input,options={}){
    const url=new URL(String(input),ORIGIN);assert.equal(url.origin,ORIGIN,'All application requests stay same-origin');
    const method=options.method||'GET';const body=options.body?JSON.parse(options.body):null;
    this.calls.push({path:url.pathname,url:url.href,method,body,headers:options.headers});
    if(this.closed)throw new Error('Mock server closed');
    if(url.pathname==='/api/admin/state'&&this.holdInitialAdminProbe&&!this.probeHeld){
      this.probeHeld=true;
      const response=this.fail('admin_required','请重新登录',401);
      return new Promise(resolve=>{this.releaseInitialAdminProbe=()=>resolve(response);});
    }
    if(url.pathname==='/api/session')return this.json({token:TOKEN,userId:this.me.id,recoveryCode:TOKEN,restored:'token',snapshot:this.snapshot()});
    if(url.pathname==='/api/snapshot')return this.json(this.snapshot());
    if(url.pathname==='/api/events')return this.stream(false,options.signal);
    if(url.pathname.startsWith('/api/votes/')){
      const id=decodeURIComponent(url.pathname.split('/').at(-1));const c=this.contestants.find(c=>c.id===id);
      if(c.voting!=='open')return this.fail('vote_locked','该选手已经锁票',409,{state:this.state()});
      const before=this.me.votes.includes(id);
      this.me.votes=this.me.votes.filter(value=>value!==id);
      if(body.voted)this.me.votes.push(id);
      if(before!==body.voted){this.me.version++;c.rawVotes+=body.voted?1:-1;}
      this.emit('me',clone(this.me));
      return this.json({voted:body.voted,contestantId:id,me:clone(this.me),revision:this.revision,replayed:false});
    }
    if(url.pathname==='/api/messages'){
      const message={id:'m_'+(this.messages.length+1),text:body.text,highlight:false,createdAt:++this.clock,userId:this.me.id,deleted:false};
      this.messages.push(message);this.emit('messages',{messages:[message]});
      return this.json({message,replayed:false});
    }
    if(url.pathname==='/api/admin/session'){
      if(body.password!==PASSWORD)return this.fail('invalid_password','管理密码不正确',401);
      this.admin=true;return this.json({ok:true,state:this.state(true)});
    }
    if(url.pathname.startsWith('/api/admin/')&&!this.admin)return this.fail('admin_required','请重新登录',401);
    if(url.pathname==='/api/admin/state')return this.json(this.state(true));
    if(url.pathname==='/api/admin/events')return this.stream(true,options.signal);
    if(url.pathname==='/api/admin/logout'){this.admin=false;return this.json({ok:true});}
    if(url.pathname==='/api/admin/action')return this.action(body);
    throw new Error('Unexpected mock request '+method+' '+url.pathname);
  }
  action(body){
    if(this.conflictOnce){this.conflictOnce=false;this.revision++;return this.fail('revision_conflict','另一位管理员已更新',409,{state:this.state(true)});}
    assert.equal(body.expectedRevision,this.revision,'Mutations carry current revision');
    assert.ok(body.requestId?.length>=8,'Mutations carry a unique request id');
    const c=this.contestants.find(c=>c.id===body.contestantId);
    switch(body.action){
      case 'lock':c.voting='locked';c.epoch++;break;
      case 'open':c.voting='open';c.epoch++;break;
      case 'lock_all':for(const c of this.contestants)if(c.voting==='open'){c.voting='locked';c.epoch++;}break;
      case 'select':{
        const previous=this.contestants.find(c=>c.id===this.currentId);
        if(previous&&previous.id!==c.id){previous.status='performed';if(body.lockPrevious){previous.voting='locked';previous.epoch++;}}
        this.currentId=c.id;c.status='performing';break;
      }
      case 'set_status':c.status=body.status;if(this.currentId===c.id&&c.status!=='performing')this.currentId=null;break;
      case 'publish':for(const c of this.contestants)if(body.contestantIds.includes(c.id))c.published=body.visible;break;
      case 'upsert_contestant':case 'import_contestants':{
        const values=body.action==='import_contestants'?body.contestants:[body.contestant];
        for(const v of values){
          if(v.name.length>60||v.group.length>40)return this.fail('invalid_input','组别需为 1 至 40 个字符',422);
          const old=this.contestants.find(c=>c.id===v.id);
          if(old)Object.assign(old,v);
          else this.contestants.push({...v,id:'c_'+(this.contestants.length+1),status:'upcoming',voting:'pending',epoch:0,published:false,rawVotes:0,adjustmentTotal:0,adjustments:[]});
        }break;
      }
      case 'adjust':{
        const a={id:'a_'+(c.adjustments.length+1),delta:body.delta,reason:body.reason,public:body.public,createdAt:++this.clock};
        c.adjustmentTotal+=body.delta;c.adjustments.push(a);break;
      }
      case 'message':this.messages.push({id:'m_'+(this.messages.length+1),text:body.text,highlight:body.highlight??true,createdAt:++this.clock,userId:null,deleted:false});break;
      case 'delete_message':this.messages.find(m=>m.id===body.messageId).deleted=true;break;
      case 'ban':this.me.bannedUntil=body.seconds?Date.now()+body.seconds*1000:0;this.me.version++;this.emit('me',clone(this.me));break;
      case 'settings':this.title=body.title;break;
      case 'remove_contestant':this.contestants=this.contestants.filter(c=>c.id!==body.contestantId);break;
      default:throw new Error('Unimplemented action '+body.action);
    }
    this.revision++;this.audit.unshift({id:this.revision,action:body.action,detail:body,createdAt:++this.clock});
    this.updateControl();return this.json({ok:true,state:this.state(true),replayed:false});
  }
  close(){this.closed=true;for(const item of this.streams){item.closed=true;try{item.controller.close();}catch(_){}}this.streams.clear();}
}

async function fixture(page,{url,server=new MockApi()}={}){
  const localErrors=[];const vc=new VirtualConsole();
  vc.on('jsdomError',error=>localErrors.push(error.stack||String(error)));
  const dom=new JSDOM(await fs.readFile(path.join(ROOT,page+'.html'),'utf8'),{url:url||ORIGIN+(page==='index'?'/':'/'+page),runScripts:'outside-only',virtualConsole:vc});
  const w=dom.window;
  Object.defineProperty(w.document,'hidden',{value:false,writable:true,configurable:true});
  w.matchMedia=media=>({matches:false,media,addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}});
  w.BroadcastChannel=class {postMessage(){}close(){}};
  w.TextEncoder=TextEncoder;w.TextDecoder=TextDecoder;w.Response=Response;w.ReadableStream=ReadableStream;
  w.fetch=(...args)=>server.fetch(...args);
  let clipboard='';Object.defineProperty(w.navigator,'clipboard',{value:{writeText:async value=>{clipboard=value;}}});
  w.addEventListener('error',event=>localErrors.push(event.error?.stack||event.message));
  w.addEventListener('unhandledrejection',event=>localErrors.push(event.reason?.stack||String(event.reason)));
  const context=dom.getInternalVMContext(), modules=new Map();
  async function load(file){
    if(modules.has(file))return modules.get(file);
    const module=new vm.SourceTextModule(await fs.readFile(file,'utf8'),{context,identifier:file});modules.set(file,module);
    await module.link((specifier,reference)=>load(path.resolve(path.dirname(reference.identifier),specifier.split('?')[0])));
    return module;
  }
  await (await load(path.join(ROOT,page==='admin'?'admin.js':'app.js'))).evaluate();
  const $=selector=>w.document.querySelector(selector), $$=selector=>[...w.document.querySelectorAll(selector)];
  const click=selector=>{const element=typeof selector==='string'?$(selector):selector;assert.ok(element,'click target exists');element.click();};
  const input=(selector,value)=>{const e=$(selector);e.value=value;e.dispatchEvent(new w.Event('input',{bubbles:true}));};
  const change=selector=>$(selector).dispatchEvent(new w.Event('change',{bubbles:true}));
  const submit=selector=>$(selector).dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
  const clean=()=>{
    w.document.hidden=true;w.document.dispatchEvent(new w.Event('visibilitychange'));server.close();dom.window.close();
    assert.deepEqual(localErrors,[],'No DOM runtime errors');
  };
  return {w,$,$$,click,input,change,submit,server,clean,localErrors,get clipboard(){return clipboard;}};
}

test('public vote page: initial SSE, vote, cancel, broadcast, lock, ban, recovery link',async()=>{
  const f=await fixture('index');
  try{
    await until(()=>!f.$('#vote-button').disabled,'initial vote button enabled');
    assert.equal(f.$('#performer-name').textContent,'姜饼');assert.equal(f.$('#round-number').textContent,'NO. 01');
    f.click('#vote-button');assert.equal(f.$('#vote-button').disabled,true,'Pending write disables duplicate click');
    await until(()=>f.$('#vote-label').textContent.includes('已投票'),'affirmative vote rendered');
    assert.deepEqual(f.server.me.votes,['c_1']);
    await until(()=>!f.$('#vote-button').disabled,'vote throttle clears');f.click('#vote-button');
    await until(()=>f.server.me.votes.length===0&&f.$('#vote-label').textContent==='投 TA 一票','cancel rendered');
    f.input('#message-input','<img src=x onerror=alert(1)>');f.submit('#message-form');
    await until(()=>f.$('#message-list').textContent.includes('<img src=x'),'message in DOM as text');
    assert.equal(f.$$('#message-list img').length,0,'User markup is not interpreted');
    f.server.messages.push({id:'m_admin',text:'全场准备，马上锁票',highlight:true,createdAt:++f.server.clock,userId:null,deleted:false});
    f.server.emit('messages',{messages:[f.server.messages.at(-1)]});
    await until(()=>!f.$('#admin-announcement').hidden,'highlight visible');
    f.server.contestants[0].voting='locked';f.server.contestants[0].epoch++;f.server.revision++;f.server.updateControl();
    await until(()=>f.$('#vote-label').textContent==='本轮已锁票','lock reaches voting DOM');
    assert.equal(f.$('#vote-button').disabled,true);
    f.server.me.bannedUntil=Date.now()+60000;f.server.me.version++;f.server.emit('me',clone(f.server.me));
    await until(()=>f.$('#send-message').textContent==='禁言中','ban reaches composer');
    f.click('.identity-help');assert.equal(f.$('#identity-dialog').hidden,false);f.click('#copy-recovery');
    await until(()=>f.clipboard.includes('/#restore='),'recovery copied');assert.ok(f.clipboard.endsWith(TOKEN));
    f.click('#identity-dialog .modal-close');assert.equal(f.$('#identity-dialog').hidden,true);
  }finally{f.clean();}
});

test('players page: statuses, my votes, search/filter, inline vote and public reason',async()=>{
  const f=await fixture('players',{server:new MockApi({votes:['c_2']})});
  try{
    await until(()=>f.$$('.player-card').length===3,'all contestant cards');
    assert.equal(f.$('#count-all').textContent,'3');assert.equal(f.$('#count-performed').textContent,'1');assert.equal(f.$('#count-mine').textContent,'1');
    assert.ok(f.$('#players-list').textContent.includes('现场互动奖励'));
    f.click('[data-filter="mine"]');assert.equal(f.$$('.player-card').length,1);assert.equal(f.$('.player-text h2').textContent,'小鱼');
    f.click('[data-filter="open"]');assert.equal(f.$$('.player-card').length,1);assert.equal(f.$('.player-text h2').textContent,'姜饼');
    f.input('#player-search','不存在');assert.equal(f.$$('.player-card').length,0);
    f.input('#player-search','新人组');await until(()=>!f.$('[data-vote-id="c_1"]').disabled,'inline button enabled');
    f.click('[data-vote-id="c_1"]');await until(()=>f.$('#count-mine').textContent==='2','inline vote counted');
    assert.ok(f.$('.player-my-state').textContent.includes('我已投票'));
    f.server.contestants[0].voting='locked';f.server.revision++;f.server.updateControl();
    await until(()=>f.$$('.player-card').length===0,'open filter tracks lock');
    f.click('[data-filter="all"]');f.input('#player-search','');
    assert.equal(f.$('[data-vote-id="c_1"]').disabled,true);
  }finally{f.clean();}
});

test('admin page: manual login, initial rendering, immediate lock, confirmed reopen, import and publish',async()=>{
  const server=new MockApi();server.holdInitialAdminProbe=true;
  const f=await fixture('admin',{server});
  try{
    await until(()=>typeof server.releaseInitialAdminProbe==='function','initial authentication probe held');
    f.input('#admin-password',PASSWORD);f.submit('#login-form');
    await until(()=>server.calls.some(c=>c.path==='/api/admin/session'),'manual login supersedes initial probe');
    server.releaseInitialAdminProbe();
    await until(()=>!f.$('#admin-main').hidden&&!f.$('#lock-voting').disabled,'admin authenticated and live');
    assert.equal(f.$('#admin-password').value,'');assert.equal(f.$$('.admin-contestant').length,3);
    f.click('#lock-voting');await until(()=>f.$('#lock-voting').textContent==='本轮已锁票','lock action rendered');
    assert.equal(f.server.contestants[0].voting,'locked');
    f.click('#open-voting');assert.equal(f.$('#confirm-dialog').hidden,false);f.click('#confirm-submit');
    await until(()=>!f.$('#lock-voting').disabled,'reopened after confirmation');
    f.click('#import-contestants');assert.equal(f.$('#import-dialog').hidden,false);
    f.input('#import-input','新甲,决赛组\n新乙\t新人组');f.submit('#import-form');
    await until(()=>f.$$('.admin-contestant').length===5&&f.$('#import-dialog').hidden,'two imported contestants rendered');
    const imported=f.server.calls.filter(c=>c.body?.action==='import_contestants').at(-1).body.contestants;
    assert.deepEqual(imported.map(c=>[c.name,c.group,c.order]),[['新甲','决赛组',3],['新乙','新人组',4]]);
    f.$('#select-all').checked=true;f.change('#select-all');f.click('#publish-selected');
    await until(()=>f.server.contestants.every(c=>c.published),'publish selection');
    assert.ok(f.$('#admin-contestants').textContent.includes('已公布票数'));
  }finally{f.clean();}
});

test('admin contestant group limit agrees with API: 40 allowed, 41 rejected before import',async()=>{
  const f=await fixture('admin',{server:new MockApi({admin:true})});
  try{
    await until(()=>!f.$('#lock-voting').disabled,'admin live for validation');
    assert.equal(f.$('#contestant-group').maxLength,40);
    f.click('#import-contestants');f.input('#import-input','新选手,'+'甲'.repeat(41));f.submit('#import-form');
    await until(()=>f.$('#toast').textContent.includes('组别最多 40'),'group validation message');
    assert.equal(f.server.calls.filter(c=>c.body?.action==='import_contestants').length,0);
    assert.equal(f.$('#import-dialog').hidden,false);
    f.input('#import-input','新选手,'+'甲'.repeat(40));f.submit('#import-form');
    await until(()=>f.$$('.admin-contestant').length===4&&f.$('#import-dialog').hidden,'40-character group accepted');
    assert.equal(f.server.contestants.at(-1).group.length,40);
  }finally{f.clean();}
});

test('admin page: hash login strips credential; adjust, message/delete, ban, logout handlers',async()=>{
  const server=new MockApi();server.messages=[{id:'m_user',text:'现场好开心',highlight:false,createdAt:++server.clock,userId:'u_one',deleted:false}];
  const f=await fixture('admin',{url:ORIGIN+'/admin#key='+encodeURIComponent(PASSWORD),server});
  try{
    await until(()=>!f.$('#admin-main').hidden&&!f.$('#lock-voting').disabled,'hash login connected');
    assert.equal(f.w.location.hash,'');assert.equal(f.w.location.search,'');
    assert.ok(f.server.calls.every(c=>!c.url.includes(PASSWORD)),'Credential never in request URL');
    f.click('[data-tab="adjust"]');assert.equal(f.$('#panel-adjust').hidden,false);
    f.$('#adjust-contestant').value='c_1';f.change('#adjust-contestant');f.input('#adjust-delta','3');f.input('#adjust-reason','现场互动');
    f.submit('#adjust-form');assert.equal(f.$('#confirm-dialog').hidden,false);f.click('#confirm-submit');
    await until(()=>f.server.contestants[0].adjustmentTotal===3&&f.$('#adjust-detail').textContent.includes('现场互动'),'public adjustment rendered');
    const radio=f.$('input[name="adjust-public"][value="hidden"]');radio.checked=true;f.change('input[name="adjust-public"][value="hidden"]');
    assert.equal(f.$('#adjust-reason').required,false);
    f.click('[data-tab="messages"]');f.input('#admin-message-text','即将锁票');f.submit('#admin-message-form');
    await until(()=>f.$('#admin-messages').textContent.includes('即将锁票'),'admin announcement rendered');
    const userCard=f.$$('.admin-message').find(c=>c.textContent.includes('现场好开心'));
    f.click([...userCard.querySelectorAll('button')].find(b=>b.textContent==='禁言…'));assert.equal(f.$('#ban-dialog').hidden,false);
    f.$('#ban-seconds').value='300';f.submit('#ban-form');await until(()=>f.$('#ban-dialog').hidden,'ban saved');assert.ok(f.server.me.bannedUntil>Date.now());
    const announcement=f.$$('.admin-message').find(c=>c.textContent.includes('即将锁票'));
    f.click([...announcement.querySelectorAll('button')].find(b=>b.textContent==='删除弹幕'));
    await until(()=>!f.$('#admin-messages').textContent.includes('即将锁票'),'announcement removed');
    f.click('#logout');await until(()=>!f.$('#login-view').hidden&&f.$('#admin-main').hidden,'logout leaves admin view');
    assert.equal(f.server.admin,false);
  }finally{f.clean();}
});

test('admin revision conflict refreshes controls and enables subsequent action',async()=>{
  const server=new MockApi({admin:true});const f=await fixture('admin',{server});
  try{
    await until(()=>!f.$('#lock-voting').disabled,'admin live');
    server.conflictOnce=true;f.click('#lock-voting');
    await until(()=>f.$('#toast').textContent.includes('其他管理员'),'conflict notice');
    assert.equal(f.$('#stat-revision').textContent,String(server.revision));assert.equal(f.$('#lock-voting').disabled,false);
    f.click('#lock-voting');await until(()=>server.contestants[0].voting==='locked','lock can retry after conflict');
  }finally{f.clean();}
});

test('no unhandled asynchronous rejections across DOM interactions',async()=>{
  await pause(30);assert.deepEqual(errors,[]);
});
