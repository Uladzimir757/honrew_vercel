document.addEventListener('DOMContentLoaded', function() {
    const likeForm = document.getElementById('like-form');
    if (!likeForm) return; // Если формы нет (пользователь не залогинен), ничего не делаем

    const likeButtonSvg = document.querySelector('#like-button svg');
    const likesCountSpan = document.getElementById('likes-count');
    const commentForm = document.getElementById('comment-form');
    const commentsList = document.getElementById('comments-list');
    const commentContent = document.getElementById('comment-content');
    const commentsCountSpan = document.getElementById('comments-count');
    const noCommentsMessage = document.getElementById('no-comments-message');
    
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

    // Обработка комментариев
    commentForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(commentForm);

        fetch(commentForm.action, { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }

            const newComment = document.createElement('div');
            newComment.classList.add('flex', 'items-start', 'space-x-4');
            
            // Защита от XSS (простое преобразование в текст)
            const safeContent = document.createTextNode(data.content).textContent;

            newComment.innerHTML = `
                <div class="flex-shrink-0">
                    <div class="h-10 w-10 rounded-full bg-slate-700 flex items-center justify-center font-bold text-white">
                        ${data.author_email[0].toUpperCase()}
                    </div>
                </div>
                <div class="flex-grow">
                    <div class="flex items-baseline space-x-3">
                        <a href="/user/${data.author_id}?lang=${currentLang}" class="font-semibold text-white hover:underline">${data.author_email}</a>
                        <p class="text-xs text-gray-500">${data.created_at}</p>
                    </div>
                    <p class="mt-1 text-gray-300 whitespace-pre-wrap">${safeContent}</p>
                </div>
            `;
            
            commentsList.prepend(newComment);
            
            if (noCommentsMessage) {
                noCommentsMessage.style.display = 'none';
            }

            commentsCountSpan.textContent = parseInt(commentsCountSpan.textContent) + 1;
            commentContent.value = '';
        })
        .catch(error => console.error('Error handling comment:', error));
    });
});