(function () {
  const modeEl = document.getElementById("refresh-mode");
  const intervalEl = document.getElementById("refresh-interval");
  const statusEl = document.getElementById("refresh-status");
  const target = document.getElementById("dashboard-items");
  if (!modeEl || !intervalEl || !target) return;

  const refreshUrl = target.getAttribute("data-refresh-url");
  let timerId = null;

  function normalizedInterval() {
    const n = parseInt(intervalEl.value, 10);
    return Number.isInteger(n) && n >= 1 ? n : 10;
  }

  function refreshOnce() {
    htmx.ajax("GET", refreshUrl, { target: "#dashboard-items", swap: "innerHTML" });
  }

  function apply() {
    if (timerId !== null) {
      clearInterval(timerId);
      timerId = null;
    }

    const interval = normalizedInterval();
    intervalEl.value = interval;

    const isOn = modeEl.value === "on";
    intervalEl.disabled = !isOn;

    if (isOn) {
      timerId = setInterval(refreshOnce, interval * 1000);
      statusEl.textContent = `${interval}秒ごとに更新`;
    } else {
      statusEl.textContent = "自動更新なし";
    }
  }

  modeEl.addEventListener("change", apply);
  intervalEl.addEventListener("change", apply);
  apply();
})();
