document.addEventListener('DOMContentLoaded', function () {
  const darkModeToggle = document.getElementById('darkModeToggle');
  const systemPref = window.matchMedia('(prefers-color-scheme: dark)');
  const saved = localStorage.getItem('darkMode');

  function applyDarkMode(enabled) {
    document.documentElement.classList.toggle('dark', enabled);
    const icon = darkModeToggle?.querySelector('i');
    if (icon) icon.className = enabled ? 'fas fa-sun' : 'fas fa-moon';
  }

  if (saved) {
    applyDarkMode(saved === 'enabled');
  } else if (systemPref.matches) {
    applyDarkMode(true);
  }

  darkModeToggle?.addEventListener('click', () => {
    const isDark = document.documentElement.classList.contains('dark');
    applyDarkMode(!isDark);
    localStorage.setItem('darkMode', !isDark ? 'enabled' : 'disabled');
  });

  systemPref.addEventListener('change', (e) => {
    if (!localStorage.getItem('darkMode')) {
      applyDarkMode(e.matches);
    }
  });

  // Dropdown toggles
  document.getElementById('notificationBtn')?.addEventListener('click', () => {
    document.getElementById('notificationDropdown')?.classList.toggle('hidden');
  });

  document.getElementById('userMenuBtn')?.addEventListener('click', () => {
    document.getElementById('userMenu')?.classList.toggle('hidden');
  });

  // Click outside to close
  document.addEventListener('click', (e) => {
    if (!e.target.closest('#notificationBtn') && !e.target.closest('#notificationDropdown')) {
      document.getElementById('notificationDropdown')?.classList.add('hidden');
    }
    if (!e.target.closest('#userMenuBtn') && !e.target.closest('#userMenu')) {
      document.getElementById('userMenu')?.classList.add('hidden');
    }
  });
});
