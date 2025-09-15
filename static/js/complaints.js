document.addEventListener('DOMContentLoaded', function() {
    // Загружаем переводы из специального тега script
    const translationsElement = document.getElementById('translations');
    const translations = JSON.parse(translationsElement.textContent);

    // Функция для обработки кликов вне меню жалоб, чтобы закрывать их
    document.body.addEventListener('click', function(event) {
        document.querySelectorAll('.complaint-reasons').forEach(function(menu) {
            if (!menu.previousElementSibling.contains(event.target)) {
                menu.classList.add('hidden');
            }
        });
    });

    document.querySelectorAll('.complaint-container').forEach(function(container) {
        const button = container.querySelector('.complaint-button');
        const reasonsMenu = container.querySelector('.complaint-reasons');
        const form = container.querySelector('.complaint-form');

        button.addEventListener('click', function(event) {
            event.stopPropagation();
            reasonsMenu.classList.toggle('hidden');
        });
        
        form.addEventListener('submit', function(event) {
            event.preventDefault();
            
            const reason = event.submitter.value;
            const contentId = form.dataset.contentId;
            const contentType = form.dataset.contentType;
            
            const formData = new FormData();
            formData.append('content_id', contentId);
            formData.append('content_type', contentType);
            formData.append('reason', reason);
            
            fetch('/api/complaints', {
                method: 'POST',
                body: formData,
                headers: {
                    // Добавляем заголовок, чтобы FastAPI знал, что это AJAX-запрос
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => response.json())
            .then(data => {
                // Используем переводы для сообщений
                if (data.status === 'success') {
                    reasonsMenu.classList.add('hidden');
                    button.classList.add('opacity-50', 'cursor-not-allowed');
                    button.disabled = true;
                    alert(translations.complaint_success);
                } else {
                    alert(translations.complaint_error_generic + ': ' + data.message);
                }
            })
            .catch(error => {
                console.error('Ошибка при отправке жалобы:', error);
                alert(translations.complaint_error_network);
            });
        });
    });
});