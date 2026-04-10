/**
 * Shared theme toggle logic.
 * Expects the page to have elements: #themeToggle, #logo
 * Optional: #moonIcon, #sunIcon
 */
(function () {
  const themeToggleBtn = document.getElementById('themeToggle');
  const moonIcon = document.getElementById('moonIcon');
  const sunIcon = document.getElementById('sunIcon');
  const logo = document.getElementById('logo');
  const htmlEl = document.documentElement;

  const savedTheme = localStorage.getItem('theme');
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  if (savedTheme === 'dark' || (!savedTheme && systemDark)) {
    setDarkTheme();
  } else {
    setLightTheme();
  }

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      if (htmlEl.getAttribute('data-theme') === 'dark') {
        setLightTheme();
        localStorage.setItem('theme', 'light');
      } else {
        setDarkTheme();
        localStorage.setItem('theme', 'dark');
      }
    });
  }

  function setDarkTheme() {
    htmlEl.setAttribute('data-theme', 'dark');
    if (moonIcon) moonIcon.style.display = 'none';
    if (sunIcon) sunIcon.style.display = 'block';
    if (logo) logo.src = "img/EdUHK_logo_dark.png";
  }

  function setLightTheme() {
    htmlEl.removeAttribute('data-theme');
    if (moonIcon) moonIcon.style.display = 'block';
    if (sunIcon) sunIcon.style.display = 'none';
    if (logo) logo.src = "img/EdUHK_logo.png";
  }
})();
