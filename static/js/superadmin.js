document.addEventListener('DOMContentLoaded', () => {
    // Helper function to close all dropdowns
    const closeAllDropdowns = () => {
        document.querySelectorAll('.dropdown-menu, #notificationDropdown, #userMenu').forEach(menu => {
            menu.classList.add('hidden');
        });
    };

    // Sidebar Dropdowns
    document.querySelectorAll('.dropdown-toggle').forEach(button => {
        button.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent closing immediately
            const menu = button.nextElementSibling;
            const isOpen = !menu.classList.contains('hidden');

            // Close all dropdowns
            closeAllDropdowns();

            // Toggle the clicked dropdown
            if (!isOpen) {
                menu.classList.remove('hidden');
            }
        });
    });

    // Notification Dropdown
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationDropdown = document.getElementById('notificationDropdown');
    if (notificationBtn && notificationDropdown) {
        notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = !notificationDropdown.classList.contains('hidden');
            closeAllDropdowns();
            if (!isOpen) {
                notificationDropdown.classList.remove('hidden');
                // Fetch notifications via AJAX if needed
            }
        });
    }

    // User Menu Dropdown
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userMenu = document.getElementById('userMenu');
    if (userMenuBtn && userMenu) {
        userMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = !userMenu.classList.contains('hidden');
            closeAllDropdowns();
            if (!isOpen) {
                userMenu.classList.remove('hidden');
            }
        });
    }

    // Close all dropdowns on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.dropdown-toggle, #notificationBtn, #userMenuBtn, .dropdown-menu, #notificationDropdown, #userMenu')) {
            closeAllDropdowns();
        }
    });

    // Current Time
    const currentTime = document.getElementById('currentTime');
    if (currentTime) {
        setInterval(() => {
            const now = new Date();
            currentTime.textContent = now.toLocaleTimeString();
        }, 1000);
    }
});