/**
 * РАСКЛАДКА ПРОДУКТОВ - КЛИЕНТСКАЯ ЛОГИКА
 * ========================================
 */

(function() {
    'use strict';

    // ===========================
    // КОНФИГУРАЦИЯ И КОНСТАНТЫ
    // ===========================

    const CONFIG = {
        STORAGE_KEY_PREFIX: 'calc_params_',
        MESSAGE_TIMEOUT: {
            SUCCESS: 3000,
            ERROR: 5000
        },
        DEBOUNCE_DELAY: 300
    };

    // ===========================
    // СОСТОЯНИЕ ПРИЛОЖЕНИЯ
    // ===========================

    let currentPlanId = null;

    // ===========================
    // УТИЛИТАРНЫЕ ФУНКЦИИ
    // ===========================

    /**
     * Дебаунс функция для оптимизации частых вызовов
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Безопасный вызов fetch с обработкой ошибок
     */
    async function safeFetch(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Fetch error:', error);
            throw error;
        }
    }

    // ===========================
    // СИСТЕМА УВЕДОМЛЕНИЙ
    // ===========================

    const NotificationSystem = {
        container: null,

        init() {
            this.createContainer();
        },

        createContainer() {
            if (this.container) return;
            
            this.container = document.createElement('div');
            this.container.id = 'message-container';
            this.container.style.cssText = `
                position: fixed;
                top: 15px;
                right: 15px;
                z-index: 9999;
                pointer-events: none;
            `;
            document.body.appendChild(this.container);
        },

        show(message, type = 'success') {
            if (!this.container) this.createContainer();

            const messageDiv = this.createMessageElement(message, type);
            this.container.appendChild(messageDiv);
            
            // Автоматическое удаление
            const timeout = type === 'error' ? CONFIG.MESSAGE_TIMEOUT.ERROR : CONFIG.MESSAGE_TIMEOUT.SUCCESS;
            setTimeout(() => {
                if (messageDiv.parentNode) {
                    messageDiv.remove();
                }
            }, timeout);
        },

        createMessageElement(message, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = type === 'success' ? 'success-message' : 'error-message';
            messageDiv.style.pointerEvents = 'auto';

            const textSpan = document.createElement('span');
            textSpan.textContent = message;
            textSpan.style.flex = '1';

            const closeButton = document.createElement('button');
            closeButton.innerHTML = '&times;';
            closeButton.style.cssText = `
                background: none; border: none; color: white; font-size: 18px;
                font-weight: bold; cursor: pointer; padding: 0; margin-left: 12px;
                opacity: 0.8; transition: opacity 0.2s;
            `;
            
            closeButton.addEventListener('mouseover', () => closeButton.style.opacity = '1');
            closeButton.addEventListener('mouseout', () => closeButton.style.opacity = '0.8');
            closeButton.addEventListener('click', () => messageDiv.remove());

            messageDiv.style.cssText += 'display: flex; align-items: flex-start; justify-content: space-between;';
            messageDiv.appendChild(textSpan);
            messageDiv.appendChild(closeButton);

            return messageDiv;
        }
    };

    // ===========================
    // УПРАВЛЕНИЕ ВКЛАДКАМИ
    // ===========================

    const TabManager = {
        init() {
            this.bindEvents();
        },

        bindEvents() {
            const navTabs = document.querySelectorAll('.nav-tab');
            navTabs.forEach(tab => {
                tab.addEventListener('click', (e) => {
                    const tabName = e.currentTarget.dataset.tab;
                    this.switchTab(tabName);
                });
            });
        },

        switchTab(tabName) {
            // Скрываем все вкладки
            const tabPanes = document.querySelectorAll('.tab-pane');
            tabPanes.forEach(pane => pane.classList.remove('active'));

            // Убираем активный класс со всех кнопок
            const navTabs = document.querySelectorAll('.nav-tab');
            navTabs.forEach(tab => tab.classList.remove('active'));

            // Показываем нужную вкладку
            const targetPane = document.getElementById(tabName + '-tab');
            if (targetPane) {
                targetPane.classList.add('active');
            }

            // Активируем нужную кнопку
            const targetTab = document.querySelector(`[data-tab="${tabName}"]`);
            if (targetTab) {
                targetTab.classList.add('active');
            }
        }
    };

    // ===========================
    // УПРАВЛЕНИЕ ПЛАНАМИ
    // ===========================

    const PlanManager = {
        init() {
            this.bindEvents();
            currentPlanId = this.getCurrentPlanId();
        },

        getCurrentPlanId() {
            // Получаем ID плана из глобальной переменной или DOM
            const planIdMeta = document.querySelector('meta[name="current-plan-id"]');
            return planIdMeta ? planIdMeta.content : window.currentPlanId;
        },

        bindEvents() {
            // Создание нового плана
            const createBtn = document.querySelector('.create-plan-btn');
            if (createBtn) {
                createBtn.addEventListener('click', () => this.createPlan());
            }

            // Enter в поле создания плана
            const newPlanInput = document.getElementById('new-plan-name');
            if (newPlanInput) {
                newPlanInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.createPlan();
                    }
                });
            }

            // Редактирование названия плана
            const planTitle = document.querySelector('.plan-title');
            if (planTitle) {
                planTitle.addEventListener('click', () => this.startEditPlanName());
            }

            // Удаление плана
            const deleteBtn = document.querySelector('.delete-plan-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', (e) => {
                    const planId = this.getCurrentPlanId();
                    if (planId) {
                        this.deletePlan(planId);
                    }
                });
            }

            // Выбор планов
            const planItems = document.querySelectorAll('.plan-list li');
            planItems.forEach(item => {
                item.addEventListener('click', (e) => {
                    const planId = this.extractPlanId(e.currentTarget);
                    if (planId) {
                        this.selectPlan(planId);
                    }
                });
            });
        },

        extractPlanId(element) {
            // Извлекаем plan ID из onclick или data-атрибута
            const onclick = element.getAttribute('onclick');
            if (onclick) {
                const match = onclick.match(/selectPlan\((\d+)\)/);
                return match ? parseInt(match[1]) : null;
            }
            return null;
        },

        async createPlan() {
            const nameInput = document.getElementById('new-plan-name');
            const name = nameInput.value.trim();
            
            if (!name) {
                NotificationSystem.show('Введите название раскладки', 'error');
                return;
            }

            try {
                const data = await safeFetch('/', {
                    method: 'POST',
                    body: JSON.stringify({
                        action: 'create_plan',
                        name: name
                    })
                });

                if (data.status === 'success') {
                    NotificationSystem.show('Раскладка создана');
                    nameInput.value = '';
                    setTimeout(() => location.reload(), 1000);
                } else {
                    NotificationSystem.show(data.message || 'Не удалось создать раскладку', 'error');
                }
            } catch (error) {
                console.error('Ошибка при создании раскладки:', error);
                NotificationSystem.show('Произошла ошибка при создании раскладки', 'error');
            }
        },

        startEditPlanName() {
            const title = document.querySelector('.plan-title');
            const input = document.getElementById('plan-name-input');
            
            if (!title || !input) return;

            const originalName = title.dataset.originalName;
            
            title.style.display = 'none';
            input.style.display = 'inline-block';
            input.focus();
            input.select();

            const saveChanges = debounce(async () => {
                await this.savePlanName(input, title, originalName);
            }, CONFIG.DEBOUNCE_DELAY);

            // Удаляем старые обработчики
            input.removeEventListener('blur', saveChanges);
            input.removeEventListener('keypress', this.handleEnterKey);

            // Добавляем новые
            input.addEventListener('blur', saveChanges);
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    saveChanges();
                }
            });
        },

        async savePlanName(input, title, originalName) {
            const newName = input.value.trim();
            
            if (newName && newName !== originalName) {
                try {
                    const data = await safeFetch('/', {
                        method: 'POST',
                        body: JSON.stringify({
                            action: 'update_plan_name',
                            plan_id: currentPlanId,
                            new_name: newName
                        })
                    });

                    if (data.status === 'success') {
                        title.textContent = newName;
                        title.dataset.originalName = newName;
                        NotificationSystem.show('Название раскладки обновлено');
                    } else {
                        NotificationSystem.show(data.message || 'Не удалось обновить название раскладки', 'error');
                    }
                } catch (error) {
                    console.error('Ошибка при обновлении названия:', error);
                    NotificationSystem.show('Произошла ошибка при обновлении названия', 'error');
                }
            }

            title.style.display = 'inline';
            input.style.display = 'none';
        },

        async deletePlan(planId) {
            if (!confirm('Вы уверены, что хотите удалить раскладку?')) {
                return;
            }

            try {
                const data = await safeFetch('/', {
                    method: 'POST',
                    body: JSON.stringify({
                        action: 'delete_plan',
                        plan_id: planId
                    })
                });

                if (data.status === 'success') {
                    window.location.href = data.redirect;
                } else {
                    NotificationSystem.show(data.message || 'Не удалось удалить раскладку', 'error');
                }
            } catch (error) {
                console.error('Ошибка при удалении раскладки:', error);
                NotificationSystem.show('Произошла ошибка при удалении раскладки', 'error');
            }
        },

        selectPlan(planId) {
            // Сохраняем текущие параметры перед переключением
            CalculatorManager.saveParams();
            window.location.href = `/?plan_id=${planId}`;
        }
    };

    // ===========================
    // УПРАВЛЕНИЕ ДНЯМИ И ПРИЕМАМИ ПИЩИ
    // ===========================

    const MealManager = {
        init() {
            this.bindEvents();
        },

        bindEvents() {
            // Добавление дня
            const addDayBtn = document.querySelector('.add-day-btn');
            if (addDayBtn) {
                addDayBtn.addEventListener('click', () => this.addDay());
            }

            // Кнопки удаления приемов пищи
            document.addEventListener('click', (e) => {
                if (e.target.classList.contains('delete-meal-btn')) {
                    const mealId = this.getMealId(e.target);
                    if (mealId) {
                        this.deleteMeal(mealId);
                    }
                }
            });
        },

        getMealId(element) {
            const mealDiv = element.closest('[data-meal-id]');
            return mealDiv ? mealDiv.dataset.mealId : null;
        },

        async addDay() {
            const days = document.querySelectorAll('.day-container');
            const newDayNumber = days.length + 1;

            try {
                const data = await safeFetch('/', {
                    method: 'POST',
                    body: JSON.stringify({
                        action: 'add_day',
                        plan_id: currentPlanId,
                        day_number: newDayNumber
                    })
                });

                if (data.status === 'success') {
                    NotificationSystem.show('День добавлен');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    NotificationSystem.show(data.message || 'Не удалось добавить день', 'error');
                }
            } catch (error) {
                console.error('Ошибка при добавлении дня:', error);
                NotificationSystem.show('Произошла ошибка при добавлении дня', 'error');
            }
        },

        async addMeal(dayNumber) {
            const mealType = prompt('Введите тип приема пищи (например, Завтрак):');
            if (!mealType) return;

            try {
                const data = await safeFetch('/', {
                    method: 'POST',
                    body: JSON.stringify({
                        action: 'add_meal',
                        plan_id: currentPlanId,
                        day_number: dayNumber,
                        meal_type: mealType
                    })
                });

                if (data.status === 'success') {
                    NotificationSystem.show('Прием пищи добавлен');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    NotificationSystem.show(data.message || 'Не удалось добавить прием пищи', 'error');
                }
            } catch (error) {
                console.error('Ошибка при добавлении приема пищи:', error);
                NotificationSystem.show('Произошла ошибка при добавлении приема пищи', 'error');
            }
        },

        async deleteMeal(mealId) {
            if (!confirm('Удалить прием пищи?')) return;

            try {
                const data = await safeFetch('/', {
                    method: 'POST',
                    body: JSON.stringify({
                        action: 'remove_meal',
                        meal_id: mealId
                    })
                });

                if (data.status === 'success') {
                    NotificationSystem.show('Прием пищи удален');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    NotificationSystem.show(data.message || 'Не удалось удалить прием пищи', 'error');
                }
            } catch (error) {
                console.error('Ошибка при удалении приема пищи:', error);
                NotificationSystem.show('Произошла ошибка при удалении приема пищи', 'error');
            }
        }
    };

    // ===========================
    // УПРАВЛЕНИЕ ПРОДУКТАМИ
    // ===========================

    const ProductManager = {
        init() {
            this.bindEvents();
        },

        bindEvents() {
            // Обработка форм добавления продуктов
            document.addEventListener('keypress', (e) => {
                if (e.target.classList.contains('product-name') && e.key === 'Enter') {
                    const weightInput = e.target.closest('.meal').querySelector('.product-weight');
                    if (weightInput) weightInput.focus();
                }
                
                if (e.target.classList.contains('product-weight') && e.key === 'Enter') {
                    const addButton = e.target.closest('.meal').querySelector('.add-product-btn');
                    if (addButton) addButton.click();
                }
            });

            // Кнопки действий с продуктами
            document.addEventListener('click', (e) => {
                const target = e.target;
                
                if (target.classList.contains('edit-product-btn')) {
                    const productId = this.getProductId(target);
                    if (productId) this.startEditProduct(productId);
                }
                
                if (target.classList.contains('save-product-btn')) {
                    const productId = this.getProductId(target);
                    if (productId) this.saveProduct(productId);
                }
                
                if (target.classList.contains('cancel-edit-btn')) {
                    const productId = this.getProductId(target);
                    if (productId) this.cancelEdit(productId);
                }
                
                if (target.classList.contains('delete-product-btn')) {
                    const productId = this.getProductId(target);
                    if (productId) this.deleteProduct(productId);
                }
                
                if (target.classList.contains('add-product-btn')) {
                    const meal = target.closest('.meal');
                    const mealId = meal ? meal.dataset.mealId : null;
                    if (mealId) this.addProduct(mealId);
                }
            });
        },

        getProductId(element) {
            const productDiv = element.closest('[data-product-id]');
            return productDiv ? productDiv.dataset.productId : null;
        },

        startEditProduct(productId) {
            const productItem = document.querySelector(`[data-product-id="${productId}"]`);
            if (!productItem) return;

            const productDisplay = productItem.querySelector('.product-display');
            const productEditForm = productItem.querySelector('.product-edit-form');

            if (productDisplay && productEditForm) {
                productDisplay.style.display = 'none';
                productEditForm.style.display = 'flex';
                productItem.classList.add('editing');

                const nameInput = productEditForm.querySelector('input[data-type="name"]');
                if (nameInput) {
                    nameInput.focus();
                    nameInput.select();
                }
            }
        },

        async saveProduct(productId) {
            const productItem = document.querySelector(`[data-product-id="${productId}"]`);
            if (!productItem) return;

            const productDisplay = productItem.querySelector('.product-display');
            const productEditForm = productItem.querySelector('.product-edit-form');
            const nameInput = productEditForm.querySelector('input[data-type="name"]');
            const weightInput = productEditForm.querySelector('input[data-type="weight"]');

            const name = nameInput.value.trim();
            const weight = weightInput.value.trim();

            if (!name || !weight) {
                NotificationSystem.show('Пожалуйста, заполните все поля', 'error');
                return;
            }

            try {
                const data = await safeFetch('/', {
                    method: 'POST',
                    body: JSON.stringify({
                        action: 'update_product',
                        product_id: productId,
                        name: name,
                        weight: weight
                    })
                });

                if (data.status === 'success') {
                    productDisplay.textContent = `${name} - ${weight}г`;
                    productItem.dataset.productName = name;
                    productItem.dataset.productWeight = weight;

                    productDisplay.style.display = 'inline';
                    productEditForm.style.display = 'none';
                    productItem.classList.remove('editing');

                    NotificationSystem.show('Продукт обновлен');
                } else {
                    NotificationSystem.show(data.message || 'Не удалось обновить продукт', 'error');
                }
            } catch (error) {
                console.error('Ошибка при обновлении продукта:', error);
                NotificationSystem.show('Произошла ошибка при обновлении продукта', 'error');
            }
        },

        cancelEdit(productId) {
            const productItem = document.querySelector(`[data-product-id="${productId}"]`);
            if (!productItem) return;

            const productDisplay = productItem.querySelector('.product-display');
            const productEditForm = productItem.querySelector('.product-edit-form');
            const nameInput = productEditForm.querySelector('input[data-type="name"]');
            const weightInput = productEditForm.querySelector('input[data-type="weight"]');

            const originalName = productItem.dataset.productName;
            const originalWeight = productItem.dataset.productWeight;

            nameInput.value = originalName;
            weightInput.value = originalWeight;

            productDisplay.style.display = 'inline';
            productEditForm.style.display = 'none';
            productItem.classList.remove('editing');
        },

        async deleteProduct(productId) {
            if (!confirm('Удалить продукт?')) return;

            try {
                const data = await safeFetch('/', {
                    method: 'POST',
                    body: JSON.stringify({
                        action: 'delete_product',
                        product_id: productId
                    })
                });

                if (data.status === 'success') {
                    NotificationSystem.show('Продукт удален');
                    setTimeout(() => location.reload(), 1000);
                } else {
                    NotificationSystem.show(data.message || 'Не удалось удалить продукт', 'error');
                }
            } catch (error) {
                console.error('Ошибка при удалении продукта:', error);
                NotificationSystem.show('Произошла ошибка при удалении продукта', 'error');
            }
        },

        async addProduct(mealId) {
            const mealSection = document.querySelector(`[data-meal-id="${mealId}"]`);
            if (!mealSection) return;

            const productNameInput = mealSection.querySelector('.product-name');
            const productWeightInput = mealSection.querySelector('.product-weight');
            
            const name = productNameInput.value.trim();
            const weight = productWeightInput.value.trim();

            if (!name || !weight) {
                NotificationSystem.show('Пожалуйста, заполните все поля', 'error');
                return;
            }

            try {
                const data = await safeFetch('/', {
                    method: 'POST',
                    body: JSON.stringify({
                        action: 'add_product',
                        meal_id: mealId,
                        name: name,
                        weight: weight
                    })
                });

                if (data.status === 'success') {
                    NotificationSystem.show('Продукт добавлен');
                    productNameInput.value = '';
                    productWeightInput.value = '';
                    setTimeout(() => location.reload(), 1000);
                } else {
                    NotificationSystem.show(data.message || 'Не удалось добавить продукт', 'error');
                }
            } catch (error) {
                console.error('Ошибка при добавлении продукта:', error);
                NotificationSystem.show('Произошла ошибка при добавлении продукта', 'error');
            }
        }
    };

    // ===========================
    // КАЛЬКУЛЯТОР
    // ===========================

    const CalculatorManager = {
        init() {
            this.bindEvents();
            this.loadParams();
        },

        bindEvents() {
            const calculateBtn = document.querySelector('.calculate-btn');
            if (calculateBtn) {
                calculateBtn.addEventListener('click', () => this.calculate());
            }

            // Автосохранение параметров
            const tripDaysInput = document.getElementById('trip-days');
            const peopleCountInput = document.getElementById('people-count');

            if (tripDaysInput) {
                tripDaysInput.addEventListener('change', () => this.saveParams());
                tripDaysInput.addEventListener('input', debounce(() => this.saveParams(), CONFIG.DEBOUNCE_DELAY));
            }

            if (peopleCountInput) {
                peopleCountInput.addEventListener('change', () => this.saveParams());
                peopleCountInput.addEventListener('input', debounce(() => this.saveParams(), CONFIG.DEBOUNCE_DELAY));
            }
        },

        saveParams() {
            if (!currentPlanId) return;

            const tripDays = document.getElementById('trip-days')?.value;
            const peopleCount = document.getElementById('people-count')?.value;

            if (tripDays && peopleCount) {
                localStorage.setItem(`${CONFIG.STORAGE_KEY_PREFIX}${currentPlanId}`, JSON.stringify({
                    tripDays: tripDays,
                    peopleCount: peopleCount
                }));
            }
        },

        loadParams() {
            if (!currentPlanId) return;

            const savedParams = localStorage.getItem(`${CONFIG.STORAGE_KEY_PREFIX}${currentPlanId}`);
            
            if (savedParams) {
                try {
                    const params = JSON.parse(savedParams);
                    const tripDaysInput = document.getElementById('trip-days');
                    const peopleCountInput = document.getElementById('people-count');
                    
                    if (tripDaysInput) tripDaysInput.value = params.tripDays;
                    if (peopleCountInput) peopleCountInput.value = params.peopleCount;
                } catch (error) {
                    console.error('Ошибка при загрузке параметров:', error);
                }
            }
        },

        async calculate() {
            const tripDays = parseInt(document.getElementById('trip-days')?.value);
            const peopleCount = parseInt(document.getElementById('people-count')?.value);

            if (!tripDays || !peopleCount || !currentPlanId) {
                NotificationSystem.show('Пожалуйста, заполните все поля', 'error');
                return;
            }

            try {
                const data = await safeFetch('/calculate', {
                    method: 'POST',
                    body: JSON.stringify({
                        plan_id: currentPlanId,
                        trip_days: tripDays,
                        people_count: peopleCount
                    })
                });

                if (data.status === 'success') {
                    const result = data.data;
                    this.displayResults(
                        result.results,
                        result.summary.trip_days,
                        result.summary.people_count,
                        result.summary.layout_days_count,
                        result.summary.layout_repetitions,
                        result.summary.actual_days_used,
                        result.meal_types_by_day,
                        result.product_meal_usage
                    );
                    this.saveParams();
                } else {
                    NotificationSystem.show(data.message || 'Ошибка при расчете', 'error');
                }
            } catch (error) {
                console.error('Ошибка при запросе расчета:', error);
                NotificationSystem.show('Произошла ошибка при расчете', 'error');
            }
        },

        displayResults(results, tripDays, peopleCount, layoutDaysCount, layoutRepetitions, actualDaysUsed, mealTypesByDay, productMealUsage) {
            const mainResultsSection = document.getElementById('main-results-section');
            const mainResultsContent = document.getElementById('main-results-content');
            const resultsSection = document.getElementById('results-section');
            const resultsContent = document.getElementById('results-content');

            if (!mainResultsSection || !mainResultsContent || !resultsSection || !resultsContent) {
                return;
            }

            // Основная таблица результатов
            let mainHtml = this.generateMainTable(results, peopleCount, layoutDaysCount, tripDays, mealTypesByDay, productMealUsage);
            
            // Добавляем статистику
            mainHtml += this.generateStatistics(results, peopleCount, layoutDaysCount, tripDays, productMealUsage);

            // Детали расчета для боковой панели
            let detailsHtml = this.generateDetailsPanel(tripDays, peopleCount, layoutDaysCount, layoutRepetitions, actualDaysUsed);

            mainResultsContent.innerHTML = mainHtml;
            resultsContent.innerHTML = detailsHtml;

            mainResultsSection.style.display = 'block';
            resultsSection.style.display = 'block';

            // Плавная прокрутка к основной таблице
            mainResultsSection.scrollIntoView({ behavior: 'smooth' });
        },

        generateMainTable(results, peopleCount, layoutDaysCount, tripDays, mealTypesByDay, productMealUsage) {
            let html = `
                <div class="results-table-container">
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th>Продукт</th>
                                <th>1 прием пищи на ${peopleCount} чел.</th>
            `;

            // Добавляем заголовки для каждого рациона раскладки
            for (let i = 0; i < layoutDaysCount; i++) {
                const dayMealTypes = mealTypesByDay[i] || [];
                const mealType = dayMealTypes.length > 0 ? dayMealTypes.join(', ') : `Рацион ${i + 1}`;
                html += `<th>Рацион ${i + 1}<br><small>${mealType}</small></th>`;
            }

            html += `
                                <th>Количество повторений<br><small>за весь поход</small></th>
                                <th>Общий вес для покупки</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            results.forEach(result => {
                const weightPerMealForPeople = (result.weight_per_meal || 0) * peopleCount;
                const weightPerMealText = weightPerMealForPeople >= 1000 ?
                    `${(weightPerMealForPeople / 1000).toFixed(1)} кг` :
                    `${Math.round(weightPerMealForPeople)} г`;

                const mealUsage = productMealUsage[result.name] || {};

                html += `
                    <tr>
                        <td class="product-name-cell">${result.name}</td>
                        <td class="weight-per-person-cell">${weightPerMealText}</td>
                `;

                let totalOccurrences = 0;
                for (let i = 0; i < layoutDaysCount; i++) {
                    const usageCount = mealUsage[i] || 0;
                    const repetitionsForThisRation = Math.floor((tripDays - i - 1) / layoutDaysCount) + 1;
                    const totalUsageForThisRation = usageCount * repetitionsForThisRation;
                    totalOccurrences += totalUsageForThisRation;

                    const cellClass = totalUsageForThisRation > 0 ? 'meal-usage-cell' : 'meal-usage-empty-cell';
                    html += `<td class="${cellClass}">${totalUsageForThisRation > 0 ? totalUsageForThisRation : ''}</td>`;
                }

                const totalWeight = totalOccurrences * weightPerMealForPeople;
                const weightText = totalWeight >= 1000 ?
                    `${(totalWeight / 1000).toFixed(1)} кг` :
                    `${Math.round(totalWeight)} г`;

                html += `
                        <td class="occurrences-cell">${totalOccurrences}</td>
                        <td class="weight-cell">${weightText}</td>
                    </tr>
                `;
            });

            html += `
                        </tbody>
                    </table>
                </div>
            `;

            return html;
        },

        generateStatistics(results, peopleCount, layoutDaysCount, tripDays, productMealUsage) {
            // Пересчитываем общий вес
            let totalWeight = 0;
            results.forEach(result => {
                const weightPerMealForPeople = (result.weight_per_meal || 0) * peopleCount;
                const mealUsage = productMealUsage[result.name] || {};
                let totalOccurrences = 0;
                for (let i = 0; i < layoutDaysCount; i++) {
                    const usageCount = mealUsage[i] || 0;
                    const repetitionsForThisRation = Math.floor((tripDays - i - 1) / layoutDaysCount) + 1;
                    const totalUsageForThisRation = usageCount * repetitionsForThisRation;
                    totalOccurrences += totalUsageForThisRation;
                }
                totalWeight += totalOccurrences * weightPerMealForPeople;
            });

            const totalWeightText = totalWeight >= 1000 ?
                `${(totalWeight / 1000).toFixed(1)} кг` :
                `${Math.round(totalWeight)} г`;

            return `
                <div style="margin-top: 20px; padding: 15px; background: #e8f5e8; border-radius: 8px; border-left: 4px solid #28a745;">
                    <h5 style="margin: 0 0 10px 0; color: #1e7e34;">📊 Общая статистика</h5>
                    <p style="margin: 5px 0; color: #1e7e34;"><strong>Всего продуктов:</strong> ${results.length}</p>
                    <p style="margin: 5px 0; color: #1e7e34;"><strong>Общий вес для покупки:</strong> ${totalWeightText}</p>
                </div>
            `;
        },

        generateDetailsPanel(tripDays, peopleCount, layoutDaysCount, layoutRepetitions, actualDaysUsed) {
            return `
                <div style="margin-bottom: 20px; padding: 15px; background: #e3f2fd; border-radius: 8px; border-left: 4px solid #2196f3;">
                    <h5 style="margin: 0 0 10px 0; color: #1976d2;">📊 Информация о расчете</h5>
                    <p style="margin: 5px 0; color: #1976d2;"><strong>Длительность похода:</strong> ${tripDays} дней</p>
                    <p style="margin: 5px 0; color: #1976d2;"><strong>Количество человек:</strong> ${peopleCount}</p>
                    <p style="margin: 5px 0; color: #1976d2;"><strong>Рационов в раскладке:</strong> ${layoutDaysCount}</p>
                    <p style="margin: 5px 0; color: #1976d2;"><strong>Повторений раскладки:</strong> ${layoutRepetitions}</p>
                    <p style="margin: 5px 0; color: #1976d2;"><strong>Используется дней:</strong> ${actualDaysUsed}</p>
                </div>
            `;
        }
    };

    // ===========================
    // ГЛОБАЛЬНЫЕ ФУНКЦИИ ДЛЯ СОВМЕСТИМОСТИ
    // ===========================

    // Экспортируем функции в глобальную область видимости для совместимости с существующим HTML
    window.switchTab = (tabName) => TabManager.switchTab(tabName);
    window.selectPlan = (planId) => PlanManager.selectPlan(planId);
    window.createPlan = () => PlanManager.createPlan();
    window.deletePlan = (planId) => PlanManager.deletePlan(planId);
    window.editPlanName = () => PlanManager.startEditPlanName();
    window.addDay = () => MealManager.addDay();
    window.addMeal = (dayNumber) => MealManager.addMeal(dayNumber);
    window.deleteMeal = (mealId) => MealManager.deleteMeal(mealId);
    window.addProduct = (dayNumber, mealId) => ProductManager.addProduct(mealId);
    window.startEditProduct = (productId) => ProductManager.startEditProduct(productId);
    window.saveProductEdit = (productId) => ProductManager.saveProduct(productId);
    window.cancelProductEdit = (productId) => ProductManager.cancelEdit(productId);
    window.deleteProduct = (productId) => ProductManager.deleteProduct(productId);
    window.calculateFromLayout = () => CalculatorManager.calculate();
    window.showMessage = (message, type) => NotificationSystem.show(message, type);

    // ===========================
    // ИНИЦИАЛИЗАЦИЯ ПРИЛОЖЕНИЯ
    // ===========================

    document.addEventListener('DOMContentLoaded', function() {
        // Получаем ID текущего плана из шаблона
        currentPlanId = window.currentPlanId || null;
        
        // Инициализируем все модули
        NotificationSystem.init();
        TabManager.init();
        PlanManager.init();
        MealManager.init();
        ProductManager.init();
        CalculatorManager.init();

        console.log('✅ Приложение "Раскладка продуктов" инициализировано');
    });

})();