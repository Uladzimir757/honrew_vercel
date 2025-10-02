// static/js/category-selector.js
document.addEventListener('DOMContentLoaded', () => {
    const categorySelect = document.getElementById('category');
    const subcategorySelect = document.getElementById('subcategory');
    const subcategoryContainer = document.getElementById('subcategory-container');
    const lang = document.documentElement.lang || 'en';

    // Функция для загрузки основных категорий
    async function loadCategories() {
        try {
            const response = await fetch(`/api/categories?lang=${lang}`);
            if (!response.ok) throw new Error('Network response was not ok');
            const categories = await response.json();

            categorySelect.innerHTML = `<option value="">${categorySelect.dataset.placeholder}</option>`; // Очищаем и добавляем плейсхолдер
            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.id;
                option.textContent = cat.name;
                categorySelect.appendChild(option);
            });
            
            // Если есть предвыбранная категория (например, при редактировании)
            const selectedCategoryId = categorySelect.dataset.selected;
            if (selectedCategoryId) {
                categorySelect.value = selectedCategoryId;
                // Запускаем событие, чтобы загрузить подкатегории
                categorySelect.dispatchEvent(new Event('change'));
            }

        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    }

    // Функция для загрузки подкатегорий
    async function loadSubcategories(categoryId) {
        if (!categoryId) {
            subcategoryContainer.classList.add('hidden');
            subcategorySelect.innerHTML = `<option value="">${subcategorySelect.dataset.placeholder}</option>`;
            return;
        }
        try {
            const response = await fetch(`/api/subcategories/${categoryId}?lang=${lang}`);
            if (!response.ok) throw new Error('Network response was not ok');
            const subcategories = await response.json();

            if (subcategories.length > 0) {
                subcategorySelect.innerHTML = `<option value="">${subcategorySelect.dataset.placeholder}</option>`;
                subcategories.forEach(sub => {
                    const option = document.createElement('option');
                    option.value = sub.id;
                    option.textContent = sub.name;
                    subcategorySelect.appendChild(option);
                });
                subcategoryContainer.classList.remove('hidden');

                // Если есть предвыбранная подкатегория
                const selectedSubcategoryId = subcategorySelect.dataset.selected;
                if(selectedSubcategoryId) {
                    subcategorySelect.value = selectedSubcategoryId;
                }

            } else {
                subcategoryContainer.classList.add('hidden');
            }
        } catch (error) {
            console.error('Failed to load subcategories:', error);
        }
    }

    // Слушатель событий для выбора категории
    if(categorySelect) {
        categorySelect.addEventListener('change', () => {
            const categoryId = categorySelect.value;
            loadSubcategories(categoryId);
        });

        // Запускаем загрузку категорий при старте
        loadCategories();
    }
});