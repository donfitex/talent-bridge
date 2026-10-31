/**
 * TalentBridge Front-End Interactions
 */
document.addEventListener('DOMContentLoaded', () => {
    const themeButton = document.getElementById('theme-toggle');
    const themeMedia = window.matchMedia('(prefers-color-scheme: dark)');
    const applyTheme = theme => {
        document.documentElement.dataset.bsTheme = theme;
        if (themeButton) {
            themeButton.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
            themeButton.setAttribute('aria-pressed', String(theme === 'dark'));
            themeButton.setAttribute('aria-label', `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`);
        }
    };
    applyTheme(document.documentElement.dataset.bsTheme || 'light');
    themeButton?.addEventListener('click', () => {
        const theme = document.documentElement.dataset.bsTheme === 'dark' ? 'light' : 'dark';
        applyTheme(theme);
        try { localStorage.setItem('talentbridge-theme', theme); } catch {}
    });
    themeMedia.addEventListener('change', event => {
        let saved; try { saved = localStorage.getItem('talentbridge-theme'); } catch {}
        if (!saved) applyTheme(event.matches ? 'dark' : 'light');
    });
    window.addEventListener('storage', event => {
        if (event.key === 'talentbridge-theme') applyTheme(event.newValue || (themeMedia.matches ? 'dark' : 'light'));
    });
    // Configure HTMX with CSRF token from document cookies or headers
    document.body.addEventListener('htmx:configRequest', (event) => {
        const getCookie = (name) => {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        };

        const csrfToken = getCookie('csrftoken');
        if (csrfToken) {
            event.detail.headers['X-CSRFToken'] = csrfToken;
        }
    });

    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl));
});
