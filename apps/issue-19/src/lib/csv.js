import { normalizeDateInput } from "./date.js";

const HEADER = ["日期", "類型", "金額", "分類", "帳戶", "備註"];

export function parseCsv(text) {
  const rows = [];
  let row = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"') {
      if (inQuotes && next === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (!inQuotes && (char === "," || char === "\n" || char === "\r")) {
      row.push(current);
      current = "";

      if (char === "\r" && next === "\n") {
        i += 1;
      }

      if (char === "\n" || char === "\r") {
        if (row.length > 1 || row.some(cell => cell.trim() !== "")) {
          rows.push(row);
        }
        row = [];
      }
      continue;
    }

    current += char;
  }

  if (current.length || row.length) {
    row.push(current);
    rows.push(row);
  }

  return rows.map(cols => cols.map(value => value.trim()));
}

export function serializeCsv(rows) {
  return rows
    .map(row =>
      row
        .map(value => {
          const stringValue = String(value ?? "");
          if (stringValue.includes(",") || stringValue.includes("\n") || stringValue.includes('"')) {
            return `"${stringValue.replace(/"/g, '""')}"`;
          }
          return stringValue;
        })
        .join(",")
    )
    .join("\n");
}

export function transactionsToCsv(transactions) {
  const rows = [HEADER];
  for (const tx of transactions) {
    rows.push([
      tx.date,
      tx.type === "income" ? "收入" : "支出",
      tx.amount,
      tx.category,
      tx.account,
      tx.note || ""
    ]);
  }
  return serializeCsv(rows);
}

export function csvToTransactions(text) {
  const rows = parseCsv(text);
  if (rows.length === 0) {
    throw new Error("CSV 內容為空");
  }

  const header = rows[0];
  const normalizedHeader = header.map(value => value.replace(/\s+/g, ""));
  const normalizedExpected = HEADER.map(value => value.replace(/\s+/g, ""));
  if (normalizedHeader.join(",") !== normalizedExpected.join(",")) {
    throw new Error("CSV 標題不符合標準格式");
  }

  const dataRows = rows.slice(1).filter(row => row.length && row.some(cell => cell));
  return dataRows.map(row => {
    const [date, typeLabel, amountValue, category, account, note] = row;
    if (!date || !typeLabel || !amountValue || !category || !account) {
      throw new Error("CSV 欄位不可為空");
    }
    const normalizedDate = normalizeDateInput(date);
    const type = typeLabel === "收入" ? "income" : typeLabel === "支出" ? "expense" : null;
    if (!type) {
      throw new Error(`無法辨識的類型: ${typeLabel}`);
    }
    const amount = Number(amountValue);
    if (!Number.isFinite(amount) || amount < 0) {
      throw new Error(`金額格式錯誤: ${amountValue}`);
    }
    return {
      date: normalizedDate,
      type,
      amount,
      category,
      account,
      note: note || ""
    };
  });
}

export function csvHeader() {
  return HEADER.slice();
}
