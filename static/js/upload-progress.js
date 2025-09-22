// File: static/js/upload-progress.js

document.addEventListener('DOMContentLoaded', () => {
    // Находим все формы с классом 'upload-form' на странице
    const uploadForms = document.querySelectorAll('.upload-form');
    const uploadOverlay = document.getElementById('upload-overlay');

    uploadForms.forEach(form => {
        form.addEventListener('submit', async (event) => {
            // 1. Предотвращаем стандартную отправку формы
            event.preventDefault();
            
            if (uploadOverlay) {
                uploadOverlay.style.display = 'flex';
            }

            // 2. Получаем файл из инпута или записанное видео
            // Этот код будет работать и для <input type="file"> и для записанного видео,
            // если в recorder.js вы создаете File объект.
            const mediaFileInput = form.querySelector('input[type="file"][name="media_file"]');
            let file;

            if (mediaFileInput && mediaFileInput.files.length > 0) {
                file = mediaFileInput.files[0];
            } else {
                // Если это форма после записи видео, файл может быть прикреплен динамически
                // Убедитесь, что в recorder.js вы добавляете файл в dataTransfer
                const dataTransfer = new DataTransfer();
                if (window.recordedBlob) {
                    const recordedFile = new File([window.recordedBlob], "recorded_video.webm", { type: window.recordedBlob.type });
                    dataTransfer.items.add(recordedFile);
                    file = dataTransfer.files[0];
                }
            }

            if (!file) {
                alert('No file selected or recorded.');
                if (uploadOverlay) uploadOverlay.style.display = 'none';
                return;
            }

            // 3. Запрашиваем у нашего бэкенда подписанную ссылку (presigned URL)
            let presignedData;
            try {
                const response = await fetch('/api/generate-upload-url', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        filename: file.name,
                        contentType: file.type,
                    }),
                });

                if (!response.ok) {
                    throw new Error('Failed to get presigned URL from server.');
                }
                presignedData = await response.json();

            } catch (error) {
                console.error('Error getting presigned URL:', error);
                alert('Error preparing upload. Please try again.');
                if (uploadOverlay) uploadOverlay.style.display = 'none';
                return;
            }

            // 4. Загружаем файл НАПРЯМУЮ в R2 по полученной ссылке
            try {
                const uploadResponse = await fetch(presignedData.url, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': file.type,
                    },
                    body: file,
                });

                if (!uploadResponse.ok) {
                    throw new Error('Direct upload to R2 failed.');
                }

            } catch (error) {
                console.error('Error uploading file to R2:', error);
                alert('Error uploading file. Please try again.');
                if (uploadOverlay) uploadOverlay.style.display = 'none';
                return;
            }

            // 5. Собираем остальные данные из формы
            const formData = new FormData(form);
            const metadata = {
                what: formData.get('what'),
                where: formData.get('where'),
                title: formData.get('title'),
                description: formData.get('description'),
                category: formData.get('category'),
                rating: formData.get('rating'),
                objectName: presignedData.objectName, // <-- Имя файла из ответа сервера
                mediaType: file.type.startsWith('image/') ? 'image' : 'video'
            };

            // 6. Отправляем метаданные на наш основной эндпоинт /upload
            try {
                const finalResponse = await fetch(form.action, { // form.action это /upload?lang=...
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(metadata),
                });
                
                if (!finalResponse.ok) {
                     throw new Error('Server failed to process metadata.');
                }

                const result = await finalResponse.json();

                // 7. Перенаправляем пользователя на главную страницу в случае успеха
                if (result.status === 'success' && result.redirectUrl) {
                    window.location.href = result.redirectUrl;
                } else {
                    throw new Error(result.message || 'Unknown error after submitting metadata.');
                }

            } catch (error) {
                 console.error('Error submitting metadata:', error);
                 alert('Failed to save review details. Please try again.');
                 if (uploadOverlay) uploadOverlay.style.display = 'none';
            }
        });
    });
});