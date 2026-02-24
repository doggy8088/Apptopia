import { getSettings, getQueue, saveQueue } from './shared/storage.js';
import { buildNotionPayload, postNotionPage, translateWithGoogle } from './shared/notion.js';
import { normalizeWord, inferGrammar } from './shared/linguist.js';

const MENU_ID = 'linguistflow-add-to-notion';
const QUEUE_ALARM = 'linguistflow-queue';
const STATUS_DEFAULT = 'New';

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: MENU_ID,
    title: 'LinguistFlow: Add to Notion',
    contexts: ['selection']
  });
  chrome.alarms.create(QUEUE_ALARM, { periodInMinutes: 1 });
});

chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create(QUEUE_ALARM, { periodInMinutes: 1 });
});

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== MENU_ID) return;
  if (!tab?.id) return;
  await handleAddToNotion(tab.id, info.selectionText || '');
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name !== QUEUE_ALARM) return;
  await processQueue();
});

async function handleAddToNotion(tabId, fallbackSelection) {
  const settings = await getSettings();
  if (!settings.notionApiKey || !settings.notionDatabaseId) {
    await sendToast(tabId, 'Missing Notion API key or Database ID.', 'error');
    return;
  }

  const selectionPayload = await chrome.tabs.sendMessage(tabId, {
    type: 'lf-collect-selection',
    fallbackSelection
  }).catch(() => null);

  if (!selectionPayload?.selection) {
    await sendToast(tabId, 'No text selected from captions.', 'error');
    return;
  }

  const selection = selectionPayload.selection.trim();
  const context = selectionPayload.context || '';
  const word = normalizeWord(selection) || selection;
  const grammar = inferGrammar(selection);

  let definition = '';
  if (settings.googleTranslateApiKey) {
    try {
      definition = await translateWithGoogle({
        apiKey: settings.googleTranslateApiKey,
        text: selection
      });
    } catch (error) {
      await sendToast(tabId, 'Translate failed, saving without Definition.', 'error');
    }
  } else {
    const response = await chrome.tabs.sendMessage(tabId, {
      type: 'lf-translate',
      text: selection
    }).catch(() => ({ translation: '' }));
    definition = response?.translation || '';
  }

  const payload = buildNotionPayload({
    databaseId: settings.notionDatabaseId,
    word,
    definition,
    context,
    grammar,
    status: STATUS_DEFAULT,
    statusPropertyType: settings.statusPropertyType
  });

  try {
    await postNotionPage({ apiKey: settings.notionApiKey, payload });
    await sendToast(tabId, '已成功加入 Notion', 'success');
  } catch (error) {
    if (isOfflineError(error)) {
      await enqueueItem({ payload });
      await sendToast(tabId, 'Offline: Word saved to local queue.', 'error');
      return;
    }

    if (isStatusTypeMismatch(error)) {
      const retryPayload = buildNotionPayload({
        databaseId: settings.notionDatabaseId,
        word,
        definition,
        context,
        grammar,
        status: STATUS_DEFAULT,
        statusPropertyType: settings.statusPropertyType === 'status' ? 'select' : 'status'
      });
      try {
        await postNotionPage({ apiKey: settings.notionApiKey, payload: retryPayload });
        await sendToast(tabId, '已成功加入 Notion', 'success');
        return;
      } catch (retryError) {
        await sendToast(tabId, retryError.message || 'Notion write failed.', 'error');
        return;
      }
    }

    await sendToast(tabId, error.message || 'Notion write failed.', 'error');
  }
}

async function sendToast(tabId, message, variant) {
  await chrome.tabs.sendMessage(tabId, {
    type: 'lf-toast',
    message,
    variant
  }).catch(() => null);
}

function isOfflineError(error) {
  if (!error) return false;
  return error.name === 'TypeError' || /network/i.test(error.message || '');
}

function isStatusTypeMismatch(error) {
  const message = error?.message || '';
  return /status/i.test(message) && /property/i.test(message);
}

async function enqueueItem(item) {
  const queue = await getQueue();
  queue.push({
    ...item,
    createdAt: Date.now(),
    attempts: 0
  });
  await saveQueue(queue);
}

async function processQueue() {
  const settings = await getSettings();
  if (!settings.notionApiKey || !settings.notionDatabaseId) return;

  const queue = await getQueue();
  if (!queue.length) return;

  const remaining = [];
  for (const item of queue) {
    try {
      await postNotionPage({ apiKey: settings.notionApiKey, payload: item.payload });
    } catch (error) {
      remaining.push({
        ...item,
        attempts: (item.attempts || 0) + 1,
        lastError: error.message || 'Unknown error'
      });
    }
  }

  await saveQueue(remaining);
}
