// static/js/comments.js
document.addEventListener('DOMContentLoaded', () => {
    const commentForm = document.getElementById('comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', function(event) {
            event.preventDefault();
            event.stopPropagation(); // Добавлено, чтобы остановить дальнейшее всплытие события

            const contentTextarea = document.getElementById('comment-content');
            const content = contentTextarea.value.trim();
            if (!content) return;

            const formData = new FormData(this);
            const actionUrl = this.action;
            const submitButton = this.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.innerHTML;

            submitButton.disabled = true;
            submitButton.innerHTML = '...';

            fetch(actionUrl, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const newComment = createCommentElement(data.comment);
                    const commentsContainer = document.getElementById('comments-container');
                    commentsContainer.prepend(newComment);
                    
                    const noCommentsMessage = document.getElementById('no-comments-message');
                    if (noCommentsMessage) {
                        noCommentsMessage.remove();
                    }
                    contentTextarea.value = '';
                } else {
                    alert(data.message);
                    contentTextarea.value = '';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('A network error occurred. Please try again.');
            })
            .finally(() => {
                submitButton.disabled = false;
                submitButton.innerHTML = originalButtonText;
            });
        });
    }
});

function createCommentElement(comment) {
    const lang = new URLSearchParams(window.location.search).get('lang') || 'en';
    const tr = JSON.parse(document.getElementById('translations').textContent);

    const commentWrapper = document.createElement('div');
    commentWrapper.className = 'flex items-start space-x-4';
    commentWrapper.id = `comment-${comment.id}`;

    commentWrapper.innerHTML = `
        <div class="flex-1 bg-slate-800/70 p-4 rounded-lg">
            <div class="flex justify-between items-start">
                <p class="font-semibold text-blue-300">
                    <a href="/user/${comment.author_id}?lang=${lang}">${comment.author_email}</a>
                </p>
                <button class="report-button text-gray-500 hover:text-red-400 transition" 
                        data-content-id="${comment.id}" 
                        data-content-type="comment" 
                        title="${tr.complaint_report_comment || 'Report comment'}">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6H5a2 2 0 00-2 2zm0 0h7.5M12 13H9"/>
                    </svg>
                </button>
            </div>
            <p class="text-gray-300 mt-1">${escapeHTML(comment.content)}</p>
        </div>
    `;
    return commentWrapper;
}

function escapeHTML(str) {
    const p = document.createElement('p');
    p.appendChild(document.createTextNode(str));
    return p.innerHTML;
}