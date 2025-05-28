document.addEventListener('DOMContentLoaded', function () {
  console.log('darkmode.js loaded');

  // Dark Mode
  const darkModeToggle = document.getElementById('darkModeToggle');
  const systemPref = window.matchMedia('(prefers-color-scheme: dark)');
  const saved = localStorage.getItem('darkMode');

  function applyDarkMode(enabled) {
    document.documentElement.classList.toggle('dark', enabled);
    const icon = darkModeToggle?.querySelector('i');
    if (icon) icon.className = enabled ? 'fas fa-sun' : 'fas fa-moon';
  }

  // Initialize theme
  if (saved) {
    console.log('Applying saved dark mode:', saved);
    applyDarkMode(saved === 'enabled');
  } else if (systemPref.matches) {
    console.log('Applying system dark mode preference');
    applyDarkMode(true);
  }

  darkModeToggle?.addEventListener('click', () => {
    console.log('Dark mode toggle clicked');
    const isDark = !document.documentElement.classList.contains('dark');
    applyDarkMode(isDark);
    localStorage.setItem('darkMode', isDark ? 'enabled' : 'disabled');
  });

  systemPref.addEventListener('change', (e) => {
    if (!localStorage.getItem('darkMode')) {
      console.log('System preference changed:', e.matches);
      applyDarkMode(e.matches);
    }
  });

  // Notification Dropdown
  const notificationBtn = document.getElementById('notificationBtn');
  const notificationDropdown = document.getElementById('notificationDropdown');
  notificationBtn?.addEventListener('click', (e) => {
    console.log('Notification button clicked');
    e.stopPropagation();
    notificationDropdown?.classList.toggle('hidden');
  });

  // User Menu Dropdown
  const userMenuBtn = document.getElementById('userMenuBtn');
  const userMenu = document.getElementById('userMenu');
  if (userMenuBtn && userMenu) {
    console.log('User menu button and dropdown found');
    userMenuBtn.addEventListener('click', (e) => {
      console.log('User menu button clicked');
      e.stopPropagation();
      userMenu.classList.toggle('hidden');
      console.log('User menu hidden:', userMenu.classList.contains('hidden'));
    });
  } else {
    console.error('User menu elements not found:', { userMenuBtn, userMenu });
  }

  // Close dropdowns on outside click
  document.addEventListener('click', (e) => {
    if (!e.target.closest('#notificationBtn') && !e.target.closest('#notificationDropdown')) {
      notificationDropdown?.classList.add('hidden');
    }
    if (!e.target.closest('#userMenuBtn') && !e.target.closest('#userMenu')) {
      userMenu?.classList.add('hidden');
    }
  });
});