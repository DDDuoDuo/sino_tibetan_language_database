(function () {
  const MAX_TOASTS = 3;
  const AUTO_DISMISS_MS = 1000;
  const STORAGE_KEY = "warning_toasts";

  let stackEl = null;
  let activeToasts = [];

  function normalizeType(t) {
    const c = (t || "b").toString().trim().toLowerCase();
    if (c === "r" || c === "g" || c === "b") return c;
    return "b";
  }

  function getToastVisualConfig(type) {
    const t = normalizeType(type);
    if (t === "r") {
        return {
        type: "r",
        borderColor: "#dc2626",
        icon: "✘",
        iconColor: "#dc2626"
        };
    }
    if (t === "g") {
        return {
        type: "g",
        borderColor: "#16a34a",
        icon: "✓",
        iconColor: "#16a34a"
        };
    }

    return {
        type: "b",
        borderColor: "#2563eb",
        icon: "i",
        iconColor: "#2563eb"
    };
  }

  function applyToastVisuals(toastEl, type) {
    const cfg = getToastVisualConfig(type);
    toastEl.dataset.toastType = cfg.type;
    toastEl.style.borderColor = cfg.borderColor;

    const iconEl = toastEl.querySelector(".warning-toast__icon");
    if (iconEl) {
        iconEl.textContent = cfg.icon;
        iconEl.style.color = cfg.iconColor;
        iconEl.style.borderColor = cfg.iconColor;
    }
  }      

  function loadStoredToasts() {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (!raw) return [];
      const arr = JSON.parse(raw);
      return Array.isArray(arr) ? arr : [];
    } catch {
      return [];
    }
  }
  
  function saveStoredToasts(list) {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(list || []));
    } catch {
    //   ignore
    }
  }
  
  function removeStoredToast(id) {
    const list = loadStoredToasts().filter(t => t.id !== id);
    saveStoredToasts(list);
  }    

  function ensureStack() {
    if (stackEl && document.contains(stackEl)) return stackEl;

    const body = document.body || document.getElementsByTagName("body")[0];
    if (!body) return null;

    stackEl = document.getElementById("warning-toast-stack");
    if (!stackEl) {
      stackEl = document.createElement("div");
      stackEl.id = "warning-toast-stack";
      body.appendChild(stackEl);
    }
    return stackEl;
  }

  function dismissToast(toastEl) {
    if (!toastEl || toastEl.classList.contains("leaving")) return;

    toastEl.classList.add("leaving");

    const id = toastEl.dataset.toastId;
    if (id) {
      removeStoredToast(id);
    }

    toastEl.addEventListener(
      "animationend",
      () => {
        if (toastEl.parentNode) {
          toastEl.parentNode.removeChild(toastEl);
        }
        activeToasts = activeToasts.filter((t) => t !== toastEl);
      },
      { once: true }
    );
  }

  function pop_up(message, type) {
      if (!message) return;
      if (window.I18N && typeof I18N.translateLiteral === "function") {
        message = I18N.translateLiteral(message);
      }
  
      const stack = ensureStack();
      if (!stack) return;
  
      const id = "toast_" + Date.now() + "_" + Math.random().toString(16).slice(2);
      const now = Date.now();
      const expiresAt = now + AUTO_DISMISS_MS;

      const toastType = normalizeType(type);
  
      const list = loadStoredToasts().filter(t => t.expiresAt > now);
      list.push({ id, message: String(message), type: toastType, expiresAt });
      saveStoredToasts(list);

      if (activeToasts.length >= MAX_TOASTS) {
          const oldest = activeToasts[0];
          dismissToast(oldest);
          activeToasts = activeToasts.slice(1);
      }

      const toast = document.createElement("div");
      toast.className = "warning-toast";
      toast.dataset.toastId = id;
  
      toast.innerHTML = `
          <div class="warning-toast__icon">i</div>
          <div class="warning-toast__text"></div>
      `;
  
      const textEl = toast.querySelector(".warning-toast__text");
      textEl.textContent = message;

      applyToastVisuals(toast, toastType);
  
      toast.addEventListener("click", () => {
          dismissToast(toast);
      });
  
      stack.appendChild(toast);
      activeToasts.push(toast);

      setTimeout(() => {
          dismissToast(toast);
      }, AUTO_DISMISS_MS);
  }    

  function translateMessage(message) {
    if (window.I18N && typeof I18N.translateLiteral === "function") {
      return I18N.translateLiteral(message);
    }
    return message;
  }

  function confirmModal(options = {}) {
    const defaultTitle = window.I18N ? I18N.t("common.confirm.title", "请确认") : "请确认";
    const defaultConfirmText = window.I18N ? I18N.t("common.actions.confirm", "确定") : "确定";
    const defaultCancelText = window.I18N ? I18N.t("common.actions.cancel", "取消") : "取消";
    const message = translateMessage(options.message || "确定要继续吗？");
    const type = normalizeType(options.type || "b");
    const confirmText = translateMessage(options.confirmText || defaultConfirmText);
    const cancelText = translateMessage(options.cancelText || defaultCancelText);

    return new Promise((resolve) => {
      const body = document.body || document.getElementsByTagName("body")[0];
      if (!body) {
        resolve(false);
        return;
      }

      const cfg = getToastVisualConfig(type);
      const overlay = document.createElement("div");
      overlay.className = "warning-confirm";
      overlay.setAttribute("role", "dialog");
      overlay.setAttribute("aria-modal", "true");

      overlay.innerHTML = `
        <div class="warning-confirm__box">
          <div class="warning-confirm__icon"></div>
          <div class="warning-confirm__content">
            <h2 class="warning-confirm__title"></h2>
            <p class="warning-confirm__message"></p>
            <div class="warning-confirm__actions">
              <button type="button" class="warning-confirm__button warning-confirm__button--cancel"></button>
              <button type="button" class="warning-confirm__button warning-confirm__button--confirm"></button>
            </div>
          </div>
        </div>
      `;

      const icon = overlay.querySelector(".warning-confirm__icon");
      const title = overlay.querySelector(".warning-confirm__title");
      const messageEl = overlay.querySelector(".warning-confirm__message");
      const cancelBtn = overlay.querySelector(".warning-confirm__button--cancel");
      const confirmBtn = overlay.querySelector(".warning-confirm__button--confirm");

      icon.textContent = cfg.icon;
      icon.style.color = cfg.iconColor;
      icon.style.borderColor = cfg.iconColor;
      title.textContent = options.title ? translateMessage(options.title) : defaultTitle;
      messageEl.textContent = message;
      cancelBtn.textContent = cancelText;
      confirmBtn.textContent = confirmText;
      confirmBtn.dataset.confirmType = cfg.type;

      let settled = false;
      function close(result) {
        if (settled) return;
        settled = true;
        overlay.classList.add("leaving");
        document.removeEventListener("keydown", onKeyDown);
        overlay.addEventListener("animationend", () => {
          overlay.remove();
          resolve(result);
        }, { once: true });
      }

      function onKeyDown(e) {
        if (e.key === "Escape") close(false);
        if (e.key === "Enter") close(true);
      }

      overlay.addEventListener("mousedown", (e) => {
        if (e.target === overlay) close(false);
      });
      cancelBtn.addEventListener("click", () => close(false));
      confirmBtn.addEventListener("click", () => close(true));
      document.addEventListener("keydown", onKeyDown);

      body.appendChild(overlay);
      requestAnimationFrame(() => overlay.classList.add("active"));
      confirmBtn.focus();
    });
  }

  function restoreToasts() {
      const now = Date.now();
      const list = loadStoredToasts().filter(t => t.expiresAt > now);
      saveStoredToasts(list);

      list.forEach(t => {
        const remaining = t.expiresAt - now;
        if (remaining <= 0) return;

        const stack = ensureStack();
        if (!stack) return;

        const toast = document.createElement("div");
        toast.className = "warning-toast";
        toast.dataset.toastId = t.id;

        toast.innerHTML = `
          <div class="warning-toast__icon">i</div>
          <div class="warning-toast__text"></div>
        `;

        toast.querySelector(".warning-toast__text").textContent = t.message;

        const toastType = normalizeType(t.type);
        applyToastVisuals(toast, toastType);

        toast.addEventListener("click", () => {
          dismissToast(toast);
        });

        stack.appendChild(toast);
        activeToasts.push(toast);

        setTimeout(() => {
          dismissToast(toast);
        }, remaining);
      });
  }

  window.pop_up = pop_up;
  window.Warning = { pop_up, confirm: confirmModal };

  function bootWarningToasts() {
    if (!document.body) {
      requestAnimationFrame(bootWarningToasts);
      return;
    }
    restoreToasts();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bootWarningToasts);
  } else {
    bootWarningToasts();
  }
})();
