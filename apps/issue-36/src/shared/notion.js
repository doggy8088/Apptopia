const NOTION_VERSION = '2022-06-28';

export function buildNotionPayload({
  databaseId,
  word,
  definition,
  context,
  grammar,
  status,
  statusPropertyType
}) {
  const properties = {
    Word: {
      title: [{ text: { content: word } }]
    },
    Definition: {
      rich_text: definition
        ? [{ text: { content: definition } }]
        : []
    },
    Context: {
      rich_text: context
        ? [{ text: { content: context } }]
        : []
    },
    Grammar: {
      select: grammar ? { name: grammar } : null
    }
  };

  if (statusPropertyType === 'select') {
    properties.Status = {
      select: status ? { name: status } : null
    };
  } else {
    properties.Status = {
      status: status ? { name: status } : null
    };
  }

  return {
    parent: { database_id: databaseId },
    properties
  };
}

export async function postNotionPage({ apiKey, payload }) {
  const response = await fetch('https://api.notion.com/v1/pages', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      'Notion-Version': NOTION_VERSION
    },
    body: JSON.stringify(payload)
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data?.message || `Notion API error (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return data;
}

export async function translateWithGoogle({ apiKey, text, target = 'zh-TW' }) {
  if (!apiKey || !text) return '';
  const response = await fetch(`https://translation.googleapis.com/language/translate/v2?key=${apiKey}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ q: text, target, format: 'text' })
    }
  );

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data?.error?.message || 'Google Translate API error';
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return data?.data?.translations?.[0]?.translatedText || '';
}
