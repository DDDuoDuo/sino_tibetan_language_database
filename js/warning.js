(function () {
    const MAX_TOASTS = 3;
    const AUTO_DISMISS_MS = 4000;
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
      if (stackEl && document.body.contains(stackEl)) return stackEl;
      stackEl = document.createElement("div");
      stackEl.className = "warning-stack";
      document.body.appendChild(stackEl);
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
    
        const stack = ensureStack();
    
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
  
    function restoreToasts() {
        const now = Date.now();
        const list = loadStoredToasts().filter(t => t.expiresAt > now);
        saveStoredToasts(list);

        list.forEach(t => {
          const remaining = t.expiresAt - now;
          if (remaining <= 0) return;

          const stack = ensureStack();

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
    window.Warning = { pop_up };

    restoreToasts();
})();
