const DEFAULT_SETTINGS = {
  notionApiKey: '',
  notionDatabaseId: '',
  googleTranslateApiKey: '',
  statusPropertyType: 'status'
};

export async function getSettings() {
  const result = await chrome.storage.sync.get(DEFAULT_SETTINGS);
  return { ...DEFAULT_SETTINGS, ...result };
}

export async function saveSettings(settings) {
  await chrome.storage.sync.set({
    notionApiKey: settings.notionApiKey?.trim() || '',
    notionDatabaseId: settings.notionDatabaseId?.trim() || '',
    googleTranslateApiKey: settings.googleTranslateApiKey?.trim() || '',
    statusPropertyType: settings.statusPropertyType || 'status'
  });
}

export async function getQueue() {
  const result = await chrome.storage.local.get({ queue: [] });
  return result.queue || [];
}

export async function saveQueue(queue) {
  await chrome.storage.local.set({ queue });
}

export function defaultSettings() {
  return { ...DEFAULT_SETTINGS };
}
