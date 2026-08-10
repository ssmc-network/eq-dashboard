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

      // 幅/高さのinline styleを一旦リセットしてCSSの上限(max-height、幅は
      // 親いっぱい)基準で測り直す。前回shrink後の値を基準にすると、次に
      // 使える余地が広がったとき(ウィンドウを大きくした等)に縮んだまま
      // 戻らなくなるため。
      fullscreenWrap.style.width = "";
      fullscreenWrap.style.height = "";

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

      // 全画面表示はビューポート全体が背景になるため、キャンバスの縦横比と
      // 合わない分の余白(レターボックス)が出ても違和感は無い。通常表示は
      // wrap自体が枠付きのパネルなので、この余白がそのまま「使われていない
      // 箱」に見えてしまう — wrapの実寸をscale後のキャンバスに合わせて
      // 縮め、余白を無くす。
      if (!isFullscreen()) {
        const style = window.getComputedStyle(fullscreenWrap);
        const paddingX = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
        const paddingY = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
        fullscreenWrap.style.width = `${canvasEl.offsetWidth * scale + paddingX}px`;
        fullscreenWrap.style.height = `${canvasEl.offsetHeight * scale + paddingY}px`;
      }
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
    // 変わらずラップの幅だけ変わる)を捉えられないため、周囲の
    // サイズ変化をResizeObserverで監視する。監視対象はラップ自身ではなく
    // その親(.main)にしている — applyCanvasScale自身がラップの
    // width/heightをinline styleで書き換えるため、ラップ自身を監視すると
    // 「利用可能な領域が広がった(親が大きくなった)」という変化を検知
    // できず(ラップの実サイズはinline style値のまま変わらないため)、
    // ウィンドウを再度大きくしても縮んだままになってしまう。
    new ResizeObserver(applyCanvasScale).observe(fullscreenWrap.parentElement);
    target.addEventListener("htmx:afterSwap", applyCanvasScale);
    applyCanvasScale();
  }
})();
