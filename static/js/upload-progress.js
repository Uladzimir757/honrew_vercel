// Файл: static/js/upload-progress.js

document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const fileListContainer = document.getElementById('file-list');
    const submitButton = document.getElementById('submit-button');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const errorMessageDiv = document.getElementById('error-message');

    let uploadedFiles = [];

    fileInput.addEventListener('change', () => {
        fileListContainer.innerHTML = '';
        uploadedFiles = [];
        for (const file of fileInput.files) {
            const fileItem = document.createElement('div');
            fileItem.textContent = file.name;
            fileItem.className = 'text-sm text-gray-400';
            fileListContainer.appendChild(fileItem);
        }
    });

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        submitButton.disabled = true;
        errorMessageDiv.classList.add('hidden');
        progressContainer.classList.remove('hidden');

        const files = Array.from(fileInput.files);
        let totalSize = files.reduce((acc, file) => acc + file.size, 0);
        let uploadedSize = 0;

        try {
            const presignedUrlResponses = await Promise.all(
                files.map(file =>
                    fetch('/api/generate-upload-url', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ filename: file.name, contentType: file.type || 'application/octet-stream' }),
                    }).then(res => res.json())
                )
            );

            const uploadPromises = files.map((file, index) => {
                const response = presignedUrlResponses[index];
                if (!response.url) {
                    throw new Error('Failed to get presigned URL for ' + file.name);
                }
                
                // Определяем mediaType на основе Content-Type
                const mediaType = file.type.startsWith('image/') ? 'image' : 'video';
                
                uploadedFiles.push({ objectName: response.objectName, mediaType: mediaType });

                return new Promise((resolve, reject) => {
                    const xhr = new XMLHttpRequest();
                    xhr.open('PUT', response.url, true);
                    xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');

                    xhr.upload.onprogress = (event) => {
                        if (event.lengthComputable) {
                            // Эта часть не будет работать для общего прогресса,
                            // так как XHR не поддерживает отслеживание прогресса для нескольких файлов одновременно.
                            // Мы будем обновлять прогресс после каждого успешного файла.
                        }
                    };
                    
                    xhr.onload = () => {
                        if (xhr.status >= 200 && xhr.status < 300) {
                            uploadedSize += file.size;
                            const percentComplete = totalSize > 0 ? (uploadedSize / totalSize) * 100 : 0;
                            progressBar.style.width = percentComplete + '%';
                            progressText.textContent = `Uploaded ${index + 1} of ${files.length} files...`;
                            resolve(xhr.response);
                        } else {
                            reject(new Error(`Upload failed for ${file.name}: ${xhr.statusText}`));
                        }
                    };

                    xhr.onerror = () => reject(new Error(`Network error during upload for ${file.name}`));
                    xhr.send(file);
                });
            });

            await Promise.all(uploadPromises);
            progressText.textContent = "Finalizing review...";

            // ИСПРАВЛЕНО: Правильно собираем данные из формы
            const formData = new FormData(uploadForm);
            const reviewData = {
                what: formData.get('what'),
                where: formData.get('where'),
                title: formData.get('title'),
                description: formData.get('description'),
                // Важное изменение: берем ID подкатегории
                subcategory_id: formData.get('subcategory_id'), 
                rating: formData.get('rating'),
                objectNames: uploadedFiles
            };

            const finalResponse = await fetch('/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(reviewData)
            });

            const result = await finalResponse.json();

            if (result.status === 'success') {
                window.location.href = result.redirectUrl;
            } else {
                throw new Error(result.message || 'Failed to finalize review.');
            }

        } catch (error) {
            errorMessageDiv.textContent = error.message;
            errorMessageDiv.classList.remove('hidden');
            submitButton.disabled = false;
            progressContainer.classList.add('hidden');
            progressBar.style.width = '0%';
            progressText.textContent = '';
            uploadedFiles = []; // Сбрасываем, если была ошибка
        }
    });
});