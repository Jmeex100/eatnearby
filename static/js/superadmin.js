document.addEventListener('DOMContentLoaded', () => {
// /home/surecode/Documents/Django/GitHub/eatnearby/static/js/superadmin.js

  // Current Time
  const currentTime = document.getElementById('currentTime');
  if (currentTime) {
    setInterval(() => {
      const now = new Date();
      currentTime.textContent = now.toLocaleTimeString('en-US', { hour12: false });
    }, 1000);
    const now = new Date();
    currentTime.textContent = now.toLocaleTimeString('en-US', { hour12: false });
  }
});