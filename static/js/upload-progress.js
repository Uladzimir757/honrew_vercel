document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('.upload-form'); // Работаем со всеми формами с этим классом
    const overlay = document.getElementById('upload-overlay');

    if (!forms.length || !overlay) {
        return;
    }

    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            // Простая проверка, что все required поля заполнены
            let isValid = true;
            form.querySelectorAll('[required]').forEach(input => {
                if (!input.value) {
                    isValid = false;
                }
            });

            if (isValid) {
                overlay.style.display = 'flex'; // Показываем экран загрузки
            }
        });
    });
});