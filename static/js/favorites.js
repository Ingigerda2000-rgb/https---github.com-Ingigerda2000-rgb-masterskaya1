// Функции для работы с избранными товарами

// Функция для добавления/удаления товара из избранного
function toggleFavorite(productId) {
    // Получаем CSRF токен
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || 
                      document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
    
    if (!csrfToken) {
        console.error('CSRF токен не найден');
        return;
    }
    
    // Отправляем AJAX запрос
    fetch(`/products/favorite/toggle/${productId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Обновляем иконку избранного
            updateFavoriteIcon(productId, data.is_favorite);
            
            // Показываем уведомление
            showToast(data.message, 'success');
        } else if (data.redirect) {
            // Если нужна авторизация, перенаправляем на страницу входа
            window.location.href = data.redirect;
        } else {
            // Показываем сообщение об ошибке
            showToast(data.message || 'Произошла ошибка', 'danger');
        }
    })
    .catch(error => {
        console.error('Ошибка при обновлении избранного:', error);
        showToast('Произошла ошибка при обновлении избранного', 'danger');
    });
}

// Функция для обновления иконки избранного
function updateFavoriteIcon(productId, isFavorite) {
    const favoriteIcon = document.getElementById(`favorite-icon-${productId}`);
    if (favoriteIcon) {
        if (isFavorite) {
            favoriteIcon.classList.remove('bi-heart');
            favoriteIcon.classList.add('bi-heart-fill');
            favoriteIcon.style.color = '#ff0000'; // Красный цвет для избранного
        } else {
            favoriteIcon.classList.remove('bi-heart-fill');
            favoriteIcon.classList.add('bi-heart');
            favoriteIcon.style.color = ''; // Сбрасываем цвет
        }
    }
}

// Функция для проверки статуса избранного при загрузке страницы
function checkFavoriteStatus(productId) {
    fetch(`/products/favorite/check/${productId}/`)
        .then(response => response.json())
        .then(data => {
            updateFavoriteIcon(productId, data.is_favorite);
        })
        .catch(error => {
            console.error('Ошибка при проверке статуса избранного:', error);
        });
}

// Функция для отображения уведомления (используем ту же функцию, что и в cart.js)
function showFavoriteToast(message, type = 'success') {
    // Проверяем, существует ли функция showToast из cart.js
    if (typeof showToast === 'function') {
        showToast(message, type);
        return;
    }
    
    // Если функция не существует, создаем свою
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
    
    // Находим все иконки избранного на странице и проверяем их статус
    document.querySelectorAll('[id^="favorite-icon-"]').forEach(icon => {
        const productId = icon.id.replace('favorite-icon-', '');
        checkFavoriteStatus(productId);
        
        // Добавляем обработчик клика
        icon.addEventListener('click', function(e) {
            e.preventDefault();
            toggleFavorite(productId);
        });
    });
});
