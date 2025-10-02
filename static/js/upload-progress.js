// static/js/upload-progress.js
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    if (!form) return;

    const fileInput = document.getElementById('file-input');
    const submitButton = document.getElementById('submit-button');
    const requiredInputs = form.querySelectorAll('input[required], textarea[required], select[required]');
    
    // Функция для проверки, заполнены ли все обязательные поля
    function checkFormValidity() {
        let allValid = true;
        requiredInputs.forEach(input => {
            // Пропускаем проверку для скрытого select'а подкатегорий
            if (input.id === 'subcategory' && input.closest('#subcategory-container').classList.contains('hidden')) {
                return;
            }
            if (!input.value.trim()) {
                allValid = false;
            }
        });
        if (fileInput.files.length === 0) {
            allValid = false;
        }
        submitButton.disabled = !allValid;
    }

    // Проверяем форму при любом изменении
    form.addEventListener('input', checkFormValidity);
    fileInput.addEventListener('change', checkFormValidity);

    // Изначально кнопка неактивна
    checkFormValidity(); 

    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        submitButton.disabled = true;

        const files = fileInput.files;
        const objectNames = [];
        const totalFiles = files.length;

        try {
            // Шаг 1: Загрузка файлов по одному
            for (let i = 0; i < totalFiles; i++) {
                const file = files[i];
                
                // Обновляем текст и фон кнопки
                const progress = Math.round((i / totalFiles) * 100);
                submitButton.textContent = `Uploading ${i + 1}/${totalFiles}...`;
                submitButton.style.background = `linear-gradient(to right, #4f46e5 ${progress}%, #312e81 ${progress}%)`;

                const presignedUrlResponse = await fetch('/api/generate-upload-url', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ filename: file.name, contentType: file.type })
                });
                if (!presignedUrlResponse.ok) throw new Error('Failed to get presigned URL');
                
                const { url, objectName } = await presignedUrlResponse.json();

                await fetch(url, { method: 'PUT', body: file });
                
                objectNames.push({
                    objectName: objectName,
                    mediaType: file.type.startsWith('image') ? 'image' : 'video'
                });
            }

            // Финальное обновление кнопки перед отправкой данных
            submitButton.textContent = 'Saving review...';
            submitButton.style.background = `#4f46e5`; // Полностью закрашиваем

            // Шаг 2: Отправка данных формы
            const formData = new FormData(form);
            const jsonData = Object.fromEntries(formData.entries());
            jsonData.objectNames = objectNames;
            
            const finalResponse = await fetch('/upload', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(jsonData)
            });

            if (!finalResponse.ok) throw new Error('Failed to submit review data');
            const result = await finalResponse.json();

            if (result.status === 'success' && result.redirectUrl) {
                window.location.href = result.redirectUrl;
            } else {
                throw new Error(result.message || 'Unknown error');
            }

        } catch (error) {
            console.error('Upload failed:', error);
            alert('Upload failed: ' + error.message);
            // Возвращаем кнопку в исходное состояние в случае ошибки
            submitButton.textContent = document.getElementById('submit-button').textContent; // Исходный текст
            submitButton.style.background = '';
            checkFormValidity(); // Перепроверяем, должна ли кнопка быть активной
        }
    });
});