(function () {
  const initialDataEl = document.getElementById("initial-layout");
  const canvas = document.getElementById("editor-canvas");
  if (!initialDataEl || !canvas) return;

  const initial = JSON.parse(initialDataEl.textContent);

  const state = {
    id: initial.layout.id || "",
    name: initial.layout.name || "",
    width: initial.layout.width || 1920,
    height: initial.layout.height || 1080,
    items: (initial.items || []).map((it) => ({ ...it })),
  };
  let originalId = initial.layout.id || "";
  let nextSeq = state.items.length + 1;
  // 複数選択に対応するため、単一idではなくSetで選択状態を持つ。
  // 1件だけ選択されている場合はプロパティパネルの編集フォームを、
  // 2件以上ならバウンディングボックス基準の位置揃えパネルを表示する。
  let selectedIds = new Set();

  const MIN_ZOOM = 0.25;
  const MAX_ZOOM = 2;
  let zoom = 1;

  const metaId = document.getElementById("meta-id");
  const metaName = document.getElementById("meta-name");
  const metaWidth = document.getElementById("meta-width");
  const metaHeight = document.getElementById("meta-height");
  const addBtn = document.getElementById("add-item-btn");
  const saveBtn = document.getElementById("save-btn");
  const downloadBtn = document.getElementById("download-btn");
  const statusEl = document.getElementById("editor-status");
  const saveMessage = document.getElementById("save-message");

  const canvasWrap = document.getElementById("editor-canvas-wrap");
  const canvasSpacer = document.getElementById("editor-canvas-spacer");
  const zoomOutBtn = document.getElementById("zoom-out-btn");
  const zoomInBtn = document.getElementById("zoom-in-btn");
  const zoomResetBtn = document.getElementById("zoom-reset-btn");
  const minimap = document.getElementById("editor-minimap");
  const minimapItemsLayer = document.getElementById("editor-minimap-items");
  const minimapViewport = document.getElementById("editor-minimap-viewport");

  const panelEmpty = document.getElementById("editor-panel-empty");
  const panelForm = document.getElementById("editor-panel-form");
  const panelMulti = document.getElementById("editor-panel-multi");
  const multiCountEl = document.getElementById("editor-panel-multi-count");
  const fieldLabel = document.getElementById("item-label");
  const fieldTagId = document.getElementById("item-tag-id");
  const fieldX = document.getElementById("item-x");
  const fieldY = document.getElementById("item-y");
  const fieldW = document.getElementById("item-w");
  const fieldH = document.getElementById("item-h");
  const deleteBtn = document.getElementById("delete-item-btn");
  const deleteMultiBtn = document.getElementById("delete-multi-btn");
  const alignButtons = {
    left: document.getElementById("align-left-btn"),
    "center-x": document.getElementById("align-center-x-btn"),
    right: document.getElementById("align-right-btn"),
    top: document.getElementById("align-top-btn"),
    "center-y": document.getElementById("align-center-y-btn"),
    bottom: document.getElementById("align-bottom-btn"),
  };

  function findItem(id) {
    return state.items.find((it) => it.id === id) || null;
  }

  function selectedItems() {
    return state.items.filter((it) => selectedIds.has(it.id));
  }

  // ちょうど1件だけ選択されている場合のみ、そのアイテムを返す
  // (プロパティパネルの単一編集フォームが対象とするアイテム)。
  function primaryItem() {
    if (selectedIds.size !== 1) return null;
    return findItem(Array.from(selectedIds)[0]);
  }

  function renderCanvasSize() {
    canvas.style.width = `${state.width}px`;
    canvas.style.height = `${state.height}px`;
    canvas.style.transformOrigin = "top left";
    canvas.style.transform = `scale(${zoom})`;
    // transformは見た目のサイズしか変えないため、canvasWrapのスクロール範囲を
    // 決めるのはこのspacerの明示的なwidth/height(実サイズ×zoom)。
    canvasSpacer.style.width = `${state.width * zoom}px`;
    canvasSpacer.style.height = `${state.height * zoom}px`;
    zoomResetBtn.textContent = `${Math.round(zoom * 100)}%`;
    renderMinimap();
  }

  function setZoom(nextZoom) {
    zoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Math.round(nextZoom * 20) / 20));
    renderCanvasSize();
  }

  function renderMinimapItems() {
    const scale = minimap.clientWidth / state.width;
    minimapItemsLayer.innerHTML = "";
    state.items.forEach((item) => {
      const dot = document.createElement("div");
      dot.className = "editor-minimap__item";
      dot.style.left = `${item.x * scale}px`;
      dot.style.top = `${item.y * scale}px`;
      dot.style.width = `${Math.max(2, item.w * scale)}px`;
      dot.style.height = `${Math.max(2, item.h * scale)}px`;
      minimapItemsLayer.appendChild(dot);
    });
  }

  // ミニマップは、キャンバスがビューポートより大きくスクロールバーが出ている
  // 場合限定で表示する(常に出すとキャンバスが十分小さい/十分ズームアウトされて
  // いる場合にただの縮小コピーが常駐するだけになり邪魔なため)。
  function renderMinimap() {
    const needsScroll = canvasWrap.scrollWidth > canvasWrap.clientWidth || canvasWrap.scrollHeight > canvasWrap.clientHeight;
    minimap.hidden = !needsScroll;
    if (!needsScroll) return;

    const scale = minimap.clientWidth / state.width;
    minimap.style.height = `${state.height * scale}px`;
    renderMinimapItems();

    const viewLeft = canvasWrap.scrollLeft / zoom;
    const viewTop = canvasWrap.scrollTop / zoom;
    const viewWidth = Math.min(state.width, canvasWrap.clientWidth / zoom);
    const viewHeight = Math.min(state.height, canvasWrap.clientHeight / zoom);

    minimapViewport.style.left = `${viewLeft * scale}px`;
    minimapViewport.style.top = `${viewTop * scale}px`;
    minimapViewport.style.width = `${viewWidth * scale}px`;
    minimapViewport.style.height = `${viewHeight * scale}px`;
  }

  minimap.addEventListener("pointerdown", (e) => {
    const rect = minimap.getBoundingClientRect();
    const scale = minimap.clientWidth / state.width;
    const targetX = (e.clientX - rect.left) / scale;
    const targetY = (e.clientY - rect.top) / scale;
    canvasWrap.scrollTo({
      left: Math.max(0, targetX * zoom - canvasWrap.clientWidth / 2),
      top: Math.max(0, targetY * zoom - canvasWrap.clientHeight / 2),
      behavior: "smooth",
    });
  });

  canvasWrap.addEventListener("scroll", renderMinimap);
  // window resizeだけでは、サイドバー折りたたみ(ウィンドウサイズは変わらず
  // canvasWrapの幅だけ変わる)を捉えられないため、canvasWrap自体のサイズ
  // 変化をResizeObserverで監視する。
  new ResizeObserver(renderMinimap).observe(canvasWrap);
  zoomOutBtn.addEventListener("click", () => setZoom(zoom - 0.1));
  zoomInBtn.addEventListener("click", () => setZoom(zoom + 0.1));
  zoomResetBtn.addEventListener("click", () => setZoom(1));

  function renderStatus() {
    statusEl.textContent = t("layout_editor.item_count", { count: state.items.length });
  }

  function renderItems() {
    canvas.innerHTML = "";
    state.items.forEach((item) => {
      const box = document.createElement("div");
      box.className = "eq-editable-box" + (selectedIds.has(item.id) ? " is-selected" : "");
      box.dataset.itemId = item.id;
      box.style.left = `${item.x}px`;
      box.style.top = `${item.y}px`;
      box.style.width = `${item.w}px`;
      box.style.height = `${item.h}px`;

      const label = document.createElement("span");
      label.className = "eq-editable-box__label";
      label.textContent = item.label || t("layout_editor.no_label");
      box.appendChild(label);

      const handle = document.createElement("span");
      handle.className = "eq-editable-box__resize-handle";
      box.appendChild(handle);

      box.addEventListener("pointerdown", (e) => {
        // Shift+クリックは選択のトグルのみ(ドラッグは開始しない)。
        if (e.shiftKey) {
          e.preventDefault();
          e.stopPropagation();
          toggleSelect(item.id);
          return;
        }
        // 既に複数選択の一部になっている装置をそのままドラッグした場合は
        // 選択集合を維持して全体を一緒に動かす。未選択の装置をドラッグした
        // 場合は単一選択に切り替えてから動かす。
        if (!selectedIds.has(item.id)) {
          selectOnly(item.id);
        }
        startDrag(e, item, box);
      });
      handle.addEventListener("pointerdown", (e) => startResize(e, item, box));

      canvas.appendChild(box);
    });
    renderMinimap();
  }

  // ドラッグ/リサイズ中に握っているbox要素をrenderItems()のinnerHTML再構築で
  // 差し替えてしまうと、以後のstyle更新がDOMから外れた古い要素に対して行われ
  // 画面に反映されなくなる(次のクリックで再描画されるまで追従して見えない不具合の原因)。
  // 選択状態の切り替えはDOMを作り直さず、クラスの付け替えだけで済ませる。
  function highlightSelection() {
    canvas.querySelectorAll(".eq-editable-box").forEach((box) => {
      box.classList.toggle("is-selected", selectedIds.has(box.dataset.itemId));
    });
  }

  // プロパティパネルは選択件数で3状態に分岐する: 0件(空表示) / 1件(編集フォーム) /
  // 2件以上(位置揃え・一括削除パネル)。選択状態そのもの(selectedIds)の更新は
  // 呼び出し側(selectOnly/toggleSelect)が担い、この関数は表示の同期のみを行う。
  function renderSelectionPanel() {
    const item = primaryItem();
    if (selectedIds.size === 0) {
      panelEmpty.hidden = false;
      panelForm.hidden = true;
      panelMulti.hidden = true;
    } else if (item) {
      panelEmpty.hidden = true;
      panelForm.hidden = false;
      panelMulti.hidden = true;
      fieldLabel.value = item.label;
      fieldTagId.value = item.tagId;
      fieldX.value = item.x;
      fieldY.value = item.y;
      fieldW.value = item.w;
      fieldH.value = item.h;
    } else {
      panelEmpty.hidden = true;
      panelForm.hidden = true;
      panelMulti.hidden = false;
      multiCountEl.textContent = t("layout_editor.multi_selected", { count: selectedIds.size });
    }
  }

  function selectOnly(id) {
    selectedIds = id === null ? new Set() : new Set([id]);
    renderSelectionPanel();
    highlightSelection();
  }

  function toggleSelect(id) {
    if (selectedIds.has(id)) {
      selectedIds.delete(id);
    } else {
      selectedIds.add(id);
    }
    renderSelectionPanel();
    highlightSelection();
  }

  function startDrag(e, item, box) {
    e.preventDefault();
    e.stopPropagation();
    // 複数選択中にその一員をドラッグした場合は選択されている全装置を対象に、
    // そうでなければドラッグ対象の1件だけを対象にする。
    const ids = selectedIds.has(item.id) && selectedIds.size > 1 ? new Set(selectedIds) : new Set([item.id]);
    const startX = e.clientX;
    const startY = e.clientY;
    const origins = new Map();
    ids.forEach((id) => {
      const it = findItem(id);
      if (it) origins.set(id, { x: it.x, y: it.y });
    });

    // ドラッグ中のマウス移動量(画面px)はズーム倍率で割ってキャンバス座標系に
    // 変換する(scale()は見た目だけを縮小・拡大するため)。renderItems()による
    // DOM再構築はここでは行わず(上記コメント参照)、対象各要素のstyleを
    // 直接書き換える。
    function onMove(ev) {
      const dx = (ev.clientX - startX) / zoom;
      const dy = (ev.clientY - startY) / zoom;
      ids.forEach((id) => {
        const it = findItem(id);
        const origin = origins.get(id);
        if (!it || !origin) return;
        it.x = Math.max(0, Math.round(origin.x + dx));
        it.y = Math.max(0, Math.round(origin.y + dy));
        const el = id === item.id ? box : canvas.querySelector(`[data-item-id="${id}"]`);
        if (el) {
          el.style.left = `${it.x}px`;
          el.style.top = `${it.y}px`;
        }
      });
      if (selectedIds.size === 1 && selectedIds.has(item.id)) {
        fieldX.value = item.x;
        fieldY.value = item.y;
      }
    }

    function onUp() {
      document.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerup", onUp);
    }

    document.addEventListener("pointermove", onMove);
    document.addEventListener("pointerup", onUp);
  }

  function startResize(e, item, box) {
    e.preventDefault();
    e.stopPropagation();
    // リサイズは常に単一の装置が対象なので、複数選択中でもこの1件に絞る。
    selectOnly(item.id);
    const startX = e.clientX;
    const startY = e.clientY;
    const originW = item.w;
    const originH = item.h;

    function onMove(ev) {
      item.w = Math.max(20, Math.round(originW + (ev.clientX - startX) / zoom));
      item.h = Math.max(20, Math.round(originH + (ev.clientY - startY) / zoom));
      box.style.width = `${item.w}px`;
      box.style.height = `${item.h}px`;
      if (selectedIds.has(item.id)) {
        fieldW.value = item.w;
        fieldH.value = item.h;
      }
    }

    function onUp() {
      document.removeEventListener("pointermove", onMove);
      document.removeEventListener("pointerup", onUp);
    }

    document.addEventListener("pointermove", onMove);
    document.addEventListener("pointerup", onUp);
  }

  function alignSelected(mode) {
    const items = selectedItems();
    if (items.length < 2) return;
    const minX = Math.min(...items.map((it) => it.x));
    const maxRight = Math.max(...items.map((it) => it.x + it.w));
    const minY = Math.min(...items.map((it) => it.y));
    const maxBottom = Math.max(...items.map((it) => it.y + it.h));
    const centerX = (minX + maxRight) / 2;
    const centerY = (minY + maxBottom) / 2;

    items.forEach((it) => {
      switch (mode) {
        case "left":
          it.x = minX;
          break;
        case "right":
          it.x = maxRight - it.w;
          break;
        case "top":
          it.y = minY;
          break;
        case "bottom":
          it.y = maxBottom - it.h;
          break;
        case "center-x":
          it.x = centerX - it.w / 2;
          break;
        case "center-y":
          it.y = centerY - it.h / 2;
          break;
      }
      it.x = Math.max(0, Math.round(it.x));
      it.y = Math.max(0, Math.round(it.y));
    });
    renderItems();
    highlightSelection();
  }

  Object.keys(alignButtons).forEach((mode) => {
    alignButtons[mode].addEventListener("click", () => alignSelected(mode));
  });

  canvas.addEventListener("pointerdown", (e) => {
    if (e.target === canvas) selectOnly(null);
  });

  function bindField(el, key, isNumber) {
    el.addEventListener("input", () => {
      const item = primaryItem();
      if (!item) return;
      item[key] = isNumber ? Math.round(Number(el.value) || 0) : el.value;
      renderItems();
    });
  }
  bindField(fieldLabel, "label", false);
  bindField(fieldTagId, "tagId", false);
  bindField(fieldX, "x", true);
  bindField(fieldY, "y", true);
  bindField(fieldW, "w", true);
  bindField(fieldH, "h", true);

  deleteBtn.addEventListener("click", () => {
    const item = primaryItem();
    if (!item) return;
    state.items = state.items.filter((it) => it.id !== item.id);
    renderStatus();
    renderItems();
    selectOnly(null);
  });

  deleteMultiBtn.addEventListener("click", () => {
    state.items = state.items.filter((it) => !selectedIds.has(it.id));
    renderStatus();
    renderItems();
    selectOnly(null);
  });

  addBtn.addEventListener("click", () => {
    const id = `item-${nextSeq++}`;
    state.items.push({ id, label: t("layout_editor.new_item_label"), x: 40, y: 40, w: 120, h: 80, tagId: "" });
    renderStatus();
    renderItems();
    selectOnly(id);
  });

  metaId.addEventListener("input", () => {
    state.id = metaId.value;
  });
  metaName.addEventListener("input", () => {
    state.name = metaName.value;
  });
  // 幅・高さはキャンバスサイズ固定方針のためUIから外しているが、内部の
  // state.width/heightとこの配線自体は残す(#meta-width/#meta-heightを
  // テンプレートに復活させればUIからの変更をそのまま復元できる)。
  if (metaWidth) {
    metaWidth.addEventListener("input", () => {
      state.width = Number(metaWidth.value) || 100;
      renderCanvasSize();
    });
  }
  if (metaHeight) {
    metaHeight.addEventListener("input", () => {
      state.height = Number(metaHeight.value) || 100;
      renderCanvasSize();
    });
  }

  function buildPayload() {
    return {
      schemaVersion: "1.0",
      layout: { id: state.id, name: state.name, width: state.width, height: state.height },
      items: state.items.map((it) => ({
        id: it.id,
        label: it.label,
        x: it.x,
        y: it.y,
        w: it.w,
        h: it.h,
        tagId: it.tagId,
      })),
    };
  }

  downloadBtn.addEventListener("click", () => {
    if (!state.id || !state.name) {
      window.alert(t("layout_editor.id_name_required"));
      return;
    }
    const blob = new Blob([JSON.stringify(buildPayload(), null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${state.id || "layout"}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });

  async function postSave(overwrite) {
    const params = new URLSearchParams({ original_id: originalId });
    if (overwrite) params.set("overwrite", "true");
    const res = await fetch(`/api/layouts/save?${params}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload()),
    });
    const data = await res.json();
    return { res, data };
  }

  saveBtn.addEventListener("click", async () => {
    if (!state.id || !state.name) {
      window.alert(t("layout_editor.id_name_required"));
      return;
    }
    saveBtn.disabled = true;
    const originalLabel = saveBtn.textContent;
    saveBtn.textContent = t("layout_editor.saving");
    saveMessage.className = "editor-save-message";
    saveMessage.textContent = "";
    try {
      let { res, data } = await postSave(false);

      if (res.status === 409 && data.needsConfirmation) {
        const confirmed = window.confirm(
          t("layout_editor.overwrite_confirm", { id: state.id, name: data.existingName })
        );
        if (!confirmed) {
          saveMessage.textContent = t("layout_editor.save_cancelled");
          return;
        }
        ({ res, data } = await postSave(true));
      }

      if (res.ok && data.ok) {
        saveMessage.textContent = t("layout_editor.save_ok", { id: data.id });
        saveMessage.classList.add("editor-save-message--ok");
        originalId = data.id;
      } else {
        saveMessage.textContent = t("layout_editor.save_failed", { errors: (data.errors || []).join(" / ") });
        saveMessage.classList.add("editor-save-message--error");
      }
    } catch (err) {
      saveMessage.textContent = t("layout_editor.network_error");
      saveMessage.classList.add("editor-save-message--error");
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = originalLabel;
    }
  });

  renderCanvasSize();
  renderItems();
  renderStatus();
  renderSelectionPanel();
})();
