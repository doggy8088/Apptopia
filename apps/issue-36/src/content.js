import { mergeContext } from './shared/linguist.js';

const CAPTION_POLL_MS = 400;
const HISTORY_LIMIT = 5;

let shadowRoot;
let captionEl;
let toastEl;
let lastCaptionText = '';
let captionHistory = [];
let lastSelection = '';
let lastContext = '';

function createOverlay() {
  if (shadowRoot) return;
  const host = document.createElement('div');
  host.id = 'linguistflow-overlay-host';
  host.style.position = 'absolute';
  host.style.left = '0';
  host.style.top = '0';
  host.style.width = '100%';
  host.style.height = '100%';
  host.style.pointerEvents = 'none';
  host.style.zIndex = '9999';

  shadowRoot = host.attachShadow({ mode: 'open' });
  shadowRoot.innerHTML = `
    <style>
      :host { all: initial; }
      #lf-overlay {
        position: absolute;
        left: 50%;
        bottom: 12%;
        transform: translateX(-50%);
        max-width: 80%;
        min-width: 200px;
        pointer-events: none;
        font-family: "Source Sans 3", "Noto Sans TC", sans-serif;
      }
      #lf-caption {
        pointer-events: auto;
        padding: 10px 14px;
        border-radius: 12px;
        background: rgba(12, 12, 12, 0.72);
        color: #f3f4f6;
        font-size: 20px;
        line-height: 1.5;
        text-align: center;
        text-shadow: 0 2px 10px rgba(0,0,0,0.7);
        user-select: text;
        white-space: pre-wrap;
      }
      #lf-caption.empty {
        opacity: 0.5;
        font-size: 14px;
      }
      #lf-toast {
        margin-top: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        background: rgba(34, 197, 94, 0.9);
        color: #0b1a12;
        font-size: 13px;
        text-align: center;
        opacity: 0;
        transition: opacity 0.2s ease;
        pointer-events: none;
      }
      #lf-toast.error {
        background: rgba(239, 68, 68, 0.9);
        color: #fff;
      }
      #lf-toast.visible {
        opacity: 1;
      }
    </style>
    <div id="lf-overlay">
      <div id="lf-caption" class="empty">Enable YouTube captions to select text.</div>
      <div id="lf-toast"></div>
    </div>
  `;

  captionEl = shadowRoot.querySelector('#lf-caption');
  toastEl = shadowRoot.querySelector('#lf-toast');

  attachOverlay(host);
}

function attachOverlay(host) {
  const player = document.querySelector('#movie_player') || document.querySelector('ytd-player');
  if (!player) return;
  if (host.parentElement !== player) {
    player.appendChild(host);
  }
}

function updateOverlayPosition() {
  const host = shadowRoot?.host;
  if (!host) return;
  attachOverlay(host);
}

function getCaptionText() {
  const segments = document.querySelectorAll('.ytp-caption-segment');
  if (!segments.length) return '';
  const text = Array.from(segments)
    .map((segment) => segment.textContent || '')
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim();
  return text;
}

function pushCaption(text) {
  captionHistory = captionHistory.filter((item) => item.text !== text);
  captionHistory.push({ text, ts: Date.now() });
  if (captionHistory.length > HISTORY_LIMIT) {
    captionHistory.shift();
  }
}

function updateCaption() {
  const text = getCaptionText();
  if (!text) {
    captionEl.textContent = 'Enable YouTube captions to select text.';
    captionEl.classList.add('empty');
    lastCaptionText = '';
    return;
  }

  if (text !== lastCaptionText) {
    lastCaptionText = text;
    pushCaption(text);
    captionEl.textContent = text;
    captionEl.classList.remove('empty');
    lastContext = buildContext();
  }
}

function buildContext() {
  if (!captionHistory.length) return '';
  const current = captionHistory[captionHistory.length - 1]?.text || '';
  const previous = captionHistory[captionHistory.length - 2]?.text || '';
  return mergeContext(previous, current);
}

function isSelectionInsideOverlay(selection) {
  if (!selection || !selection.anchorNode) return false;
  if (!shadowRoot) return false;
  return shadowRoot.contains(selection.anchorNode);
}

function handleSelectionChange() {
  const selection = document.getSelection();
  if (!isSelectionInsideOverlay(selection)) return;
  const selectedText = selection.toString().trim();
  if (!selectedText) return;
  lastSelection = selectedText;
  lastContext = buildContext();
}

function showToast(message, type = 'success') {
  if (!toastEl) return;
  toastEl.textContent = message;
  toastEl.classList.toggle('error', type === 'error');
  toastEl.classList.add('visible');
  clearTimeout(showToast.timeout);
  showToast.timeout = setTimeout(() => {
    toastEl.classList.remove('visible');
  }, 2200);
}

async function translateWithWindowAI(text) {
  if (!text) return '';
  try {
    const ai = window.ai;
    if (!ai || !ai.languageModel?.create) return '';
    const session = await ai.languageModel.create({ temperature: 0.1 });
    const result = await session.prompt(`Translate to Traditional Chinese. Only return translation. Text: ${text}`);
    await session.destroy();
    return (result || '').trim();
  } catch (error) {
    return '';
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === 'lf-collect-selection') {
    const selectionText = lastSelection || message.fallbackSelection || '';
    const context = lastContext || buildContext();
    const video = document.querySelector('video');
    const videoTime = video ? Math.floor(video.currentTime) : 0;
    const payload = {
      selection: selectionText,
      context,
      videoTime,
      videoUrl: window.location.href
    };
    sendResponse(payload);
    return true;
  }

  if (message?.type === 'lf-toast') {
    showToast(message.message, message.variant);
  }

  if (message?.type === 'lf-translate') {
    translateWithWindowAI(message.text)
      .then((translation) => sendResponse({ translation }))
      .catch(() => sendResponse({ translation: '' }));
    return true;
  }

  return undefined;
});

function init() {
  createOverlay();
  document.addEventListener('selectionchange', handleSelectionChange);
  document.addEventListener('fullscreenchange', updateOverlayPosition);
  window.addEventListener('resize', updateOverlayPosition);

  setInterval(() => {
    updateOverlayPosition();
    updateCaption();
  }, CAPTION_POLL_MS);
}

init();
