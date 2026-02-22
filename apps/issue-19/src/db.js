const DB_NAME = "open-moneybook";
const DB_VERSION = 1;

const DEFAULT_CATEGORIES = [
  { id: "expense-food", name: "餐飲", type: "expense", color: "#d17a42" },
  { id: "expense-home", name: "居住", type: "expense", color: "#8c5e3c" },
  { id: "expense-transport", name: "交通", type: "expense", color: "#437c90" },
  { id: "expense-shopping", name: "購物", type: "expense", color: "#c66b6b" },
  { id: "expense-entertain", name: "娛樂", type: "expense", color: "#3f7d6b" },
  { id: "expense-health", name: "醫療", type: "expense", color: "#3c8a6b" },
  { id: "expense-education", name: "教育", type: "expense", color: "#b2854f" },
  { id: "expense-other", name: "其他", type: "expense", color: "#7c6f64" },
  { id: "income-salary", name: "薪資", type: "income", color: "#2f8f5b" },
  { id: "income-bonus", name: "獎金", type: "income", color: "#4e9f80" },
  { id: "income-invest", name: "投資", type: "income", color: "#3b7f87" },
  { id: "income-other", name: "其他收入", type: "income", color: "#5f8a5b" }
];

export async function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onupgradeneeded = event => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains("transactions")) {
        db.createObjectStore("transactions", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("budgets")) {
        db.createObjectStore("budgets", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("categories")) {
        db.createObjectStore("categories", { keyPath: "id" });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

function txStore(db, name, mode = "readonly") {
  return db.transaction(name, mode).objectStore(name);
}

export async function getAll(db, storeName) {
  return new Promise((resolve, reject) => {
    const request = txStore(db, storeName).getAll();
    request.onsuccess = () => resolve(request.result || []);
    request.onerror = () => reject(request.error);
  });
}

export async function putItem(db, storeName, value) {
  return new Promise((resolve, reject) => {
    const request = txStore(db, storeName, "readwrite").put(value);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

export async function addItem(db, storeName, value) {
  return new Promise((resolve, reject) => {
    const request = txStore(db, storeName, "readwrite").add(value);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

export async function deleteItem(db, storeName, key) {
  return new Promise((resolve, reject) => {
    const request = txStore(db, storeName, "readwrite").delete(key);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

export async function ensureSeedData(db) {
  const existing = await getAll(db, "categories");
  if (existing.length > 0) {
    return;
  }
  await Promise.all(DEFAULT_CATEGORIES.map(category => addItem(db, "categories", category)));
}

export function getDefaultCategories() {
  return DEFAULT_CATEGORIES.slice();
}
