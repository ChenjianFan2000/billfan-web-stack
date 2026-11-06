/* Same-origin API, redundant anonymous identity, and one SSE stream per visible page. */
const TOKEN_KEY = 'dankou.vote.identity.v1';
const HINT_KEY = 'dankou.vote.identityHint.v1';
const saved = (storage, key) => { try { return storage.getItem(key); } catch (_) { return null; } };
const save = (storage, key, value) => { try { storage.setItem(key, value); return true; } catch (_) { return false; } };
const local = () => { try { return window.localStorage; } catch (_) { return null; } };
const session = () => { try { return window.sessionStorage; } catch (_) { return null; } };
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
export const requestId = () => {
  if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
  if (window.crypto && crypto.getRandomValues) return Array.from(crypto.getRandomValues(new Uint8Array(16)), v => v.toString(16).padStart(2, '0')).join('');
  return Date.now().toString(36) + Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2);
};

function idb(mode, value, key = 'token') {
  return Promise.race([new Promise(resolve => {
    try {
      const open = indexedDB.open('dankou-vote', 1);
      open.onupgradeneeded = () => open.result.createObjectStore('identity');
      open.onerror = () => resolve(null);
      open.onblocked = () => resolve(null);
      open.onsuccess = () => {
        const db = open.result;
        const tx = db.transaction('identity', mode === 'read' ? 'readonly' : 'readwrite');
        const req = mode === 'read' ? tx.objectStore('identity').get(key) : tx.objectStore('identity').put(value, key);
        req.onsuccess = () => resolve(mode === 'read' ? req.result : true);
        req.onerror = () => resolve(null);
        tx.oncomplete = () => db.close();
        tx.onerror = () => { db.close(); resolve(null); };
      };
    } catch (_) { resolve(null); }
  }), delay(700).then(() => null)]);
}

async function fingerprint() {
  try {
    if (!window.crypto || !crypto.subtle) return {};
    const canvas = document.createElement('canvas');
    canvas.width = 240; canvas.height = 64;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#991401'; ctx.fillRect(3, 3, 176, 43);
    ctx.fillStyle = '#ffd766'; ctx.font = '17px sans-serif';
    ctx.fillText('旦口喜剧 / DANKOU 2026', 8, 28);
    ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = '#f76a5c';
    ctx.beginPath(); ctx.arc(185, 35, 22, 0, 2 * Math.PI); ctx.fill();
    const glCanvas = document.createElement('canvas');
    const gl = glCanvas.getContext('webgl') || glCanvas.getContext('experimental-webgl');
    let renderer = '', caps = [];
    if (gl) {
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      renderer = ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : String(gl.getParameter(gl.RENDERER));
      caps = [gl.getParameter(gl.MAX_TEXTURE_SIZE), gl.getParameter(gl.MAX_RENDERBUFFER_SIZE), gl.getParameter(gl.MAX_VERTEX_ATTRIBS)];
      const lose = gl.getExtension('WEBGL_lose_context'); if (lose) lose.loseContext();
    }
    const source = JSON.stringify({v: 1, canvas: canvas.toDataURL(), renderer, caps,
      screen: [screen.width, screen.height].sort((a,b) => a-b), depth: screen.colorDepth,
      ratio: devicePixelRatio, platform: navigator.platform, language: navigator.language,
      cores: navigator.hardwareConcurrency || 0, touch: navigator.maxTouchPoints || 0,
      zone: Intl.DateTimeFormat().resolvedOptions().timeZone});
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(source));
    return {fingerprint: Array.from(new Uint8Array(digest), n => n.toString(16).padStart(2, '0')).join(''),
      fingerprintVersion: 'v1', fingerprintQualified: Boolean(gl && renderer && ctx)};
  } catch (_) { return {}; }
}

export class ApiError extends Error {
  constructor(response, body) {
    super(body?.error?.message || body?.detail || '请求未完成，请稍后再试');
    this.status = response.status; this.code = body?.error?.code; this.body = body;
    this.retryAfterMs = Number(body?.retryAfterMs || body?.error?.retryAfterMs || response.headers.get('Retry-After') * 1000 || 0);
  }
}

export class VoteClient extends EventTarget {
  constructor(admin = false) {
    super(); this.admin = admin; this.token = ''; this.recoveryCode = '';
    this.state = null; this.connection = 'connecting'; this.live = false;
    this.retry = 0; this.stream = null; this.timer = null; this.lastEvent = 0;
    this.stopped = false; this.generation = 0; this.pending = new Set();
    this.nextVoteAt = 0; this.nextMessageAt = 0;
    this.serverOffset = 0;
    this.identityEpoch = 0;
    this.deletedMessages = new Set();
    this.identityChannel = null;
    if (!admin) {
      try {
        this.identityChannel = new BroadcastChannel('dankou-vote-identity');
        this.identityChannel.onmessage = event => {
          if (event.data?.token && event.data.token !== this.token) this.adoptIdentity(event.data.token);
        };
      } catch (_) { /* Storage events still synchronize tabs in older browsers. */ }
      window.addEventListener('storage', event => {
        if (event.key === TOKEN_KEY && event.newValue && event.newValue !== this.token) this.adoptIdentity(event.newValue);
      });
    }
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) { this.stopStream(); this.setConnection('paused'); }
      else this.resume();
    });
    window.addEventListener('pagehide', () => this.stopStream());
    window.addEventListener('pageshow', event => { if (event.persisted) this.resume(); });
    window.addEventListener('offline', () => { this.stopStream(); this.setConnection('offline'); });
    window.addEventListener('online', () => this.resume());
  }
  emit(type, detail) { this.dispatchEvent(new CustomEvent(type, {detail})); }
  now() { return Date.now() + this.serverOffset; }
  setConnection(value) { this.connection = value; this.live = value === 'live' || value === 'polling'; this.emit('connection', value); }
  async api(path, options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);
    const headers = {'Accept': 'application/json', ...options.headers};
    if (options.body) headers['Content-Type'] = 'application/json';
    if (this.token && !this.admin) headers.Authorization = 'Bearer ' + this.token;
    try {
      const response = await fetch(path, {...options, headers, credentials: 'same-origin', cache: 'no-store', signal: controller.signal});
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new ApiError(response, body);
      return body;
    } finally { clearTimeout(timeout); }
  }
  accept(state) {
    if (!state) return;
    const previous = this.state;
    if (previous && state.streamId === previous.streamId) {
      let me = previous.me;
      if (state.me && (!me || (state.me.id === me.id && (state.me.version || 0) >= (me.version || 0)))) me = state.me;
      const older = state.revision < previous.revision || (state.revision === previous.revision && state.serverTime < previous.serverTime);
      if (!this.admin && !older && state.revision === previous.revision && state.messages && previous.messages) {
        const known = new Set(state.messages.map(message => message.id));
        // Chat does not change the control revision. Keep messages created after an in-flight snapshot was read.
        state = {...state, messages:[...state.messages, ...previous.messages.filter(message => !known.has(message.id) && message.createdAt >= state.serverTime)].slice(-60)};
      }
      state = {...(older ? previous : state), ...(me ? {me} : {})};
    }
    if (!this.admin && state.messages) state = {...state, messages:state.messages.filter(message => !this.deletedMessages.has(message.id))};
    if (state.serverTime && state.serverTime !== previous?.serverTime) this.serverOffset = state.serverTime - Date.now();
    this.state = state;
    this.emit('change', state);
  }
  async start(recoveryCode = '') {
    this.stopStream(); this.setConnection('connecting');
    if (this.admin) { await this.refresh(); this.connect(); return; }
    const boot = async () => {
      const candidates = [saved(local(), TOKEN_KEY), saved(session(), TOKEN_KEY), await idb('read')];
      const tokens = Array.from(new Set(candidates.filter(v => typeof v === 'string' && v.length >= 20 && v.length <= 512)));
      const identityHint = saved(local(), HINT_KEY) || saved(session(), HINT_KEY) || await idb('read', undefined, 'hint') || undefined;
      const device = await fingerprint();
      const result = await this.api('/api/session', {method: 'POST', body: JSON.stringify({tokens, identityHint, ...device, ...(recoveryCode ? {recoveryCode} : {})})});
      if (this.state?.me?.id !== result.userId) { ++this.identityEpoch; this.state = null; }
      this.token = result.token; this.recoveryCode = result.recoveryCode;
      save(local(), TOKEN_KEY, result.token); save(session(), TOKEN_KEY, result.token);
      save(local(), HINT_KEY, result.userId); save(session(), HINT_KEY, result.userId);
      await idb('write', result.token);
      await idb('write', result.userId, 'hint');
      this.accept(result.snapshot); this.emit('identity', {restored: result.restored, userId: result.userId});
      this.identityChannel?.postMessage({token: result.token});
    };
    // A supported Web Lock prevents two newly opened tabs from issuing separate identities.
    if (navigator.locks?.request) await navigator.locks.request('dankou-identity', boot);
    else await boot();
    this.connect();
  }
  async adoptIdentity(token) {
    if (this.adopting || token === this.token || typeof token !== 'string' || token.length > 512) return;
    this.adopting = true; this.stopStream(); this.setConnection('connecting');
    try {
      const result = await this.api('/api/session', {method:'POST', body:JSON.stringify({recoveryCode:token})});
      ++this.identityEpoch; this.state = null; this.token = result.token; this.recoveryCode = result.recoveryCode;
      save(local(), TOKEN_KEY, result.token);
      save(session(), TOKEN_KEY, result.token); save(session(), HINT_KEY, result.userId);
      save(local(), HINT_KEY, result.userId);
      await idb('write', result.token); await idb('write', result.userId, 'hint');
      this.accept(result.snapshot); this.emit('identity', {restored:true,userId:result.userId});
    } catch (_) { this.emit('identity-error', null); }
    finally { this.adopting=false; this.connect(); }
  }
  async login(password) {
    await this.api('/api/admin/session', {method: 'POST', body: JSON.stringify({password})});
    await this.start();
  }
  async refresh() {
    const identityEpoch = this.identityEpoch;
    const result = await this.api(this.admin ? '/api/admin/state' : '/api/snapshot');
    if (identityEpoch === this.identityEpoch) this.accept(result);
    return this.state;
  }
  stopStream() {
    ++this.generation; clearTimeout(this.timer); this.timer = null;
    if (this.stream) this.stream.abort(); this.stream = null;
    if (this.nativeStream) this.nativeStream.close(); this.nativeStream = null;
    this.live = false;
  }
  resume() {
    if (!this.state || this.stopped || document.hidden) return;
    this.stopStream(); this.setConnection('connecting');
    // Every visible return receives a new authoritative snapshot at the start of its stream.
    this.timer = setTimeout(() => this.connect(), 80 + Math.random() * 350);
  }
  consume(type, data) {
    this.lastEvent = Date.now(); this.retry = 0;
    if (data.serverTime) this.serverOffset = data.serverTime - Date.now();
    if (type === 'snapshot' || type === 'admin_state') { this.accept(data); this.setConnection('live'); }
    else if (type === 'state') this.accept({...data, me: this.state?.me});
    else if (type === 'counts' && this.state && data.streamId === this.state.streamId && data.revision === this.state.revision && data.serverTime >= this.state.serverTime) {
      const counts = new Map((data.counts || []).map(item => [item.id, item.votes]));
      this.accept({...this.state, serverTime:data.serverTime, contestants:this.state.contestants.map(c => c.published && counts.has(c.id) ? {...c,votes:counts.get(c.id)} : c)});
    }
    else if (type === 'me' && this.state) {
      if (!this.state.me || (data.id === this.state.me.id && (data.version || 0) >= (this.state.me.version || 0))) this.accept({...this.state, me: data});
    } else if (type === 'messages' && this.state) {
      const known = new Set((this.state.messages || []).map(m => m.id));
      const fresh = (data.messages || []).filter(m => !known.has(m.id) && !this.deletedMessages.has(m.id));
      const messages = [...(this.state.messages || []), ...fresh].slice(-60);
      this.accept({...this.state, messages}); this.emit('messages', fresh);
    } else if (type === 'message_deleted' && this.state) {
      this.deletedMessages.add(data.id);
      if (this.deletedMessages.size > 2000) this.deletedMessages.delete(this.deletedMessages.values().next().value);
      this.accept({...this.state, messages: (this.state.messages || []).filter(m => m.id !== data.id)});
      this.emit('deleted', data.id);
    } else if (type === 'resync') this.resume();
  }
  async connect() {
    if (document.hidden || this.stopped || !this.state) return;
    this.stopStream();
    if (!navigator.onLine) { this.setConnection('offline'); return; }
    const generation = this.generation;
    const controller = new AbortController(); this.stream = controller;
    this.setConnection('connecting'); this.lastEvent = Date.now();
    const handshakeTimeout = setTimeout(() => controller.abort(), 15000);
    let watchdog;
    try {
      const headers = {'Accept': 'text/event-stream'};
      if (!this.admin && this.token) headers.Authorization = 'Bearer ' + this.token;
      const response = await fetch(this.admin ? '/api/admin/events' : '/api/events', {headers, credentials:'same-origin', cache:'no-store', signal: controller.signal});
      clearTimeout(handshakeTimeout);
      if (generation !== this.generation) return;
      if (!response.ok) throw new ApiError(response, await response.json().catch(() => ({})));
      if (!response.body?.getReader) {
        controller.abort();
        if (typeof EventSource !== 'undefined') await this.nativeEvents(generation);
        else await this.poll(generation);
        return;
      }
      const reader = response.body.getReader(), decoder = new TextDecoder();
      let buffer = '';
      watchdog = setInterval(() => { if (Date.now() - this.lastEvent > 55000) controller.abort(); }, 10000);
      while (generation === this.generation) {
        const {done, value} = await reader.read(); if (done) break;
        if (generation !== this.generation) break;
        buffer += decoder.decode(value, {stream: true});
        if (buffer.length > 1000000) throw new Error('同步数据异常');
        buffer = buffer.replace(/\r\n/g, '\n');
        let boundary;
        while ((boundary = buffer.indexOf('\n\n')) >= 0) {
          const block = buffer.slice(0, boundary); buffer = buffer.slice(boundary + 2);
          let type = 'message', payload = [];
          for (const line of block.split('\n')) {
            if (line.startsWith('event:')) type = line.slice(6).trim();
            if (line.startsWith('data:')) payload.push(line.slice(5).trimStart());
          }
          if (payload.length) this.consume(type, JSON.parse(payload.join('\n')));
          else this.lastEvent = Date.now();
        }
      }
    } catch (error) {
      if (generation === this.generation && error.status === 401) { this.emit('expired', null); this.stopped = this.admin; }
    } finally {
      clearTimeout(handshakeTimeout);
      clearInterval(watchdog);
      if (generation === this.generation && !this.stopped && !document.hidden) {
        this.setConnection(navigator.onLine ? 'reconnecting' : 'offline');
        const backoff = Math.min(15000, 700 * 2 ** Math.min(this.retry++, 5));
        this.timer = setTimeout(() => this.connect(), backoff * (.7 + Math.random() * .6));
      }
    }
  }
  nativeEvents(generation) {
    return new Promise(resolve => {
      const stream = new EventSource(this.admin ? '/api/admin/events' : '/api/events');
      this.nativeStream = stream;
      const watchdog = setInterval(() => {
        if (generation !== this.generation || Date.now() - this.lastEvent > 55000) { clearInterval(watchdog); stream.close(); resolve(); }
      }, 5000);
      for (const type of ['snapshot','admin_state','state','counts','me','messages','message_deleted','heartbeat','resync']) {
        stream.addEventListener(type, event => { if(generation === this.generation) this.consume(type,JSON.parse(event.data)); });
      }
      stream.onerror = () => { clearInterval(watchdog); stream.close(); this.poll(generation).then(resolve,resolve); };
    });
  }
  async poll(generation) {
    while (generation === this.generation && !document.hidden && !this.stopped) {
      try { await this.refresh(); }
      catch (error) {
        if (generation === this.generation && error.status === 401) { this.emit('expired', null); this.stopped = this.admin; }
        throw error;
      }
      if (generation !== this.generation) return;
      this.setConnection('polling');
      await delay(14000 + Math.random() * 3000);
    }
  }
  async vote(contestant, voted) {
    if (!this.live || this.pending.size || Date.now() < this.nextVoteAt) return false;
    const identityEpoch = this.identityEpoch;
    this.pending.add(contestant.id); this.emit('change', this.state);
    try {
      const result = await this.api('/api/votes/' + encodeURIComponent(contestant.id), {method:'PUT',body:JSON.stringify({voted, epoch:contestant.epoch, requestId:requestId()})});
      if (identityEpoch !== this.identityEpoch) return false;
      // A simultaneous tab may have produced a newer me event while this request was in flight.
      if (result.me && result.me.id === this.state?.me?.id && (result.me.version || 0) >= (this.state.me.version || 0)) this.accept({...this.state, me:result.me});
      this.nextVoteAt = Date.now() + (this.state.limits?.voteMs || 800);
      return true;
    } catch (error) {
      if (error.retryAfterMs) this.nextVoteAt = Date.now() + error.retryAfterMs;
      await this.refresh().catch(() => this.setConnection('reconnecting'));
      throw error;
    } finally {
      this.pending.delete(contestant.id); this.emit('change', this.state);
      setTimeout(() => this.emit('change', this.state), Math.max(50, this.nextVoteAt - Date.now() + 30));
    }
  }
  async message(text) {
    const result = await this.api('/api/messages', {method:'POST',body:JSON.stringify({text, requestId:requestId()})});
    this.nextMessageAt = Date.now() + (this.state.limits?.messageMs || 5000);
    if (result.message) this.consume('messages', {messages:[result.message]});
    return result;
  }
  async action(action, values = {}) {
    const result = await this.api('/api/admin/action', {method:'POST',body:JSON.stringify({action,...values,expectedRevision:this.state.revision,requestId:requestId()})});
    this.accept(result.state); return result;
  }
}

export function storedPreference(key, fallback) { return saved(local(), 'dankou.pref.' + key) ?? fallback; }
export function setPreference(key, value) { save(local(), 'dankou.pref.' + key, value); }
