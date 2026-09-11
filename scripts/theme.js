var THEME_KEY = 'rhs-theme';
var savedTheme = localStorage.getItem(THEME_KEY) || 'current';

if (savedTheme !== 'current') {
  document.documentElement.setAttribute('data-theme', savedTheme);
}

document.addEventListener('DOMContentLoaded', function () {
  var select = document.getElementById('theme-select');
  if (!select) return;

  select.value = savedTheme;

  select.addEventListener('change', function () {
    var theme = select.value;
    localStorage.setItem(THEME_KEY, theme);
    if (theme === 'current') {
      document.documentElement.removeAttribute('data-theme');
    } else {
      document.documentElement.setAttribute('data-theme', theme);
    }
  });
});
