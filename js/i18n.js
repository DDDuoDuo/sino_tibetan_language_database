(function () {
  const SUPPORTED_LOCALES = ["zh-cn", "en-us"];
  const STORAGE_KEY = "site_locale";
  let currentLocale = localStorage.getItem(STORAGE_KEY) || "zh-cn";
  let dictionary = {};
  let sourceDictionary = null;
  let sourceIndex = new Map();
  let isApplying = false;
  let observer = null;
  const textNodeKeys = new WeakMap();

  if (currentLocale !== "zh-cn") {
    document.documentElement.classList.add("i18n-pending");
    const style = document.createElement("style");
    style.textContent = `
      html.i18n-pending body { opacity: 0; }
      body { transition: opacity 140ms ease; }
    `;
    document.head.appendChild(style);
  }

  function getByPath(obj, path) {
    return String(path || "")
      .split(".")
      .reduce((acc, key) => (acc && Object.prototype.hasOwnProperty.call(acc, key) ? acc[key] : undefined), obj);
  }

  function format(value, vars = {}) {
    if (typeof value !== "string") return value;
    return value.replace(/\{(\w+)\}/g, (_, key) => (vars[key] == null ? `{${key}}` : String(vars[key])));
  }

  function normalizeLiteral(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
  }

  function flattenStrings(obj, path = []) {
    if (typeof obj === "string") {
      const normalized = normalizeLiteral(obj);
      if (normalized && !sourceIndex.has(normalized)) {
        sourceIndex.set(normalized, path.join("."));
      }
      return;
    }
    if (Array.isArray(obj)) {
      obj.forEach((item, index) => flattenStrings(item, path.concat(String(index))));
      return;
    }
    if (obj && typeof obj === "object") {
      Object.keys(obj).forEach((key) => flattenStrings(obj[key], path.concat(key)));
    }
  }

  async function loadSourceDictionary() {
    if (sourceDictionary) return sourceDictionary;
    const resp = await fetch("locales/zh-cn.json", { cache: "no-store" });
    if (!resp.ok) throw new Error("Failed to load source locale zh-cn");
    sourceDictionary = await resp.json();
    sourceIndex = new Map();
    flattenStrings(sourceDictionary);
    return sourceDictionary;
  }

  async function loadLocale(locale = currentLocale) {
    const normalized = SUPPORTED_LOCALES.includes(locale) ? locale : "zh-cn";
    const source = await loadSourceDictionary();
    if (normalized === "zh-cn") {
      dictionary = source;
    } else {
      const resp = await fetch(`locales/${normalized}.json`, { cache: "no-store" });
      if (!resp.ok) throw new Error(`Failed to load locale ${normalized}`);
      dictionary = await resp.json();
    }
    currentLocale = normalized;
    localStorage.setItem(STORAGE_KEY, normalized);
    document.documentElement.lang = normalized === "zh-cn" ? "zh-CN" : "en-US";
    applyTranslations();
    document.dispatchEvent(new CustomEvent("i18n:changed", { detail: { locale: normalized } }));
    return dictionary;
  }

  function t(key, fallback = "", vars = {}) {
    const value = getByPath(dictionary, key);
    if (value === undefined || value === null || value === "") return format(fallback, vars);
    return format(value, vars);
  }

  function parseVars(value) {
    if (!value) return {};
    try {
      const parsed = JSON.parse(value);
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch (err) {
      return {};
    }
  }

  function stringifyVars(vars = {}) {
    try {
      return JSON.stringify(vars || {});
    } catch (err) {
      return "{}";
    }
  }

  function translateKey(key, fallback = "") {
    return t(key, fallback);
  }

  function splitOuterWhitespace(value) {
    const text = String(value);
    return {
      prefix: text.match(/^\s*/)?.[0] || "",
      suffix: text.match(/\s*$/)?.[0] || "",
    };
  }

  function translateLiteral(value) {
    const normalized = normalizeLiteral(value);
    if (!normalized) return value;
    const key = sourceIndex.get(normalized);
    if (!key) return value;
    const translated = translateKey(key, value);
    if (!translated || translated === value) return value;
    const { prefix, suffix } = splitOuterWhitespace(value);
    return `${prefix}${translated}${suffix}`;
  }

  function translateTextNode(node) {
    const text = node.nodeValue;
    if (!text || !normalizeLiteral(text)) return;

    let meta = textNodeKeys.get(node);
    if (!meta) {
      const key = sourceIndex.get(normalizeLiteral(text));
      if (!key) return;
      meta = { key, ...splitOuterWhitespace(text) };
      textNodeKeys.set(node, meta);
    }

    const translated = translateKey(meta.key, text);
    if (translated && node.nodeValue !== `${meta.prefix}${translated}${meta.suffix}`) {
      node.nodeValue = `${meta.prefix}${translated}${meta.suffix}`;
    }
  }

  function shouldSkipTextNode(node) {
    const parent = node.parentElement;
    if (!parent) return true;
    return ["SCRIPT", "STYLE", "TEXTAREA"].includes(parent.tagName);
  }

  function applyAutoText(root = document) {
    const start = root.nodeType === Node.TEXT_NODE ? root : root;
    if (start.nodeType === Node.TEXT_NODE) {
      if (!shouldSkipTextNode(start)) translateTextNode(start);
      return;
    }

    const walker = document.createTreeWalker(start, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        return shouldSkipTextNode(node) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      },
    });

    let node;
    while ((node = walker.nextNode())) {
      translateTextNode(node);
    }
  }

  function translateAttribute(el, attr, dataKey) {
    if (!el.hasAttribute(attr)) return;
    let key = el.dataset[dataKey];
    const current = el.getAttribute(attr);
    if (!key) {
      key = sourceIndex.get(normalizeLiteral(current));
      if (!key) return;
      el.dataset[dataKey] = key;
    }
    const translated = translateKey(key, current);
    if (translated && translated !== current) el.setAttribute(attr, translated);
  }

  function applyAutoAttributes(root = document) {
    const elements = root.nodeType === Node.ELEMENT_NODE ? [root, ...root.querySelectorAll("*")] : [...root.querySelectorAll("*")];
    elements.forEach((el) => {
      translateAttribute(el, "placeholder", "i18nAutoPlaceholderKey");
      translateAttribute(el, "title", "i18nAutoTitleKey");
      translateAttribute(el, "aria-label", "i18nAutoAriaLabelKey");
      translateAttribute(el, "alt", "i18nAutoAltKey");
      if (el.tagName === "INPUT" && ["button", "submit", "reset"].includes((el.getAttribute("type") || "").toLowerCase())) {
        translateAttribute(el, "value", "i18nAutoValueKey");
      }
    });
  }

  function selectElements(root, selector) {
    if (root.nodeType === Node.ELEMENT_NODE) {
      const matches = root.matches(selector) ? [root] : [];
      return matches.concat([...root.querySelectorAll(selector)]);
    }
    return [...root.querySelectorAll(selector)];
  }

  function applyTranslations(root = document) {
    if (isApplying || !sourceDictionary) return;
    if (root.nodeType === Node.TEXT_NODE) {
      isApplying = true;
      try {
        applyAutoText(root);
      } finally {
        isApplying = false;
      }
      return;
    }
    isApplying = true;
    try {
      selectElements(root, "[data-i18n]").forEach((el) => {
        const fallback = el.dataset.i18nFallback ?? el.textContent;
        el.textContent = t(el.dataset.i18n, fallback, parseVars(el.dataset.i18nVars));
      });
      selectElements(root, "[data-i18n-placeholder]").forEach((el) => {
        const fallback = el.getAttribute("placeholder") || "";
        el.setAttribute("placeholder", t(el.dataset.i18nPlaceholder, fallback));
      });
      selectElements(root, "[data-i18n-title]").forEach((el) => {
        const fallback = el.getAttribute("title") || "";
        el.setAttribute("title", t(el.dataset.i18nTitle, fallback));
      });
      selectElements(root, "[data-i18n-aria-label]").forEach((el) => {
        const fallback = el.getAttribute("aria-label") || "";
        el.setAttribute("aria-label", t(el.dataset.i18nAriaLabel, fallback));
      });
      applyCommonChrome(root);
      applyAutoAttributes(root);
      applyAutoText(root);
    } finally {
      isApplying = false;
    }
  }

  function setText(el, key, fallback) {
    if (el) el.textContent = t(key, fallback);
  }

  function setDynamicText(el, key, fallback = "", vars = {}) {
    if (!el) return;
    el.dataset.i18n = key;
    el.dataset.i18nFallback = fallback;
    el.dataset.i18nVars = stringifyVars(vars);
    el.textContent = t(key, fallback, vars);
  }

  function applyCommonChrome(root = document) {
    root.querySelectorAll('a[href="index.html"]').forEach((el) => setText(el, "common.nav.home", el.textContent));
    root.querySelectorAll('a[href="language_map.html"]').forEach((el) => setText(el, "common.nav.research", el.textContent));
    root.querySelectorAll('a[href="contribute.html"]').forEach((el) => setText(el, "common.nav.contributors", el.textContent));
    root.querySelectorAll('a[href="account.html"]').forEach((el) => setText(el, "common.nav.account", el.textContent));
    root.querySelectorAll('a[href="projects.html"]').forEach((el) => setText(el, "common.nav.projects", el.textContent));
    root.querySelectorAll("#logoutBtn").forEach((el) => setText(el, "common.nav.logout", el.textContent));
    root.querySelectorAll("#themeToggle").forEach((el) => {
      el.setAttribute("title", t("common.theme.toggle", el.getAttribute("title") || "切换主题"));
    });

    if (window.Auth && !Auth.isLoggedIn()) {
      root.querySelectorAll("#userStatus").forEach((el) => setText(el, "common.actions.login", el.textContent || "登录"));
    }
  }

  window.I18N = {
    loadLocale,
    applyTranslations,
    t,
    setText: setDynamicText,
    translateLiteral,
    get locale() {
      return currentLocale;
    },
    get dictionary() {
      return dictionary;
    },
    supportedLocales: SUPPORTED_LOCALES,
  };

  function startObserver() {
    if (observer) return;
    observer = new MutationObserver((mutations) => {
      if (isApplying || !sourceDictionary) return;
      mutations.forEach((mutation) => {
        if (mutation.type === "childList") {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE || node.nodeType === Node.TEXT_NODE) {
              applyTranslations(node);
            }
          });
        } else if (mutation.type === "characterData") {
          applyTranslations(mutation.target);
        }
      });
    });
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      characterData: true,
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    loadLocale(currentLocale)
      .then(() => {
        startObserver();
        document.documentElement.classList.remove("i18n-pending");
        document.documentElement.classList.add("i18n-ready");
      })
      .catch((err) => {
        console.warn("i18n load failed:", err);
        document.documentElement.classList.remove("i18n-pending");
      });
  });
})();
