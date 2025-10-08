document.addEventListener('DOMContentLoaded', function() {
    const likeForm = document.getElementById('like-form');
    if (!likeForm) return; // Если формы нет (пользователь не залогинен), ничего не делаем

    const likeButtonSvg = document.querySelector('#like-button svg');
    const likesCountSpan = document.getElementById('likes-count');
    
    // Получаем язык из data-атрибута, который мы добавим в HTML
    const currentLang = document.body.getAttribute('data-lang') || 'en';

    // Обработка лайков
    likeForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        fetch(likeForm.action, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    // Если ошибка (например, сессия истекла), перенаправляем на логин
                    window.location.href = `/login?lang=${currentLang}`;
                    return;
                }
                likesCountSpan.textContent = data.likes_count;
                if (data.user_has_liked) {
                    likeButtonSvg.classList.add('text-red-500');
                    likeButtonSvg.classList.remove('text-gray-400', 'hover:text-red-400');
                } else {
                    likeButtonSvg.classList.remove('text-red-500');
                    likeButtonSvg.classList.add('text-gray-400', 'hover:text-red-400');
                }
            })
            .catch(error => console.error('Error handling like:', error));
    });

    // =======================================================================
    // БЛОК ОБРАБОТКИ КОММЕНТАРИЕВ БЫЛ УДАЛЕН ИЗ ЭТОГО ФАЙЛА.
    // Эта логика теперь находится только в файле `static/js/comments.js`,
    // чтобы избежать дублирования запросов и сохранения комментариев.
    // =======================================================================
});