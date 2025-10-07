// static/js/complaints.js
document.addEventListener('DOMContentLoaded', function() {
    const translations = JSON.parse(document.getElementById('translations').textContent);

    // Функция для создания модального окна жалобы
    function createComplaintModal(contentId, contentType) {
        // Удаляем старое модальное окно, если оно есть
        const oldModal = document.getElementById('complaint-modal');
        if (oldModal) {
            oldModal.remove();
        }

        const modal = document.createElement('div');
        modal.id = 'complaint-modal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-70 z-50 flex items-center justify-center';
        modal.innerHTML = `
            <div class="bg-slate-800 rounded-lg shadow-xl p-6 w-full max-w-md">
                <h3 class="text-xl font-bold text-white mb-4">${translations.complaint_report || 'Report'}</h3>
                <div class="space-y-2">
                    <button data-reason="spam" class="complaint-reason-btn w-full text-left p-2 rounded hover:bg-slate-700">${translations.complaint_reason_spam || 'Spam'}</button>
                    <button data-reason="insult" class="complaint-reason-btn w-full text-left p-2 rounded hover:bg-slate-700">${translations.complaint_reason_insult || 'Insult'}</button>
                    <button data-reason="fraud" class="complaint-reason-btn w-full text-left p-2 rounded hover:bg-slate-700">${translations.complaint_reason_fraud || 'Slander / Deception'}</button>
                </div>
                <div class="text-right mt-4">
                    <button id="complaint-cancel-btn" class="text-gray-400 hover:text-white">Cancel</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Закрытие модального окна
        modal.addEventListener('click', (e) => {
            if (e.target.id === 'complaint-modal' || e.target.id === 'complaint-cancel-btn') {
                modal.remove();
            }
        });

        // Обработка выбора причины
        modal.querySelectorAll('.complaint-reason-btn').forEach(button => {
            button.addEventListener('click', () => {
                sendComplaint(contentId, contentType, button.dataset.reason, button);
                modal.remove();
            });
        });
    }

    // Функция отправки жалобы на сервер
    function sendComplaint(contentId, contentType, reason, buttonElement) {
        const formData = new FormData();
        formData.append('content_id', contentId);
        formData.append('content_type', contentType);
        formData.append('reason', reason);

        fetch('/api/complaints', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert(translations.complaint_success);
                // Делаем кнопку неактивной, чтобы нельзя было пожаловаться дважды
                const originalButton = document.querySelector(`[data-content-id='${contentId}'][data-content-type='${contentType}']`);
                if (originalButton) {
                    originalButton.disabled = true;
                    originalButton.classList.add('opacity-50', 'cursor-not-allowed');
                }
            } else {
                alert(translations.complaint_error_generic + ': ' + (data.message || ''));
            }
        })
        .catch(error => {
            console.error('Complaint submission error:', error);
            alert(translations.complaint_error_network);
        });
    }

    // Навешиваем обработчик на все кнопки "Пожаловаться"
    document.body.addEventListener('click', function(event) {
        const reportButton = event.target.closest('.report-button');
        if (reportButton) {
            const { contentId, contentType } = reportButton.dataset;
            createComplaintModal(contentId, contentType);
        }
    });
});