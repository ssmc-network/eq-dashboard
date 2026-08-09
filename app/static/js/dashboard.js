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
      statusEl.textContent = t("dashboard.refresh_status_on", { interval });
    } else {
      statusEl.textContent = t("dashboard.refresh_status_off");
    }
  }

  modeEl.addEventListener("change", apply);
  intervalEl.addEventListener("change", apply);
  apply();

  const layoutSwitcher = document.getElementById("layout-switcher");
  if (layoutSwitcher) {
    layoutSwitcher.addEventListener("change", () => {
      window.location.href = `/ui/dashboard/${layoutSwitcher.value}`;
    });
  }

  const fullscreenBtn = document.getElementById("fullscreen-btn");
  const fullscreenWrap = document.getElementById("dashboard-canvas-wrap");
  const fullscreenExitBtn = document.getElementById("fullscreen-exit-btn");
  if (fullscreenBtn && fullscreenWrap && fullscreenExitBtn) {
    function isFullscreen() {
      return document.fullscreenElement === fullscreenWrap;
    }

    // transformは#dashboard-items内の.dashboard-canvas(auto-refreshのたびに
    // 作り直される)に適用するため、htmxのswap後も再計算が必要。
    function applyFullscreenScale() {
      const canvasEl = target.querySelector(".dashboard-canvas");
      if (!canvasEl) return;
      if (!isFullscreen()) {
        canvasEl.style.transform = "";
        return;
      }
      const scale = Math.min(window.innerWidth / canvasEl.offsetWidth, window.innerHeight / canvasEl.offsetHeight);
      canvasEl.style.transform = `scale(${scale})`;
    }

    function enterFullscreen() {
      fullscreenWrap.requestFullscreen();
    }

    function exitFullscreen() {
      document.exitFullscreen();
    }

    fullscreenBtn.addEventListener("click", () => {
      if (isFullscreen()) {
        exitFullscreen();
      } else {
        enterFullscreen();
      }
    });
    // ツールバーのボタンはfullscreenWrapの外にあり、全画面中は視覚的に隠れて
    // クリックできなくなるため、fullscreenWrap内部にも終了ボタンを置く。
    fullscreenExitBtn.addEventListener("click", exitFullscreen);

    document.addEventListener("fullscreenchange", () => {
      fullscreenBtn.textContent = isFullscreen() ? t("dashboard.fullscreen_exit") : t("dashboard.fullscreen_enter");
      applyFullscreenScale();
    });

    window.addEventListener("resize", () => {
      if (isFullscreen()) applyFullscreenScale();
    });

    target.addEventListener("htmx:afterSwap", applyFullscreenScale);
  }
})();
