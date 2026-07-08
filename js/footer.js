(function () {
  function isAdmin() {
    return !!(window.Auth && Auth.isAdmin && Auth.isAdmin());
  }

  function renderFooter() {
    if (document.getElementById("siteFooter")) return;

    const footer = document.createElement("footer");
    footer.id = "siteFooter";
    footer.className = "site-footer";
    footer.innerHTML = `
      <div class="site-footer__inner">
        <div class="site-footer__group">
          <span data-i18n="footer.contact">Contact</span>
          <a href="mailto:hongdiding@gmail.com">hongdiding@gmail.com</a>
        </div>
        <div class="site-footer__group">
          <span data-i18n="footer.links">Links</span>
          <a href="https://www.culiutech.com/" target="_blank" rel="noopener">CULIU</a>
          <a href="https://www.eduhk.hk/" target="_blank" rel="noopener">EdUHK</a>
        </div>
        <div class="site-footer__group">
          <label for="siteLocaleSelect" data-i18n="footer.language">Language</label>
          <select id="siteLocaleSelect" class="site-footer__select">
            <option value="zh-cn">简体中文</option>
            <option value="en-us">English</option>
          </select>
        </div>
        <div class="site-footer__group site-footer__admin" style="display:none;">
          <a href="translation_editor.html" data-i18n="footer.translationEditor">Translation editor</a>
        </div>
        <div class="site-footer__copyright" data-i18n="footer.copyright">Copyright © EdUHK. All rights reserved.</div>
      </div>
    `;

    document.body.appendChild(footer);

    const select = footer.querySelector("#siteLocaleSelect");
    select.value = window.I18N?.locale || localStorage.getItem("site_locale") || "zh-cn";
    select.addEventListener("change", async () => {
      if (window.I18N) {
        await I18N.loadLocale(select.value);
      } else {
        localStorage.setItem("site_locale", select.value);
      }
      window.location.reload();
    });

    updateAdminLink();
    if (window.I18N) I18N.applyTranslations(footer);
  }

  function updateAdminLink() {
    const adminEl = document.querySelector(".site-footer__admin");
    if (adminEl) adminEl.style.display = isAdmin() ? "flex" : "none";
  }

  window.SiteFooter = { render: renderFooter, updateAdminLink };

  document.addEventListener("DOMContentLoaded", renderFooter);
  document.addEventListener("auth:changed", updateAdminLink);
})();
