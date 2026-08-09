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
  let selectedId = null;

  const metaId = document.getElementById("meta-id");
  const metaName = document.getElementById("meta-name");
  const metaWidth = document.getElementById("meta-width");
  const metaHeight = document.getElementById("meta-height");
  const addBtn = document.getElementById("add-item-btn");
  const saveBtn = document.getElementById("save-btn");
  const downloadBtn = document.getElementById("download-btn");
  const statusEl = document.getElementById("editor-status");
  const saveMessage = document.getElementById("save-message");

  const panelEmpty = document.getElementById("editor-panel-empty");
  const panelForm = document.getElementById("editor-panel-form");
  const fieldLabel = document.getElementById("item-label");
  const fieldTagId = document.getElementById("item-tag-id");
  const fieldX = document.getElementById("item-x");
  const fieldY = document.getElementById("item-y");
  const fieldW = document.getElementById("item-w");
  const fieldH = document.getElementById("item-h");
  const deleteBtn = document.getElementById("delete-item-btn");

  function findItem(id) {
    return state.items.find((it) => it.id === id) || null;
  }

  function renderCanvasSize() {
    canvas.style.width = `${state.width}px`;
    canvas.style.height = `${state.height}px`;
  }

  function renderStatus() {
    statusEl.textContent = t("layout_editor.item_count", { count: state.items.length });
  }

  function renderItems() {
    canvas.innerHTML = "";
    state.items.forEach((item) => {
      const box = document.createElement("div");
      box.className = "eq-editable-box" + (item.id === selectedId ? " is-selected" : "");
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

      box.addEventListener("pointerdown", (e) => startDrag(e, item, box));
      handle.addEventListener("pointerdown", (e) => startResize(e, item, box));

      canvas.appendChild(box);
    });
  }

  // ドラッグ/リサイズ中に握っているbox要素をrenderItems()のinnerHTML再構築で
  // 差し替えてしまうと、以後のstyle更新がDOMから外れた古い要素に対して行われ
  // 画面に反映されなくなる(次のクリックで再描画されるまで追従して見えない不具合の原因)。
  // 選択状態の切り替えはDOMを作り直さず、クラスの付け替えだけで済ませる。
  function highlightSelection() {
    canvas.querySelectorAll(".eq-editable-box").forEach((box) => {
      box.classList.toggle("is-selected", box.dataset.itemId === selectedId);
    });
  }

  function select(id) {
    selectedId = id;
    const item = findItem(id);
    if (!item) {
      panelEmpty.hidden = false;
      panelForm.hidden = true;
      highlightSelection();
      return;
    }
    panelEmpty.hidden = true;
    panelForm.hidden = false;
    fieldLabel.value = item.label;
    fieldTagId.value = item.tagId;
    fieldX.value = item.x;
    fieldY.value = item.y;
    fieldW.value = item.w;
    fieldH.value = item.h;
    highlightSelection();
  }

  function startDrag(e, item, box) {
    e.preventDefault();
    e.stopPropagation();
    select(item.id);
    const startX = e.clientX;
    const startY = e.clientY;
    const originX = item.x;
    const originY = item.y;

    function onMove(ev) {
      item.x = Math.max(0, Math.round(originX + (ev.clientX - startX)));
      item.y = Math.max(0, Math.round(originY + (ev.clientY - startY)));
      box.style.left = `${item.x}px`;
      box.style.top = `${item.y}px`;
      if (selectedId === item.id) {
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
    select(item.id);
    const startX = e.clientX;
    const startY = e.clientY;
    const originW = item.w;
    const originH = item.h;

    function onMove(ev) {
      item.w = Math.max(20, Math.round(originW + (ev.clientX - startX)));
      item.h = Math.max(20, Math.round(originH + (ev.clientY - startY)));
      box.style.width = `${item.w}px`;
      box.style.height = `${item.h}px`;
      if (selectedId === item.id) {
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

  canvas.addEventListener("pointerdown", (e) => {
    if (e.target === canvas) select(null);
  });

  function bindField(el, key, isNumber) {
    el.addEventListener("input", () => {
      const item = findItem(selectedId);
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
    state.items = state.items.filter((it) => it.id !== selectedId);
    renderStatus();
    selectedId = null;
    renderItems();
    select(null);
  });

  addBtn.addEventListener("click", () => {
    const id = `item-${nextSeq++}`;
    state.items.push({ id, label: t("layout_editor.new_item_label"), x: 40, y: 40, w: 120, h: 80, tagId: "" });
    renderStatus();
    selectedId = id;
    renderItems();
    select(id);
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
})();
