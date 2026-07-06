(function () {
  const SUPPORTED_LOCALES = ["zh-cn", "en-us"];
  const STORAGE_KEY = "site_locale";
  let currentLocale = localStorage.getItem(STORAGE_KEY) || "zh-cn";
  let dictionary = {};

  function getByPath(obj, path) {
    return String(path || "")
      .split(".")
      .reduce((acc, key) => (acc && Object.prototype.hasOwnProperty.call(acc, key) ? acc[key] : undefined), obj);
  }

  function format(value, vars = {}) {
    if (typeof value !== "string") return value;
    return value.replace(/\{(\w+)\}/g, (_, key) => (vars[key] == null ? `{${key}}` : String(vars[key])));
  }

  async function loadLocale(locale = currentLocale) {
    const normalized = SUPPORTED_LOCALES.includes(locale) ? locale : "zh-cn";
    const resp = await fetch(`locales/${normalized}.json`, { cache: "no-store" });
    if (!resp.ok) throw new Error(`Failed to load locale ${normalized}`);
    dictionary = await resp.json();
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

  function applyTranslations(root = document) {
    root.querySelectorAll("[data-i18n]").forEach((el) => {
      const fallback = el.dataset.i18nFallback ?? el.textContent;
      el.textContent = t(el.dataset.i18n, fallback);
    });
    root.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const fallback = el.getAttribute("placeholder") || "";
      el.setAttribute("placeholder", t(el.dataset.i18nPlaceholder, fallback));
    });
    root.querySelectorAll("[data-i18n-title]").forEach((el) => {
      const fallback = el.getAttribute("title") || "";
      el.setAttribute("title", t(el.dataset.i18nTitle, fallback));
    });
    root.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
      const fallback = el.getAttribute("aria-label") || "";
      el.setAttribute("aria-label", t(el.dataset.i18nAriaLabel, fallback));
    });
    applyCommonChrome(root);
  }

  function setText(el, key, fallback) {
    if (el) el.textContent = t(key, fallback);
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
    get locale() {
      return currentLocale;
    },
    get dictionary() {
      return dictionary;
    },
    supportedLocales: SUPPORTED_LOCALES,
  };

  document.addEventListener("DOMContentLoaded", () => {
    loadLocale(currentLocale).catch((err) => console.warn("i18n load failed:", err));
  });
})();
