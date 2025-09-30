document.addEventListener('DOMContentLoaded', function() {
    const categorySelect = document.getElementById('category');
    const subcategorySelect = document.getElementById('subcategory');
    const subcategoryContainer = document.getElementById('subcategory-container');

    async function fetchCategories() {
        try {
            const response = await fetch('/api/categories');
            if (!response.ok) throw new Error('Failed to load categories');
            const categories = await response.json();
            
            // Запоминаем текущую выбранную категорию (если есть)
            const previouslySelected = categorySelect.dataset.selected;
            
            categorySelect.innerHTML = `<option value="">${categorySelect.dataset.placeholder}</option>`;
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                if (previouslySelected == category.id) {
                    option.selected = true;
                }
                categorySelect.appendChild(option);
            });
            
            // Если категория была выбрана, сразу загружаем подкатегории
            if (previouslySelected) {
                fetchSubcategories(previouslySelected);
            }

        } catch (error) {
            console.error(error);
        }
    }

    async function fetchSubcategories(categoryId) {
        if (!categoryId) {
            subcategoryContainer.classList.add('hidden');
            subcategorySelect.innerHTML = '';
            return;
        }
        try {
            const response = await fetch(`/api/subcategories/${categoryId}`);
            if (!response.ok) throw new Error('Failed to load subcategories');
            const subcategories = await response.json();

            subcategorySelect.innerHTML = `<option value="">${subcategorySelect.dataset.placeholder}</option>`;
            if (subcategories.length > 0) {
                subcategories.forEach(subcategory => {
                    const option = new Option(subcategory.name, subcategory.id);
                    subcategorySelect.appendChild(option);
                });
                subcategoryContainer.classList.remove('hidden');
            } else {
                subcategoryContainer.classList.add('hidden');
            }
        } catch (error) {
            console.error(error);
            subcategoryContainer.classList.add('hidden');
        }
    }

    categorySelect.addEventListener('change', () => {
        fetchSubcategories(categorySelect.value);
    });

    // Инициализация
    fetchCategories();
});