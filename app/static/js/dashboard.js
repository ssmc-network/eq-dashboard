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
  if (fullscreenBtn && fullscreenWrap) {
    function isFullscreen() {
      return document.fullscreenElement === fullscreenWrap;
    }

    // 通常表示でも、キャンバスをラップ領域に収まるようscale-to-fitする
    // (画面の空きスペースを有効活用するため)。全画面表示中はウィンドウ
    // 全体に、それ以外はラップのクライアント領域(パディング分を除く)に
    // フィットさせる。transformは#dashboard-items内の.dashboard-canvas
    // (auto-refreshのたびに作り直される)に適用するため、htmxのswap後も
    // 再計算が必要。
    function applyCanvasScale() {
      const canvasEl = target.querySelector(".dashboard-canvas");
      if (!canvasEl) return;
      let availableWidth;
      let availableHeight;
      if (isFullscreen()) {
        availableWidth = window.innerWidth;
        availableHeight = window.innerHeight;
      } else {
        const style = window.getComputedStyle(fullscreenWrap);
        availableWidth = fullscreenWrap.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
        availableHeight = fullscreenWrap.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
      }
      const scale = Math.min(availableWidth / canvasEl.offsetWidth, availableHeight / canvasEl.offsetHeight);
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

    document.addEventListener("fullscreenchange", () => {
      fullscreenBtn.textContent = isFullscreen() ? t("dashboard.fullscreen_exit") : t("dashboard.fullscreen_enter");
      applyCanvasScale();
    });

    // window resizeだけでは、サイドバー折りたたみ(ウィンドウサイズは
    // 変わらずラップの幅だけ変わる)を捉えられないため、ラップ自体の
    // サイズ変化をResizeObserverで監視する。
    new ResizeObserver(applyCanvasScale).observe(fullscreenWrap);
    target.addEventListener("htmx:afterSwap", applyCanvasScale);
    applyCanvasScale();
  }
})();
