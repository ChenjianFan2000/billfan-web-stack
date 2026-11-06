import test from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {setMaxListeners} from 'node:events';

globalThis.document=new EventTarget();
document.hidden=false;
globalThis.window=new EventTarget();
// The test fixture shares browser targets across isolated client instances.
setMaxListeners(32, document, window);
window.crypto=webcrypto;
globalThis.BroadcastChannel=class {postMessage(){} close(){}};
Object.defineProperty(globalThis,'navigator',{value:{onLine:true},configurable:true});
const {VoteClient}=await import('../services/vote/static/api.js');
const snapshot=(options={})=>({
  revision:1,streamId:'server-a',serverTime:1000,title:'测试',currentId:'c',
  contestants:[{id:'c',name:'测试选手',order:0,epoch:2,voting:'open',published:true,votes:1}],
  messages:[],limits:{voteMs:1,messageMs:5000},
  me:{id:'u',version:1,votes:[],bannedUntil:0},...options
});
function makeClient(){
  const c=new VoteClient();c.connect=()=>{};c.accept(snapshot());c.setConnection('live');return c;
}

test('late snapshot cannot roll back a newer personal vote',()=>{
  const c=makeClient();
  c.consume('me',{id:'u',version:3,votes:['c'],bannedUntil:0});
  c.accept(snapshot({serverTime:1200,me:{id:'u',version:2,votes:[],bannedUntil:0}}));
  assert.deepEqual(c.state.me.votes,['c']);
  assert.equal(c.state.me.version,3);
});

test('stale control snapshot cannot reopen a locked contestant',()=>{
  const c=makeClient();
  c.accept(snapshot({revision:2,serverTime:1300,contestants:[{...c.state.contestants[0],voting:'locked',epoch:3}]}));
  c.accept(snapshot({serverTime:1400}));
  assert.equal(c.state.revision,2);
  assert.equal(c.state.contestants[0].voting,'locked');
});

test('same-revision snapshots and counts respect server time',()=>{
  const c=makeClient();
  c.consume('counts',{revision:1,streamId:'server-a',serverTime:1300,counts:[{id:'c',votes:9}]});
  c.accept(snapshot({serverTime:1200}));
  assert.equal(c.state.contestants[0].votes,9);
  c.consume('counts',{revision:1,streamId:'server-a',serverTime:1250,counts:[{id:'c',votes:2}]});
  assert.equal(c.state.contestants[0].votes,9);
});

test('count updates cannot reveal unpublished counts or cross a control epoch',()=>{
  const c=makeClient();
  c.accept(snapshot({serverTime:1300,contestants:[{...c.state.contestants[0],published:false,votes:null}]}));
  c.consume('counts',{revision:1,streamId:'server-a',serverTime:1400,counts:[{id:'c',votes:8}]});
  assert.equal(c.state.contestants[0].votes,null);
  c.consume('counts',{revision:2,streamId:'server-a',serverTime:1500,counts:[{id:'c',votes:20}]});
  assert.equal(c.state.revision,1);
});

test('late response from identity A cannot overwrite restored identity B',async()=>{
  const c=makeClient();
  let finish;
  c.api=()=>new Promise(resolve=>{finish=resolve;});
  const request=c.vote(c.state.contestants[0],true);
  ++c.identityEpoch;c.state=null;
  c.accept(snapshot({me:{id:'other',version:1,votes:[],bannedUntil:0}}));
  finish({me:{id:'u',version:99,votes:['c'],bannedUntil:0},voted:true});
  assert.equal(await request,false);
  assert.equal(c.state.me.id,'other');
  assert.deepEqual(c.state.me.votes,[]);
});

test('private SSE from another identity is ignored',()=>{
  const c=makeClient();
  c.consume('me',{id:'other',version:100,votes:['c'],bannedUntil:0});
  assert.equal(c.state.me.id,'u');
  assert.deepEqual(c.state.me.votes,[]);
});

test('snapshot started before identity change cannot overwrite the new identity',async()=>{
  const c=makeClient();let finish;c.api=()=>new Promise(resolve=>{finish=resolve;});
  const request=c.refresh();++c.identityEpoch;c.state=null;
  c.accept(snapshot({me:{id:'other',version:2,votes:['c'],bannedUntil:0}}));
  finish(snapshot({serverTime:2000}));
  await request;
  assert.equal(c.state.me.id,'other');
  assert.deepEqual(c.state.me.votes,['c']);
});

test('simultaneous clicks make one request and preserve affirmative semantics',async()=>{
  const c=makeClient();let calls=0,finish;
  c.api=(path,options)=>{calls++;assert.equal(JSON.parse(options.body).voted,true);return new Promise(resolve=>{finish=resolve;});};
  const first=c.vote(c.state.contestants[0],true);
  assert.equal(await c.vote(c.state.contestants[0],true),false);
  finish({me:{id:'u',version:2,votes:['c'],bannedUntil:0},voted:true});
  assert.equal(await first,true);assert.equal(calls,1);
  assert.deepEqual(c.state.me.votes,['c']);
});

test('message batches deduplicate and deletions remove the displayed item',()=>{
  const c=makeClient(),m={id:'m',text:'好笑',highlight:false,createdAt:1001};
  c.consume('messages',{messages:[m]});c.consume('messages',{messages:[m]});
  assert.equal(c.state.messages.length,1);
  c.consume('message_deleted',{id:'m'});
  assert.equal(c.state.messages.length,0);
});

test('new server stream accepts its authoritative snapshot after restart',()=>{
  const c=makeClient();
  c.accept(snapshot({revision:20}));
  c.accept(snapshot({revision:2,streamId:'server-b',serverTime:3000}));
  assert.equal(c.state.streamId,'server-b');
  assert.equal(c.state.revision,2);
});

test('late message POST response cannot resurrect a deleted message',()=>{
  const c=makeClient(),m={id:'removed',text:'已删除',highlight:false,createdAt:1100};
  c.consume('messages',{messages:[m]});
  c.consume('message_deleted',{id:m.id});
  c.consume('messages',{messages:[m]});
  assert.equal(c.state.messages.length,0);
});

test('late snapshot retains newer chat even without a control revision change',()=>{
  const c=makeClient(),m={id:'new',text:'新的弹幕',highlight:false,createdAt:1400};
  c.consume('messages',{messages:[m]});
  c.accept(snapshot({serverTime:1300}));
  assert.equal(c.state.messages.length,1);
  assert.equal(c.state.messages[0].id,'new');
});

