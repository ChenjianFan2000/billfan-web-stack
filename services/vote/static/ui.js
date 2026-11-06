export const $ = (selector, parent = document) => parent.querySelector(selector);
export const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];
export function node(tag, classes, text) {
  const element = document.createElement(tag);
  if (classes) element.className = classes;
  if (text !== undefined) element.textContent = String(text);
  return element;
}
export function button(text, classes, handler) {
  const element = node('button', classes, text); element.type = 'button';
  if (handler) element.addEventListener('click', handler); return element;
}
let toastTimer;
export function toast(message, duration = 4500) {
  const box = $('#toast'); if (!box) return;
  clearTimeout(toastTimer); box.textContent = message; box.hidden = false;
  toastTimer = setTimeout(() => { box.hidden = true; }, duration);
}
export const timeText = value => new Date(value).toLocaleTimeString('zh-CN', {hour:'2-digit',minute:'2-digit',hour12:false});
export const dateText = value => new Date(value).toLocaleString('zh-CN', {month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});
export const voteStatus = contestant => ({open:'投票进行中',locked:'已锁票',pending:'尚未开票'})[contestant?.voting] || '等待开场';
export const showStatus = contestant => ({upcoming:'待上场',performing:'正在演出',performed:'已演出'})[contestant?.status] || '待上场';
export function errorMessage(error) {
  if (error?.name === 'AbortError') return '网络响应较慢，请重新同步后查看是否已保存。';
  if (error instanceof TypeError) return '网络暂时不可用，请连接网络后重试。';
  return typeof error?.message === 'string' ? error.message : '操作未完成，请稍后再试。';
}
let activeModal, previousFocus;
export function openModal(backdrop) {
  if (activeModal) closeModal(activeModal);
  previousFocus = document.activeElement; activeModal = backdrop;
  backdrop.hidden = false; document.body.style.overflow = 'hidden';
  const box = $('[role="dialog"]', backdrop); box.focus();
}
export function closeModal(backdrop = activeModal) {
  if (!backdrop) return; backdrop.hidden = true; document.body.style.overflow = '';
  activeModal = null; previousFocus?.focus();
}
export function setupModals() {
  $$('.modal-close').forEach(item => item.addEventListener('click', () => closeModal(item.closest('.modal-backdrop'))));
  $$('.modal-backdrop').forEach(item => item.addEventListener('click', event => { if (event.target === item) closeModal(item); }));
  document.addEventListener('keydown', event => {
    if (!activeModal) return;
    if (event.key === 'Escape') { event.preventDefault(); closeModal(); }
    if (event.key === 'Tab') {
      const controls = $$('button:not(:disabled),a[href],input:not(:disabled),textarea:not(:disabled),select:not(:disabled),summary,[tabindex="0"]', activeModal).filter(item => item.getClientRects().length);
      if (!controls.length) { event.preventDefault(); return; }
      const first=controls[0], last=controls[controls.length-1];
      if (event.shiftKey && (document.activeElement === first || document.activeElement.getAttribute('role') === 'dialog')) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
}
export function renderConnection(client) {
  const names = {connecting:'正在同步',live:'现场已连接',reconnecting:'正在重连',offline:'网络已断开',paused:'已暂停同步',polling:'兼容模式'};
  const element = $('#connection');
  if (element) { element.className = 'connection ' + (client.live ? 'live' : 'offline'); element.lastElementChild.textContent = names[client.connection] || '正在同步'; }
  const banner = $('#network-banner');
  if (banner) {
    banner.hidden = client.connection === 'live' || client.connection === 'paused';
    banner.textContent = client.connection === 'polling' ? '当前浏览器使用兼容同步，状态可能稍有延迟；每一票仍由服务器确认。' : client.connection === 'offline' ? '网络暂时断开。你的已保存投票不会丢失，联网后会自动恢复。' : '正在与现场同步，恢复连接后即可继续操作。';
  }
}
