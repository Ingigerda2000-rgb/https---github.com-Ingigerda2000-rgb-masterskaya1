// Функция для обновления счетчика корзины и содержимого всплывающего окна
function updateCartCount() {
    fetch('/cart/summary/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log("Данные корзины:", data);
            
            // Обновляем счетчик корзины
            const cartCount = document.getElementById('cart-count');
            if (cartCount) {
                cartCount.textContent = data.item_count;
                // Скрываем бейдж если корзина пуста
                cartCount.style.display = data.item_count > 0 ? 'inline-block' : 'none';
            }
            
            // Обновляем всплывающее окно корзины
            updateCartPreview(data);
            
            // Обновляем иконки изделий в каталоге
            updateCartIcons(data.items);
        })
        .catch(error => {
            console.error('Ошибка при обновлении корзины:', error);
        });
}

// Функция для обновления содержимого всплывающего окна корзины
function updateCartPreview(data) {
    const cartPreviewItems = document.getElementById('cart-preview-items');
    const emptyCartMessage = document.getElementById('empty-cart-message');
    const cartTotal = document.getElementById('cart-total');
    const cartTotalBadge = document.getElementById('cart-total-badge');
    
    if (!cartPreviewItems || !emptyCartMessage || !cartTotal || !cartTotalBadge) {
        console.error('Не найдены элементы корзины');
        return;
    }
    
    // Обновляем общую сумму
    cartTotal.textContent = `${data.total} ₽`;
    cartTotalBadge.textContent = `${data.total} ₽`;
    
    // Если корзина пуста, показываем сообщение
    if (data.item_count === 0 || !data.items || data.items.length === 0) {
        emptyCartMessage.style.display = 'block';
        // Очищаем содержимое, кроме сообщения о пустой корзине
        const items = cartPreviewItems.querySelectorAll('.cart-preview-item');
        items.forEach(item => item.remove());
        return;
    }
    
    // Скрываем сообщение о пустой корзине
    emptyCartMessage.style.display = 'none';
    
    // Очищаем текущее содержимое
    const existingItems = cartPreviewItems.querySelectorAll('.cart-preview-item');
    existingItems.forEach(item => item.remove());
    
    // Добавляем элементы корзины
    data.items.forEach(item => {
        const itemElement = document.createElement('div');
        itemElement.className = 'cart-preview-item border-bottom p-2';
        itemElement.dataset.itemId = item.product_id || item.id;
        
        itemElement.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="flex-shrink-0" style="width: 50px; height: 50px;">
                    ${item.image ? `<img src="${item.image}" alt="${item.name}" class="img-fluid rounded" style="width: 100%; height: 100%; object-fit: cover;">` : 
                    `<div class="bg-light rounded d-flex align-items-center justify-content-center" style="width: 100%; height: 100%;">
                        <i class="bi bi-image text-muted"></i>
                    </div>`}
                </div>
                <div class="flex-grow-1 ms-3">
                    <h6 class="mb-0 small" style="overflow-wrap: break-word; word-break: break-word;">${item.name}</h6>
                    <div class="d-flex justify-content-between align-items-center mt-1">
                        <div class="input-group input-group-sm" style="width: 100px;">
                            <button class="btn btn-decrease-quantity" type="button" data-item-id="${item.id}" style="border: 1px solid #8a2be2; color: #8a2be2;">-</button>
                            <input type="text" class="form-control text-center item-quantity" value="${item.quantity}" readonly style="border: 1px solid #8a2be2;">
                            <button class="btn btn-increase-quantity" type="button" data-item-id="${item.id}" style="border: 1px solid #8a2be2; color: #8a2be2;">+</button>
                        </div>
                        <div class="ms-2">
                            <span class="fw-bold" style="color: #8a2be2;">${item.subtotal} ₽</span>
                        </div>
                    </div>
                </div>
                <div class="ms-2">
                    <button class="btn btn-sm btn-remove-item" data-item-id="${item.id}" style="border: 1px solid #8a2be2; color: #8a2be2;">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            </div>
        `;
        
        cartPreviewItems.appendChild(itemElement);
    });
    
    // Добавляем обработчики событий для кнопок
    addCartItemEventListeners();
}

// Функция для добавления обработчиков событий кнопкам в корзине
function addCartItemEventListeners() {
    // Кнопки увеличения количества
    document.querySelectorAll('.btn-increase-quantity').forEach(button => {
        button.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            updateCartItemQuantity(itemId, 1);
        });
    });
    
    // Кнопки уменьшения количества
    document.querySelectorAll('.btn-decrease-quantity').forEach(button => {
        button.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            updateCartItemQuantity(itemId, -1);
        });
    });
    
    // Кнопки удаления
    document.querySelectorAll('.btn-remove-item').forEach(button => {
        button.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            removeCartItem(itemId);
        });
    });
}

// Функция для обновления количества изделий в корзине
function updateCartItemQuantity(itemId, change) {
    // Находим текущее количество
    const itemElement = document.querySelector(`.cart-preview-item[data-item-id="${itemId}"]`);
    const quantityInput = itemElement.querySelector('.item-quantity');
    let currentQuantity = parseInt(quantityInput.value);
    let newQuantity = currentQuantity + change;
    
    // Если новое количество меньше или равно 0, удаляем изделие
    if (newQuantity <= 0) {
        removeCartItem(itemId);
        return;
    }
    
    // Получаем CSRF токен
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                      document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    
    // Отправляем запрос на обновление количества
    const formData = new FormData();
    formData.append('quantity', newQuantity);
    
    fetch(`/cart/update/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Обновляем корзину
            updateCartCount();
        } else {
            alert(data.message || 'Произошла ошибка при обновлении корзины');
        }
    })
    .catch(error => {
        console.error('Ошибка при обновлении количества изделий:', error);
    });
}

// Функция для удаления изделия из корзины
function removeCartItem(itemId) {
    // Получаем CSRF токен
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                      document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    
    fetch(`/cart/remove/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Обновляем корзину
            updateCartCount();
        } else {
            alert(data.message || 'Произошла ошибка при удалении изделия из корзины');
        }
    })
    .catch(error => {
        console.error('Ошибка при удалении изделия из корзины:', error);
    });
}

// Функция для обновления иконок изделий в каталоге
function updateCartIcons(items) {
    if (!items || !Array.isArray(items)) return;
    
    // Сначала сбрасываем все иконки
    document.querySelectorAll('[id^="cart-icon-"]').forEach(icon => {
        icon.classList.remove('bi-cart-check-fill');
        icon.classList.add('bi-cart-plus');
    });
    
    document.querySelectorAll('[id^="cart-qty-"]').forEach(qty => {
        qty.style.display = 'none';
        qty.textContent = '0';
    });
    
    // Затем обновляем иконки для изделий в корзине
    items.forEach(item => {
        const productId = item.product_id;
        const iconElement = document.getElementById(`cart-icon-${productId}`);
        const qtyElement = document.getElementById(`cart-qty-${productId}`);
        
        if (iconElement) {
            iconElement.classList.remove('bi-cart-plus');
            iconElement.classList.add('bi-cart-check-fill');
        }
        
        if (qtyElement) {
            qtyElement.textContent = item.quantity;
            qtyElement.style.display = 'inline-block';
        }
    });
}

// Функция для добавления изделия в корзину
function addToCart(productId, quantity = 1) {
    // Получаем CSRF токен
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                      document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    
    if (!csrfToken) {
        console.error('CSRF токен не найден');
        return;
    }
    
    // Создаем FormData для отправки данных
    const formData = new FormData();
    formData.append('quantity', quantity);
    
    // Отправляем AJAX запрос
    fetch(`/cart/add/${productId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Обновляем информацию о корзине
            updateCartCount();
            
            // Показываем уведомление об успешном добавлении
            showToast('Товар добавлен в корзину', 'success');
        } else {
            // Показываем сообщение об ошибке
            showToast(data.message || 'Произошла ошибка при добавлении изделия в корзину', 'danger');
        }
    })
    .catch(error => {
        console.error('Ошибка при добавлении изделия в корзину:', error);
        showToast('Произошла ошибка при добавлении изделия в корзину', 'danger');
    });
}

// Функция для отображения уведомления
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? '#8a2be2' : '#dc3545';
    
    toast.className = 'toast align-items-center text-white border-0 position-fixed bottom-0 end-0 m-3';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    toast.style.backgroundColor = bgColor;
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    document.body.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    
    // Удаляем уведомление после скрытия
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем CSRF токен в мета-тег, если его нет
    if (!document.querySelector('meta[name="csrf-token"]')) {
        const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
        if (csrfToken) {
            const meta = document.createElement('meta');
            meta.name = 'csrf-token';
            meta.content = csrfToken;
            document.head.appendChild(meta);
        }
    }
    
    // Обновляем корзину при загрузке
    updateCartCount();
    
    // Обновляем каждые 30 секунд
    setInterval(updateCartCount, 30000);
});
