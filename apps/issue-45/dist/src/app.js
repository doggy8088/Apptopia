const STORAGE_KEY = "pixelnest.v1";
const CANVAS_BASE = { width: 960, height: 540 };

const FOLDERS = {
  desk: { label: "書桌 / 工作", path: "desk/work" },
  bed: { label: "床鋪 / 日記", path: "bed/journal" },
  shelf: { label: "書櫃 / 學習", path: "shelf/study" },
  fridge: { label: "冰箱 / 購物", path: "fridge/shopping" }
};

const ROOM_OBJECTS = [
  { id: "door", label: "玄關", rect: { x: 60, y: 360, w: 200, h: 140 }, color: "#d9895b" },
  { id: "desk", label: "書桌", rect: { x: 580, y: 120, w: 200, h: 120 }, color: "#f2c14e" },
  { id: "bed", label: "床鋪", rect: { x: 140, y: 120, w: 240, h: 140 }, color: "#f28c6f" },
  { id: "shelf", label: "書櫃", rect: { x: 680, y: 300, w: 200, h: 140 }, color: "#4b7f52" },
  { id: "fridge", label: "冰箱", rect: { x: 400, y: 320, w: 180, h: 160 }, color: "#8ecae6" }
];

const PATHS = {
  desk: [
    { x: 150, y: 420 },
    { x: 340, y: 420 },
    { x: 520, y: 300 },
    { x: 660, y: 180 }
  ],
  bed: [
    { x: 150, y: 420 },
    { x: 180, y: 260 }
  ],
  shelf: [
    { x: 150, y: 420 },
    { x: 360, y: 420 },
    { x: 720, y: 380 }
  ],
  fridge: [
    { x: 150, y: 420 },
    { x: 320, y: 420 },
    { x: 470, y: 380 }
  ]
};

const DEFAULT_STATE = {
  folders: {
    desk: [],
    bed: [],
    shelf: [],
    fridge: []
  },
  inbox: [],
  settings: {
    provider: "gemini",
    model: "gemini-1.5-flash",
    apiKey: "",
    allowFallback: true
  },
  game: {
    coins: 0
  }
};

const SAMPLE_INBOX = [
  "週三與開發團隊開會",
  "鮮奶買兩瓶",
  "今天看了很棒的電影"
];

let state = loadState();
let currentFolder = "desk";
let currentNoteId = null;
let installPromptEvent = null;

const elements = {
  coinCount: document.getElementById("coinCount"),
  inboxCount: document.getElementById("inboxCount"),
  inboxList: document.getElementById("inboxList"),
  newInboxText: document.getElementById("newInboxText"),
  addInbox: document.getElementById("addInbox"),
  autoSort: document.getElementById("autoSort"),
  agentStatus: document.getElementById("agentStatus"),
  exportZip: document.getElementById("exportZip"),
  provider: document.getElementById("provider"),
  model: document.getElementById("model"),
  apiKey: document.getElementById("apiKey"),
  allowFallback: document.getElementById("allowFallback"),
  saveSettings: document.getElementById("saveSettings"),
  settingsStatus: document.getElementById("settingsStatus"),
  installButton: document.getElementById("installButton"),
  editorModal: document.getElementById("editorModal"),
  folderLabel: document.getElementById("folderLabel"),
  folderTitle: document.getElementById("folderTitle"),
  closeEditor: document.getElementById("closeEditor"),
  noteList: document.getElementById("noteList"),
  noteTitle: document.getElementById("noteTitle"),
  noteContent: document.getElementById("noteContent"),
  newNote: document.getElementById("newNote"),
  saveNote: document.getElementById("saveNote"),
  deleteNote: document.getElementById("deleteNote"),
  rewardToast: document.getElementById("rewardToast")
};

const canvas = document.getElementById("roomCanvas");
const ctx = canvas.getContext("2d");
ctx.imageSmoothingEnabled = false;

const agent = {
  x: 300,
  y: 420,
  size: 24,
  speed: 140,
  queue: [],
  carrying: null,
  happyFrames: 0,
  onComplete: null
};

function loadState() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      return structuredClone(DEFAULT_STATE);
    }
    const parsed = JSON.parse(stored);
    const merged = structuredClone(DEFAULT_STATE);
    merged.folders = { ...merged.folders, ...(parsed.folders || {}) };
    merged.inbox = Array.isArray(parsed.inbox) ? parsed.inbox : merged.inbox;
    merged.settings = { ...merged.settings, ...(parsed.settings || {}) };
    merged.game = { ...merged.game, ...(parsed.game || {}) };
    return merged;
  } catch (error) {
    console.warn("Failed to load state", error);
    return structuredClone(DEFAULT_STATE);
  }
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function ensureSamples() {
  if (state.inbox.length === 0) {
    state.inbox = SAMPLE_INBOX.map((text) => createNote(text));
    saveState();
  }
}

function createNote(content) {
  return {
    id: `note_${crypto.randomUUID()}`,
    title: content.split("\n")[0].slice(0, 24) || "未命名",
    content,
    checkedCount: countChecked(content),
    createdAt: new Date().toISOString()
  };
}

function countChecked(content) {
  const matches = content.match(/\[x\]/gi);
  return matches ? matches.length : 0;
}

function updateCounts() {
  elements.coinCount.textContent = state.game.coins.toString();
  elements.inboxCount.textContent = state.inbox.length.toString();
}

function renderInbox() {
  elements.inboxList.innerHTML = "";
  state.inbox.forEach((note) => {
    const item = document.createElement("li");
    item.textContent = note.content;
    elements.inboxList.appendChild(item);
  });
  updateCounts();
}

function openEditor(folderId) {
  currentFolder = folderId;
  elements.folderLabel.textContent = folderId.toUpperCase();
  elements.folderTitle.textContent = FOLDERS[folderId].label;
  elements.editorModal.classList.add("open");
  elements.editorModal.setAttribute("aria-hidden", "false");
  renderNotesList();
  if (!currentNoteId && state.folders[folderId].length) {
    selectNote(state.folders[folderId][0].id);
  }
}

function closeEditor() {
  elements.editorModal.classList.remove("open");
  elements.editorModal.setAttribute("aria-hidden", "true");
  currentNoteId = null;
}

function renderNotesList() {
  elements.noteList.innerHTML = "";
  const notes = state.folders[currentFolder];
  notes.forEach((note) => {
    const item = document.createElement("li");
    item.textContent = note.title || "未命名";
    item.classList.toggle("active", note.id === currentNoteId);
    item.addEventListener("click", () => selectNote(note.id));
    elements.noteList.appendChild(item);
  });
}

function selectNote(noteId) {
  const note = state.folders[currentFolder].find((entry) => entry.id === noteId);
  if (!note) {
    return;
  }
  currentNoteId = noteId;
  elements.noteTitle.value = note.title || "";
  elements.noteContent.value = note.content || "";
  renderNotesList();
}

function createNoteInFolder() {
  const note = createNote("");
  note.title = "新筆記";
  state.folders[currentFolder].unshift(note);
  saveState();
  currentNoteId = note.id;
  renderNotesList();
  selectNote(note.id);
}

function handleSaveNote() {
  if (!currentNoteId) {
    createNoteInFolder();
  }
  const note = state.folders[currentFolder].find((entry) => entry.id === currentNoteId);
  if (!note) {
    return;
  }
  const newTitle = elements.noteTitle.value.trim() || "未命名";
  const newContent = elements.noteContent.value.trim();
  const newChecked = countChecked(newContent);
  if (newChecked > note.checkedCount) {
    const delta = newChecked - note.checkedCount;
    rewardCoins(delta * 10);
  }
  note.title = newTitle;
  note.content = newContent;
  note.checkedCount = newChecked;
  note.updatedAt = new Date().toISOString();
  saveState();
  renderNotesList();
}

function handleDeleteNote() {
  if (!currentNoteId) {
    return;
  }
  state.folders[currentFolder] = state.folders[currentFolder].filter((note) => note.id !== currentNoteId);
  currentNoteId = null;
  saveState();
  renderNotesList();
  elements.noteTitle.value = "";
  elements.noteContent.value = "";
}

function rewardCoins(amount) {
  state.game.coins += amount;
  updateCounts();
  elements.rewardToast.textContent = `+${amount} coins`;
  elements.rewardToast.classList.add("show");
  agent.happyFrames = 30;
  setTimeout(() => elements.rewardToast.classList.remove("show"), 1200);
  saveState();
}

function showStatus(message, target = elements.agentStatus) {
  target.textContent = message;
}

function setupSettings() {
  elements.provider.value = state.settings.provider;
  elements.model.value = state.settings.model;
  elements.apiKey.value = state.settings.apiKey;
  elements.allowFallback.checked = state.settings.allowFallback;
}

function saveSettings() {
  state.settings.provider = elements.provider.value;
  state.settings.model = elements.model.value.trim();
  state.settings.apiKey = elements.apiKey.value.trim();
  state.settings.allowFallback = elements.allowFallback.checked;
  saveState();
  showStatus("設定已儲存。", elements.settingsStatus);
}

function addInboxNote() {
  const value = elements.newInboxText.value.trim();
  if (!value) {
    return;
  }
  state.inbox.unshift(createNote(value));
  elements.newInboxText.value = "";
  saveState();
  renderInbox();
  showStatus("便條已放到玄關。");
}

function getObjectById(id) {
  return ROOM_OBJECTS.find((obj) => obj.id === id);
}

function drawRoom() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#fef0dd";
  ctx.fillRect(0, 0, CANVAS_BASE.width, CANVAS_BASE.height);

  for (let x = 0; x < CANVAS_BASE.width; x += 40) {
    for (let y = 0; y < CANVAS_BASE.height; y += 40) {
      ctx.fillStyle = (x + y) % 80 === 0 ? "#f8e2c7" : "#f9e8d4";
      ctx.fillRect(x, y, 40, 40);
    }
  }

  ROOM_OBJECTS.forEach((obj) => {
    ctx.fillStyle = obj.color;
    ctx.fillRect(obj.rect.x, obj.rect.y, obj.rect.w, obj.rect.h);
    ctx.strokeStyle = "#2a241b";
    ctx.lineWidth = 4;
    ctx.strokeRect(obj.rect.x, obj.rect.y, obj.rect.w, obj.rect.h);
    ctx.fillStyle = "#2a241b";
    ctx.font = "14px 'Press Start 2P'";
    ctx.fillText(obj.label, obj.rect.x + 8, obj.rect.y + 24);
  });

  drawInboxNotes();
  drawAgent();
}

function drawInboxNotes() {
  const door = getObjectById("door");
  state.inbox.slice(0, 6).forEach((note, index) => {
    const offsetX = (index % 3) * 26;
    const offsetY = Math.floor(index / 3) * 26;
    const x = door.rect.x + 30 + offsetX;
    const y = door.rect.y + 60 + offsetY;
    ctx.fillStyle = "#fffdf7";
    ctx.fillRect(x, y, 20, 20);
    ctx.strokeStyle = "#2a241b";
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, 20, 20);
    ctx.fillStyle = "#2a241b";
    ctx.fillRect(x + 6, y + 6, 8, 2);
    ctx.fillRect(x + 6, y + 10, 8, 2);
  });
}

function drawAgent() {
  const size = agent.size + (agent.happyFrames > 0 ? 4 : 0);
  ctx.fillStyle = "#3a5a40";
  ctx.fillRect(agent.x - size / 2, agent.y - size / 2, size, size);
  ctx.fillStyle = "#fef0dd";
  ctx.fillRect(agent.x - size / 4, agent.y - size / 4, size / 2, size / 2);
  if (agent.carrying) {
    ctx.fillStyle = "#fff";
    ctx.fillRect(agent.x + size / 2, agent.y - size / 2, 16, 12);
  }
}

function updateAgent(delta) {
  if (agent.queue.length === 0) {
    if (agent.onComplete) {
      agent.onComplete();
      agent.onComplete = null;
    }
    agent.happyFrames = Math.max(0, agent.happyFrames - 1);
    return;
  }
  const target = agent.queue[0];
  const dx = target.x - agent.x;
  const dy = target.y - agent.y;
  const distance = Math.hypot(dx, dy);
  if (distance < 2) {
    agent.queue.shift();
    return;
  }
  const step = (agent.speed * delta) / 1000;
  agent.x += (dx / distance) * step;
  agent.y += (dy / distance) * step;
}

function moveAgentAlong(points) {
  return new Promise((resolve) => {
    agent.queue = points.map((point) => ({ ...point }));
    agent.onComplete = resolve;
  });
}

async function autoSortInbox() {
  if (state.inbox.length === 0) {
    showStatus("玄關沒有待整理的便條。");
    return;
  }
  showStatus("Pixel Agent 準備整理...請稍候。");

  let plan;
  const hasKey = Boolean(state.settings.apiKey);
  if (hasKey) {
    try {
      plan = await requestSortPlan();
    } catch (error) {
      console.error(error);
      if (!state.settings.allowFallback) {
        showStatus("LLM 失敗，請檢查 API Key 或稍後再試。");
        return;
      }
      showStatus("LLM 失敗，改用本地分類。");
      plan = fallbackPlan();
    }
  } else {
    showStatus("未設定 API Key，改用本地分類。");
    plan = fallbackPlan();
  }

  const doorPoint = PATHS.desk[0];
  for (const action of plan) {
    const noteIndex = state.inbox.findIndex((note) => note.id === action.id);
    if (noteIndex === -1) {
      continue;
    }
    const note = state.inbox[noteIndex];
    const destination = action.destination;
    showStatus(`整理中：${note.content} → ${FOLDERS[destination].label}`);
    await moveAgentAlong([doorPoint]);
    agent.carrying = note.title;
    await delay(300);
    await moveAgentAlong(PATHS[destination]);
    agent.carrying = null;

    state.inbox.splice(noteIndex, 1);
    state.folders[destination].unshift(note);
    saveState();
    renderInbox();
  }

  showStatus("整理完成。Pixel Agent 已經歸檔所有便條。");
}

function fallbackPlan() {
  return state.inbox.map((note) => ({
    id: note.id,
    destination: classifyNote(note.content)
  }));
}

function classifyNote(text) {
  if (/買|購物|牛奶|鮮奶|雞蛋|菜|超市/i.test(text)) {
    return "fridge";
  }
  if (/會議|專案|工作|開發|報告/i.test(text)) {
    return "desk";
  }
  if (/閱讀|學習|課程|研究|筆記/i.test(text)) {
    return "shelf";
  }
  return "bed";
}

async function requestSortPlan() {
  const prompt = buildSortPrompt();
  const provider = state.settings.provider;
  if (provider === "openai") {
    return requestOpenAI(prompt);
  }
  return requestGemini(prompt);
}

function buildSortPrompt() {
  const notes = state.inbox.map((note) => ({ id: note.id, text: note.content }));
  return `你是 PixelNest 的整理小精靈。請將以下便條分類到四個資料夾：desk(工作)、bed(日記)、shelf(學習)、fridge(購物)。\n\n請只回傳 JSON 陣列，格式如下：\n[{"id":"note_id","destination":"desk","reason":"原因"}]\n\n待分類便條：${JSON.stringify(notes, null, 2)}`;
}

async function requestGemini(prompt) {
  const model = state.settings.model || "gemini-1.5-flash";
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${state.settings.apiKey}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{ role: "user", parts: [{ text: prompt }] }],
        generationConfig: { temperature: 0.2 }
      })
    }
  );

  if (!response.ok) {
    throw new Error(`Gemini API error: ${response.status}`);
  }

  const data = await response.json();
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text || "";
  return parsePlan(text);
}

async function requestOpenAI(prompt) {
  const model = state.settings.model || "gpt-4o-mini";
  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${state.settings.apiKey}`
    },
    body: JSON.stringify({
      model,
      temperature: 0.2,
      messages: [
        {
          role: "system",
          content: "你是分類助手，只能輸出 JSON 陣列。"
        },
        { role: "user", content: prompt }
      ]
    })
  });

  if (!response.ok) {
    throw new Error(`OpenAI API error: ${response.status}`);
  }

  const data = await response.json();
  const text = data?.choices?.[0]?.message?.content || "";
  return parsePlan(text);
}

function parsePlan(text) {
  const jsonMatch = text.match(/\[\s*{[\s\S]*}\s*\]/);
  const jsonText = jsonMatch ? jsonMatch[0] : text;
  const parsed = JSON.parse(jsonText);
  return parsed.map((item) => ({
    id: item.id,
    destination: FOLDERS[item.destination] ? item.destination : classifyNote(item.text || "")
  }));
}

async function exportZip() {
  const zip = new JSZip();

  Object.entries(FOLDERS).forEach(([key, info]) => {
    const folder = zip.folder(info.path);
    state.folders[key].forEach((note) => {
      const fileName = `${sanitizeFileName(note.title || note.id)}-${note.id.slice(-6)}.md`;
      folder.file(fileName, note.content || "");
    });
  });

  const inboxFolder = zip.folder("inbox");
  state.inbox.forEach((note) => {
    const fileName = `${sanitizeFileName(note.title || note.id)}-${note.id.slice(-6)}.md`;
    inboxFolder.file(fileName, note.content || "");
  });

  const blob = await zip.generateAsync({ type: "blob" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `pixelnest-export-${new Date().toISOString().slice(0, 10)}.zip`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);

  showStatus("已完成 ZIP 匯出。", elements.agentStatus);
}

function sanitizeFileName(name) {
  return name.replace(/[^a-z0-9\u4e00-\u9fa5_-]/gi, "_").slice(0, 32) || "note";
}

function setupCanvasInteractions() {
  canvas.addEventListener("click", (event) => {
    const point = getCanvasPoint(event);
    const clickedObject = ROOM_OBJECTS.find(
      (obj) =>
        point.x >= obj.rect.x &&
        point.x <= obj.rect.x + obj.rect.w &&
        point.y >= obj.rect.y &&
        point.y <= obj.rect.y + obj.rect.h
    );

    if (clickedObject && FOLDERS[clickedObject.id]) {
      openEditor(clickedObject.id);
      return;
    }

    if (isAgentHit(point)) {
      autoSortInbox();
    }
  });
}

function isAgentHit(point) {
  return (
    point.x >= agent.x - agent.size / 2 &&
    point.x <= agent.x + agent.size / 2 &&
    point.y >= agent.y - agent.size / 2 &&
    point.y <= agent.y + agent.size / 2
  );
}

function getCanvasPoint(event) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = CANVAS_BASE.width / rect.width;
  const scaleY = CANVAS_BASE.height / rect.height;
  return {
    x: (event.clientX - rect.left) * scaleX,
    y: (event.clientY - rect.top) * scaleY
  };
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function setupInstallPrompt() {
  window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    installPromptEvent = event;
    elements.installButton.disabled = false;
  });

  elements.installButton.addEventListener("click", async () => {
    if (!installPromptEvent) {
      showStatus("目前瀏覽器尚未觸發安裝提示。");
      return;
    }
    installPromptEvent.prompt();
    installPromptEvent = null;
  });
}

function registerServiceWorker() {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch((error) => {
      console.warn("Service worker registration failed", error);
    });
  }
}

function startAnimation() {
  let lastTime = performance.now();
  function tick(now) {
    const delta = now - lastTime;
    lastTime = now;
    updateAgent(delta);
    drawRoom();
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

canvas.width = CANVAS_BASE.width;
canvas.height = CANVAS_BASE.height;
ensureSamples();
renderInbox();
setupSettings();
setupCanvasInteractions();
setupInstallPrompt();
registerServiceWorker();
startAnimation();

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeEditor();
  }
});

elements.addInbox.addEventListener("click", addInboxNote);

elements.newInboxText.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    addInboxNote();
  }
});

elements.autoSort.addEventListener("click", autoSortInbox);

elements.exportZip.addEventListener("click", exportZip);

elements.saveSettings.addEventListener("click", saveSettings);

elements.closeEditor.addEventListener("click", closeEditor);

elements.newNote.addEventListener("click", createNoteInFolder);

elements.saveNote.addEventListener("click", handleSaveNote);

elements.deleteNote.addEventListener("click", handleDeleteNote);
