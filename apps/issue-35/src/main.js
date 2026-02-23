import {
  formatPace,
  formatPaceInput,
  paceToSpeed,
  parsePaceInput,
  speedToPace
} from "./lib/pace.js";

const speedInput = document.getElementById("speed-input");
const paceInput = document.getElementById("pace-input");
const paceOutput = document.getElementById("pace-output");
const speedOutput = document.getElementById("speed-output");
const errorMessage = document.getElementById("error-message");
const form = document.getElementById("converter-form");
const resetButton = document.getElementById("reset-btn");
const modeButtons = document.querySelectorAll(".mode-button");
const quickPicks = document.getElementById("quick-picks");
const offlineStatus = document.getElementById("offline-status");

const speedField = speedInput.closest("label");
const paceField = paceInput.closest("label");

const SPEED_PRESETS = [
  { label: "恢復 6.0", value: 6.0 },
  { label: "慢跑 8.0", value: 8.0 },
  { label: "馬拉松 10.0", value: 10.0 },
  { label: "節奏 12.0", value: 12.0 },
  { label: "間歇 15.0", value: 15.0 }
];

const PACE_PRESETS = [
  { label: "4'30\"", value: "4:30" },
  { label: "5'00\"", value: "5:00" },
  { label: "6'00\"", value: "6:00" },
  { label: "7'00\"", value: "7:00" },
  { label: "8'00\"", value: "8:00" }
];

let activeMode = "speed";

function setMode(mode) {
  activeMode = mode;
  modeButtons.forEach(button => {
    const isActive = button.dataset.mode === mode;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", String(isActive));
  });

  speedField.classList.toggle("is-active", mode === "speed");
  paceField.classList.toggle("is-active", mode === "pace");

  renderQuickPicks();
  clearError();
}

function setError(message) {
  errorMessage.textContent = message;
}

function clearError() {
  errorMessage.textContent = "";
}

function updateOutputs({ paceSeconds, speed }) {
  if (Number.isFinite(paceSeconds)) {
    paceOutput.textContent = formatPace(paceSeconds);
  } else {
    paceOutput.textContent = "--";
  }

  if (Number.isFinite(speed)) {
    speedOutput.textContent = speed.toFixed(1);
  } else {
    speedOutput.textContent = "--";
  }
}

function convertFromSpeed() {
  clearError();
  const speedValue = Number.parseFloat(speedInput.value);
  if (!Number.isFinite(speedValue) || speedValue <= 0) {
    throw new Error("請輸入有效的時速數值");
  }
  const pace = speedToPace(speedValue);
  const speed = Number(speedValue.toFixed(1));
  paceInput.value = formatPaceInput(pace);
  updateOutputs({ paceSeconds: pace.totalSeconds, speed });
}

function convertFromPace() {
  clearError();
  const pace = parsePaceInput(paceInput.value);
  const speed = paceToSpeed(pace.totalSeconds);
  speedInput.value = speed.toFixed(1);
  updateOutputs({ paceSeconds: pace.totalSeconds, speed });
}

function handleConvert(event) {
  event.preventDefault();
  try {
    if (activeMode === "speed") {
      convertFromSpeed();
    } else {
      convertFromPace();
    }
  } catch (error) {
    setError(error.message);
  }
}

function handleReset() {
  speedInput.value = "";
  paceInput.value = "";
  updateOutputs({ paceSeconds: null, speed: null });
  clearError();
}

function renderQuickPicks() {
  const presets = activeMode === "speed" ? SPEED_PRESETS : PACE_PRESETS;
  quickPicks.innerHTML = "";
  presets.forEach(preset => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = preset.label;
    button.addEventListener("click", () => {
      if (activeMode === "speed") {
        speedInput.value = String(preset.value.toFixed(1));
        convertFromSpeed();
      } else {
        paceInput.value = preset.value;
        convertFromPace();
      }
    });
    quickPicks.appendChild(button);
  });
}

function updateOfflineStatus() {
  if (!offlineStatus) {
    return;
  }
  offlineStatus.textContent = navigator.onLine
    ? "離線可用 · PWA Ready"
    : "離線模式 · 已套用快取";
}

modeButtons.forEach(button => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});

speedInput.addEventListener("focus", () => setMode("speed"));
paceInput.addEventListener("focus", () => setMode("pace"));

form.addEventListener("submit", handleConvert);
resetButton.addEventListener("click", handleReset);

window.addEventListener("online", updateOfflineStatus);
window.addEventListener("offline", updateOfflineStatus);

setMode(activeMode);

speedInput.value = "10.0";
try {
  convertFromSpeed();
} catch (error) {
  setError(error.message);
}

updateOfflineStatus();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("./sw.js").catch(() => {
      setError("PWA 快取註冊失敗，請稍後重試");
    });
  });
}
