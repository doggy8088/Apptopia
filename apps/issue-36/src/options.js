import { defaultSettings, getSettings, saveSettings } from './shared/storage.js';

const form = document.getElementById('settings-form');
const statusEl = document.getElementById('status');

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? '#b91c11' : '#1b6f4a';
}

async function init() {
  const settings = await getSettings();
  form.notionApiKey.value = settings.notionApiKey;
  form.notionDatabaseId.value = settings.notionDatabaseId;
  form.googleTranslateApiKey.value = settings.googleTranslateApiKey;
  form.statusPropertyType.value = settings.statusPropertyType || defaultSettings().statusPropertyType;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  setStatus('Saving...');
  try {
    await saveSettings({
      notionApiKey: form.notionApiKey.value,
      notionDatabaseId: form.notionDatabaseId.value,
      googleTranslateApiKey: form.googleTranslateApiKey.value,
      statusPropertyType: form.statusPropertyType.value
    });
    setStatus('Settings saved.');
  } catch (error) {
    setStatus('Failed to save settings.', true);
  }
});

init();
