// raskladka/static/js/login.js
(function() {
    const input = document.getElementById('password');
    const btn = document.querySelector('.toggle-visibility');
    if (!input || !btn) return;

    function setVisible(visible) {
        input.type = visible ? 'text' : 'password';
        btn.setAttribute('aria-pressed', String(visible));
        btn.setAttribute('aria-label', visible ? 'Скрыть пароль' : 'Показать пароль');
        btn.title = visible ? 'Скрыть пароль' : 'Показать пароль';
        // toggle icon center dot by switching to filled/outlined styles
        const svg = btn.querySelector('svg');
        if (!svg) return;
        const existing = svg.querySelector('circle[data-dot]');
        if (existing) existing.remove();
        if (visible) {
            const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            dot.setAttribute('data-dot', '1');
            dot.setAttribute('cx', '12');
            dot.setAttribute('cy', '12');
            dot.setAttribute('r', '1.5');
            dot.setAttribute('fill', 'currentColor');
            svg.appendChild(dot);
        }
    }

    let visible = false;
    btn.addEventListener('click', function() {
        visible = !visible;
        setVisible(visible);
    });

    // Trim username input on submit to avoid accidental spaces
    const form = document.querySelector('form');
    const usernameInput = document.querySelector('input[name="username"]');
    if (form && usernameInput) {
        form.addEventListener('submit', function() {
            usernameInput.value = usernameInput.value.trim();
        });
    }
})();


