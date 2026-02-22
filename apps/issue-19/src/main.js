import { addBatch, addItem, deleteItem, ensureSeedData, getAll, openDB, putItem } from "./db.js";
import { csvToTransactions, transactionsToCsv } from "./lib/csv.js";
import { categoryTotals, dailyBalanceSeries, filterTransactionsByMonth, monthlyTotals } from "./lib/budget.js";
import { formatCurrency, normalizeDateInput, nowMonth, todayDate } from "./lib/date.js";

const state = {
  db: null,
  transactions: [],
  budgets: [],
  categories: [],
  month: nowMonth()
};

const elements = {
  month: document.querySelector("#month"),
  summaryIncome: document.querySelector("#summary-income"),
  summaryExpense: document.querySelector("#summary-expense"),
  summaryBalance: document.querySelector("#summary-balance"),
  budgetAlert: document.querySelector("#budget-alert"),
  txForm: document.querySelector("#tx-form"),
  txType: document.querySelector("#tx-type"),
  txCategory: document.querySelector("#tx-category"),
  txList: document.querySelector("#tx-list"),
  budgetForm: document.querySelector("#budget-form"),
  budgetCategory: document.querySelector("#budget-category"),
  budgetAmount: document.querySelector("#budget-amount"),
  budgetList: document.querySelector("#budget-list"),
  exportCsv: document.querySelector("#export-csv"),
  importCsv: document.querySelector("#import-csv"),
  toast: document.querySelector("#toast")
};

let pieChart;
let lineChart;

async function init() {
  state.db = await openDB();
  await ensureSeedData(state.db);
  await loadData();
  wireEvents();
  render();
  registerServiceWorker();
}

async function loadData() {
  const [transactions, budgets, categories] = await Promise.all([
    getAll(state.db, "transactions"),
    getAll(state.db, "budgets"),
    getAll(state.db, "categories")
  ]);

  state.transactions = transactions.sort((a, b) => b.date.localeCompare(a.date));
  state.budgets = budgets;
  state.categories = categories;
}

function wireEvents() {
  elements.month.value = state.month;
  elements.month.addEventListener("change", event => {
    state.month = event.target.value;
    render();
  });

  elements.txType.addEventListener("change", () => {
    renderCategoryOptions();
  });

  elements.txForm.addEventListener("submit", async event => {
    event.preventDefault();
    const formData = new FormData(elements.txForm);
    let normalizedDate = "";
    try {
      normalizedDate = normalizeDateInput(formData.get("date"));
    } catch (error) {
      showToast(error.message || "日期格式錯誤", "warn");
      return;
    }

    const payload = {
      date: normalizedDate,
      type: formData.get("type"),
      amount: Number(formData.get("amount")),
      categoryId: formData.get("category"),
      account: formData.get("account"),
      note: formData.get("note")?.trim() || ""
    };

    const category = state.categories.find(item => item.id === payload.categoryId);

    if (!payload.type || !payload.categoryId || !payload.account) {
      showToast("請完整填寫必填欄位", "warn");
      return;
    }

    if (!Number.isFinite(payload.amount) || payload.amount <= 0) {
      showToast("金額必須為正數", "warn");
      return;
    }

    const transaction = {
      id: crypto.randomUUID(),
      date: payload.date,
      type: payload.type,
      amount: payload.amount,
      categoryId: payload.categoryId,
      category: category?.name || "未分類",
      account: payload.account,
      note: payload.note,
      createdAt: new Date().toISOString()
    };

    await addItem(state.db, "transactions", transaction);
    state.transactions.unshift(transaction);
    elements.txForm.reset();
    elements.txForm.querySelector("input[name='date']").value = todayDate();

    const warning = checkBudgetWarning(transaction.categoryId, transaction.date.slice(0, 7));
    if (warning) {
      if (transaction.date.startsWith(state.month)) {
        elements.budgetAlert.textContent = warning;
        elements.budgetAlert.classList.remove("hidden");
      }
      showToast(warning, "warn");
    }

    render();
  });

  elements.txList.addEventListener("click", async event => {
    const target = event.target.closest("button[data-id]");
    if (!target) {
      return;
    }
    const id = target.dataset.id;
    await deleteItem(state.db, "transactions", id);
    state.transactions = state.transactions.filter(tx => tx.id !== id);
    render();
  });

  elements.budgetForm.addEventListener("submit", async event => {
    event.preventDefault();
    const categoryId = elements.budgetCategory.value;
    const amount = Number(elements.budgetAmount.value);
    if (!categoryId || !Number.isFinite(amount) || amount <= 0) {
      showToast("請輸入有效的預算", "warn");
      return;
    }

    const budget = {
      id: categoryId,
      categoryId,
      amount,
      period: "monthly",
      updatedAt: new Date().toISOString()
    };

    await putItem(state.db, "budgets", budget);
    const existingIndex = state.budgets.findIndex(item => item.id === categoryId);
    if (existingIndex >= 0) {
      state.budgets[existingIndex] = budget;
    } else {
      state.budgets.push(budget);
    }

    elements.budgetAmount.value = "";
    showToast("預算已更新");
    render();
  });

  elements.exportCsv.addEventListener("click", () => {
    const monthTransactions = filterTransactionsByMonth(state.transactions, state.month);
    const csv = transactionsToCsv(monthTransactions);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `open-moneybook-${state.month}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  });

  elements.importCsv.addEventListener("change", async event => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    try {
      const text = await file.text();
      const imported = csvToTransactions(text);
      const { newCategories, newTransactions } = buildImportBatch(imported);

      if (newCategories.length || newTransactions.length) {
        await addBatch(state.db, { categories: newCategories, transactions: newTransactions });
        if (newCategories.length) {
          state.categories.push(...newCategories);
        }
        if (newTransactions.length) {
          state.transactions = [...newTransactions, ...state.transactions].sort((a, b) => b.date.localeCompare(a.date));
        }
      }

      showToast(`成功匯入 ${newTransactions.length} 筆交易`);
      render();
    } catch (error) {
      showToast(error.message || "CSV 匯入失敗", "warn");
    } finally {
      event.target.value = "";
    }
  });
}

function buildImportBatch(imported) {
  const categoryMap = new Map(state.categories.map(cat => [`${cat.type}:${cat.name}`, cat.id]));
  const newCategories = [];
  const newTransactions = [];

  for (const item of imported) {
    const categoryName = item.category?.trim() || "未分類";
    const key = `${item.type}:${categoryName}`;
    let categoryId = categoryMap.get(key);
    if (!categoryId) {
      categoryId = `${item.type}-custom-${crypto.randomUUID()}`;
      categoryMap.set(key, categoryId);
      newCategories.push({
        id: categoryId,
        name: categoryName,
        type: item.type,
        color: "#7c6f64"
      });
    }

    newTransactions.push({
      id: crypto.randomUUID(),
      date: item.date,
      type: item.type,
      amount: item.amount,
      categoryId,
      category: categoryName,
      account: item.account,
      note: item.note,
      createdAt: new Date().toISOString()
    });
  }

  return { newCategories, newTransactions };
}

function render() {
  renderCategoryOptions();
  renderBudgetOptions();
  renderSummary();
  renderBudgets();
  updateBudgetAlert();
  renderTransactions();
  renderCharts();
}

function renderCategoryOptions() {
  const type = elements.txType.value;
  const options = state.categories.filter(cat => cat.type === type);
  const selected = elements.txCategory.value;
  const fragment = document.createDocumentFragment();
  for (const option of options) {
    const item = document.createElement("option");
    item.value = option.id;
    item.textContent = option.name;
    fragment.appendChild(item);
  }
  elements.txCategory.replaceChildren(fragment);
  if (selected) {
    elements.txCategory.value = selected;
  }
  if (!elements.txForm.querySelector("input[name='date']").value) {
    elements.txForm.querySelector("input[name='date']").value = todayDate();
  }
}

function renderBudgetOptions() {
  const options = state.categories.filter(cat => cat.type === "expense");
  const selected = elements.budgetCategory.value;
  const fragment = document.createDocumentFragment();
  for (const option of options) {
    const item = document.createElement("option");
    item.value = option.id;
    item.textContent = option.name;
    fragment.appendChild(item);
  }
  elements.budgetCategory.replaceChildren(fragment);
  if (selected) {
    elements.budgetCategory.value = selected;
  }
}

function renderSummary() {
  const { income, expense, balance } = monthlyTotals(state.transactions, state.month);
  elements.summaryIncome.textContent = formatCurrency(income);
  elements.summaryExpense.textContent = formatCurrency(expense);
  elements.summaryBalance.textContent = formatCurrency(balance);
}

function renderBudgets() {
  const totals = categoryTotals(state.transactions, state.month, "expense");
  elements.budgetList.replaceChildren();
  if (!state.budgets.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "尚未設定預算";
    elements.budgetList.appendChild(empty);
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const budget of state.budgets) {
    const category = state.categories.find(cat => cat.id === budget.categoryId);
    const spent = totals.get(budget.categoryId) || 0;
    const ratio = budget.amount ? Math.min(spent / budget.amount, 1.4) : 0;
    const isOver = spent > budget.amount;

    const item = document.createElement("div");
    item.className = "budget-item";

    const title = document.createElement("h4");
    title.textContent = category?.name || "分類";

    const amounts = document.createElement("p");
    amounts.textContent = `${formatCurrency(spent)} / ${formatCurrency(budget.amount)}`;

    const progress = document.createElement("div");
    progress.className = `progress${isOver ? " over" : ""}`;
    const bar = document.createElement("span");
    bar.style.width = `${Math.min(ratio * 100, 100)}%`;
    progress.appendChild(bar);

    const status = document.createElement("p");
    status.className = "muted";
    status.textContent = isOver ? "已超支" : "尚可用";

    item.append(title, amounts, progress, status);
    fragment.appendChild(item);
  }

  elements.budgetList.appendChild(fragment);
}

function updateBudgetAlert() {
  const totals = categoryTotals(state.transactions, state.month, "expense");
  const alerts = state.budgets
    .map(budget => {
      const spent = totals.get(budget.categoryId) || 0;
      if (spent <= budget.amount) {
        return null;
      }
      const category = state.categories.find(cat => cat.id === budget.categoryId);
      return `${category?.name || "分類"} 超支 ${formatCurrency(spent - budget.amount)}`;
    })
    .filter(Boolean);

  if (alerts.length) {
    elements.budgetAlert.textContent = `本月預算提醒：${alerts.join("、")}`;
    elements.budgetAlert.classList.remove("hidden");
  } else {
    elements.budgetAlert.textContent = "";
    elements.budgetAlert.classList.add("hidden");
  }
}

function renderTransactions() {
  const monthTx = filterTransactionsByMonth(state.transactions, state.month);
  elements.txList.replaceChildren();
  if (!monthTx.length) {
    const emptyRow = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 7;
    cell.className = "muted";
    cell.textContent = "尚無交易";
    emptyRow.appendChild(cell);
    elements.txList.appendChild(emptyRow);
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const tx of monthTx) {
    const row = document.createElement("tr");
    const label = tx.type === "income" ? "收入" : "支出";
    const amount = tx.type === "income" ? `+${formatCurrency(tx.amount)}` : `-${formatCurrency(tx.amount)}`;

    const cells = [
      tx.date,
      label,
      tx.category,
      tx.account,
      amount,
      tx.note || ""
    ];

    for (const value of cells) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.appendChild(cell);
    }

    const actionCell = document.createElement("td");
    const button = document.createElement("button");
    button.dataset.id = tx.id;
    button.textContent = "刪除";
    actionCell.appendChild(button);
    row.appendChild(actionCell);

    fragment.appendChild(row);
  }
  elements.txList.appendChild(fragment);
}

function renderCharts() {
  const totals = categoryTotals(state.transactions, state.month, "expense");
  const labels = [];
  const values = [];
  const colors = [];

  for (const [categoryId, value] of totals.entries()) {
    const category = state.categories.find(cat => cat.id === categoryId);
    labels.push(category?.name || "其他");
    values.push(value);
    colors.push(category?.color || "#7c6f64");
  }

  const pieData = {
    labels,
    datasets: [
      {
        data: values,
        backgroundColor: colors
      }
    ]
  };

  if (!pieChart) {
    pieChart = new Chart(document.getElementById("pie-chart"), {
      type: "doughnut",
      data: pieData,
      options: {
        plugins: {
          legend: {
            position: "bottom"
          }
        }
      }
    });
  } else {
    pieChart.data = pieData;
    pieChart.update();
  }

  const series = dailyBalanceSeries(state.transactions, state.month);
  const lineData = {
    labels: series.map(point => point.date),
    datasets: [
      {
        label: "每日結餘",
        data: series.map(point => point.value),
        borderColor: "#0f3d3e",
        backgroundColor: "rgba(15, 61, 62, 0.15)",
        fill: true,
        tension: 0.3
      }
    ]
  };

  if (!lineChart) {
    lineChart = new Chart(document.getElementById("line-chart"), {
      type: "line",
      data: lineData,
      options: {
        plugins: {
          legend: { display: false }
        }
      }
    });
  } else {
    lineChart.data = lineData;
    lineChart.update();
  }
}

function checkBudgetWarning(categoryId, month = state.month) {
  const budget = state.budgets.find(item => item.categoryId === categoryId);
  if (!budget) {
    return "";
  }
  const totals = categoryTotals(state.transactions, month, "expense");
  const spent = totals.get(categoryId) || 0;
  if (spent > budget.amount) {
    const category = state.categories.find(cat => cat.id === categoryId);
    return `${category?.name || "分類"} 已超出預算 ${formatCurrency(spent - budget.amount)}`;
  }
  return "";
}

function showToast(message, variant) {
  elements.toast.textContent = message;
  elements.toast.classList.remove("hidden", "warn");
  if (variant === "warn") {
    elements.toast.classList.add("warn");
  }
  setTimeout(() => {
    elements.toast.classList.add("hidden");
  }, 2800);
}

function registerServiceWorker() {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("./sw.js");
    });
  }
}

init();
