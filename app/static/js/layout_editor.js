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
  // Ctrl+C/Ctrl+Vのクリップボードはページ内のJS変数のみに保持する
  // (OSクリップボードAPIは使わない — このエディタ内で完結する用途のみのため)。
  // idはコピー時点では持たせず、貼り付けのたびに新規発行する。
  let clipboard = [];
  let pasteCount = 0;
  const PASTE_OFFSET = 24;

  // Ctrl+Z/Ctrl+Shift+Z(またはCtrl+Y)のUndo/Redoは、コピペと同様ページ内の
  // JS変数のみで完結させる。差分ベースのコマンドパターンではなく、items配列
  // 全体のスナップショットを操作の直前にpushする単純な方式にしている
  // (ドラッグ/リサイズ/位置揃え/追加/削除/貼り付け/プロパティ編集など操作の
  // 種類が多く、それぞれに逆操作を実装するより素直で壊れにくいため)。
  // layout自体のid/name(メタ情報)はUndo対象に含めない — コピー機能が
  // アイテムのみを対象にしているのと同様、スコープをアイテム操作に揃えている。
  let undoStack = [];
  let redoStack = [];
  const MAX_HISTORY = 50;

  // サーバー未保存の変更があるかどうか。beforeunloadで画面離脱前の警告を
  // 出すために使う(保存成功時のみfalseに戻す)。
  let isDirty = false;
  function markDirty() {
    isDirty = true;
  }

  function snapshotItems() {
    return state.items.map((it) => ({ ...it }));
  }

  // 操作を実際に適用する直前に呼ぶ(適用後ではない) — スタックには
  // 「その操作が起きる前の状態」を積む。
  function pushHistory() {
    markDirty();
    undoStack.push(snapshotItems());
    if (undoStack.length > MAX_HISTORY) undoStack.shift();
    redoStack = [];
  }

  // Undo後、元選択されていたidが削除/貼り付け等で意味を持たない場合が
  // あるため、選択状態は素直にクリアする(どの操作を取り消したかによらず
  // 一貫した挙動にするため)。
  function undo() {
    if (undoStack.length === 0) return;
    markDirty();
    redoStack.push(snapshotItems());
    state.items = undoStack.pop();
    renderStatus();
    renderItems();
    selectOnly(null);
  }

  function redo() {
    if (redoStack.length === 0) return;
    markDirty();
    undoStack.push(snapshotItems());
    state.items = redoStack.pop();
    renderStatus();
    renderItems();
    selectOnly(null);
  }

  // このページは(HTMXのhx-boostを使わない)通常のマルチページ遷移なので、
  // サイドバーのリンククリック・タブを閉じる・リロードのいずれもbeforeunloadで
  // 一律に捕捉できる。ブラウザ標準の確認ダイアログはメッセージ文言を
  // カスタマイズできない仕様のため、returnValueの中身自体に意味はない。
  window.addEventListener("beforeunload", (e) => {
    if (!isDirty) return;
    e.preventDefault();
    e.returnValue = "";
  });

  const MIN_ZOOM = 0.25;
  const MAX_ZOOM = 2;
  let zoom = 1;

  const metaId = document.getElementById("meta-id");
  const metaName = document.getElementById("meta-name");
  const metaWidth = document.getElementById("meta-width");
  const metaHeight = document.getElementById("meta-height");
  const addBtn = document.getElementById("add-item-btn");
  const addDividerBtn = document.getElementById("add-divider-btn");
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
  const fieldTagIdRow = document.getElementById("item-tag-id-row");
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
  const distributeButtons = {
    x: document.getElementById("distribute-horizontal-btn"),
    y: document.getElementById("distribute-vertical-btn"),
  };

  // 区切り線は「細い矩形」として使うため、装置(最小20px)より小さい最小
  // サイズを許可する。ドラッグリサイズとプロパティパネルのW/H入力の両方で
  // 使う共通の基準値(以前はドラッグリサイズ側にしか反映されておらず、
  // パネルの入力欄には装置向けのmin="10"がHTML側に直書きされたまま残っていた)。
  function minSizeFor(item) {
    return item.type === "divider" ? 2 : 20;
  }

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
    // 区切り線は装置ではないのでこの件数には含めない。
    const count = state.items.filter((it) => it.type !== "divider").length;
    statusEl.textContent = t("layout_editor.item_count", { count });
  }

  function renderItems() {
    canvas.innerHTML = "";
    state.items.forEach((item) => {
      const box = document.createElement("div");
      box.className =
        "eq-editable-box" +
        (item.type === "divider" ? " eq-editable-box--divider" : "") +
        (selectedIds.has(item.id) ? " is-selected" : "");
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
      // 区切り線はタグ・稼働状態と無関係なので、tagId欄はそもそも見せない。
      fieldTagIdRow.hidden = item.type === "divider";
      fieldLabel.value = item.label;
      fieldTagId.value = item.tagId;
      fieldX.value = item.x;
      fieldY.value = item.y;
      fieldW.min = minSizeFor(item);
      fieldH.min = minSizeFor(item);
      fieldW.value = item.w;
      fieldH.value = item.h;
    } else {
      panelEmpty.hidden = true;
      panelForm.hidden = true;
      panelMulti.hidden = false;
      multiCountEl.textContent = t("layout_editor.multi_selected", { count: selectedIds.size });
    }
    // 位置揃えボタンは常にツールバーに表示し(サイドパネルとは違い選択状況に
    // 応じて隠れない)、2件以上選択されている場合のみ活性化する。
    Object.values(alignButtons).forEach((btn) => {
      btn.disabled = selectedIds.size < 2;
    });
    // 均等配置は「両端を固定し、間を等間隔にする」操作のため、間に最低1件は
    // 挟まっている必要がある(3件以上)。2件だと位置揃えと区別がつかない。
    Object.values(distributeButtons).forEach((btn) => {
      btn.disabled = selectedIds.size < 3;
    });
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
    // ドラッグ中の各pointermoveごとではなく、ジェスチャー開始時に1回だけ
    // pushする(1回のドラッグ操作 = 1回のUndo、という粒度に揃えるため)。
    pushHistory();
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
    // リサイズ操作1回 = Undo1回、という粒度に揃えるため開始時に1回だけpushする。
    pushHistory();
    // リサイズは常に単一の装置が対象なので、複数選択中でもこの1件に絞る。
    selectOnly(item.id);
    const startX = e.clientX;
    const startY = e.clientY;
    const originW = item.w;
    const originH = item.h;
    // 横に伸ばせば横線、縦に伸ばせば縦線になる。
    const minSize = minSizeFor(item);

    function onMove(ev) {
      item.w = Math.max(minSize, Math.round(originW + (ev.clientX - startX) / zoom));
      item.h = Math.max(minSize, Math.round(originH + (ev.clientY - startY) / zoom));
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
    pushHistory();
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

  // 両端(先頭・末尾、位置でソート)は固定したまま、間の装置を等間隔になる
  // ように再配置する。等間隔の基準は中心間の距離ではなく、隣接する矩形の
  // 隙間(edge-to-edge)を揃える方式にしている(サイズが不揃いの装置群でも
  // 見た目が破綻しにくいため)。
  function distributeSelected(axis) {
    const items = selectedItems();
    if (items.length < 3) return;
    pushHistory();
    const sizeKey = axis === "x" ? "w" : "h";
    const sorted = [...items].sort((a, b) => a[axis] - b[axis]);
    const first = sorted[0];
    const last = sorted[sorted.length - 1];
    const span = last[axis] + last[sizeKey] - first[axis];
    const totalSize = sorted.reduce((sum, it) => sum + it[sizeKey], 0);
    const gap = (span - totalSize) / (sorted.length - 1);

    let cursor = first[axis] + first[sizeKey] + gap;
    for (let i = 1; i < sorted.length - 1; i++) {
      const it = sorted[i];
      it[axis] = Math.max(0, Math.round(cursor));
      cursor = it[axis] + it[sizeKey] + gap;
    }
    renderItems();
    highlightSelection();
  }

  Object.keys(distributeButtons).forEach((axis) => {
    distributeButtons[axis].addEventListener("click", () => distributeSelected(axis));
  });

  canvas.addEventListener("pointerdown", (e) => {
    if (e.target === canvas) selectOnly(null);
  });

  document.addEventListener("keydown", (e) => {
    const active = document.activeElement;
    // フォーカスがテキスト入力中の場合はブラウザ標準のコピペを優先し、
    // ショートカットを奪わない(ラベル編集中にCtrl+Cした場合など)。
    if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.isContentEditable)) {
      return;
    }
    const isCopy = (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "c";
    const isPaste = (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "v";
    // Redoは環境によってCtrl+Shift+Z(Mac系の慣習)とCtrl+Y(Windows系の慣習)の
    // どちらも使われるため両方を受け付ける。
    const isUndo = (e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === "z";
    const isRedo =
      (e.ctrlKey || e.metaKey) && ((e.shiftKey && e.key.toLowerCase() === "z") || e.key.toLowerCase() === "y");

    if (isUndo) {
      e.preventDefault();
      undo();
      return;
    } else if (isRedo) {
      e.preventDefault();
      redo();
      return;
    } else if (isCopy) {
      if (selectedIds.size === 0) return;
      e.preventDefault();
      // tagIdはコピーしない — 貼り付け後にそのまま保存すると同一tagIdの重複と
      // なりサーバー側バリデーションで弾かれるため、他の装置と同様「未割り当て」
      // の状態で複製し、後から手動で割り当てる運用に合わせる。
      clipboard = selectedItems().map((it) => ({ label: it.label, x: it.x, y: it.y, w: it.w, h: it.h, type: it.type }));
      pasteCount = 0;
    } else if (isPaste) {
      if (clipboard.length === 0) return;
      e.preventDefault();
      pushHistory();
      pasteCount += 1;
      const offset = PASTE_OFFSET * pasteCount;
      const newIds = [];
      clipboard.forEach((snapshot) => {
        const id = `item-${nextSeq++}`;
        state.items.push({
          id,
          label: snapshot.label,
          x: Math.max(0, snapshot.x + offset),
          y: Math.max(0, snapshot.y + offset),
          w: snapshot.w,
          h: snapshot.h,
          tagId: "",
          type: snapshot.type,
        });
        newIds.push(id);
      });
      renderStatus();
      renderItems();
      selectedIds = new Set(newIds);
      renderSelectionPanel();
      highlightSelection();
    }
  });

  // minFnを渡した数値フィールド(w/h)は、直接入力された値もドラッグリサイズと
  // 同じ最小サイズ(minSizeFor)でクランプする — HTMLのmin属性はスピナーの
  // 挙動には効くが、キー入力そのものを止めるわけではないため、両方揃える。
  function bindField(el, key, isNumber, minFn) {
    // 1キー入力ごとにpushすると「1文字ずつUndoする」形になり使いづらいため、
    // フォーカスしてから最初のinputでのみpushする(フォーカスを外すまでの
    // 一連の編集をまとめて1回のUndoにする)。
    let sessionStarted = false;
    el.addEventListener("focus", () => {
      sessionStarted = false;
    });
    el.addEventListener("input", () => {
      const item = primaryItem();
      if (!item) return;
      if (!sessionStarted) {
        pushHistory();
        sessionStarted = true;
      }
      if (isNumber) {
        const raw = Math.round(Number(el.value) || 0);
        item[key] = minFn ? Math.max(minFn(item), raw) : raw;
      } else {
        item[key] = el.value;
      }
      renderItems();
    });
  }
  bindField(fieldLabel, "label", false);
  bindField(fieldTagId, "tagId", false);
  bindField(fieldX, "x", true);
  bindField(fieldY, "y", true);
  bindField(fieldW, "w", true, minSizeFor);
  bindField(fieldH, "h", true, minSizeFor);

  deleteBtn.addEventListener("click", () => {
    const item = primaryItem();
    if (!item) return;
    pushHistory();
    state.items = state.items.filter((it) => it.id !== item.id);
    renderStatus();
    renderItems();
    selectOnly(null);
  });

  deleteMultiBtn.addEventListener("click", () => {
    pushHistory();
    state.items = state.items.filter((it) => !selectedIds.has(it.id));
    renderStatus();
    renderItems();
    selectOnly(null);
  });

  addBtn.addEventListener("click", () => {
    pushHistory();
    const id = `item-${nextSeq++}`;
    state.items.push({
      id,
      label: t("layout_editor.new_item_label"),
      x: 40,
      y: 40,
      w: 120,
      h: 80,
      tagId: "",
      type: "equipment",
    });
    renderStatus();
    renderItems();
    selectOnly(id);
  });

  addDividerBtn.addEventListener("click", () => {
    pushHistory();
    const id = `item-${nextSeq++}`;
    state.items.push({
      id,
      label: t("layout_editor.new_divider_label"),
      x: 40,
      y: 40,
      w: 200,
      h: 4,
      tagId: "",
      type: "divider",
    });
    renderStatus();
    renderItems();
    selectOnly(id);
  });

  metaId.addEventListener("input", () => {
    markDirty();
    state.id = metaId.value;
  });
  metaName.addEventListener("input", () => {
    markDirty();
    state.name = metaName.value;
  });
  // 幅・高さはキャンバスサイズ固定方針のためUIから外しているが、内部の
  // state.width/heightとこの配線自体は残す(#meta-width/#meta-heightを
  // テンプレートに復活させればUIからの変更をそのまま復元できる)。
  if (metaWidth) {
    metaWidth.addEventListener("input", () => {
      markDirty();
      state.width = Number(metaWidth.value) || 100;
      renderCanvasSize();
    });
  }
  if (metaHeight) {
    metaHeight.addEventListener("input", () => {
      markDirty();
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
        type: it.type,
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
        isDirty = false;
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
