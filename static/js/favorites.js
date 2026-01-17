// favorites.js - Функциональность для работы с избранными товарами

$(document).ready(function() {
    // Обработка клика по кнопке избранного
    $('.favorite-btn').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        const $btn = $(this);
        const productId = $btn.data('product-id');
        const $icon = $btn.find('i');

        // Отправляем AJAX запрос
        $.ajax({
            url: `/products/favorite/toggle/${productId}/`,
            type: 'POST',
            data: {
                'csrfmiddlewaretoken': $('input[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.success) {
                    if (response.is_favorite) {
                        $icon.removeClass('bi-heart').addClass('bi-heart-fill text-danger');
                        showToast('Товар добавлен в избранное', 'success');
                    } else {
                        $icon.removeClass('bi-heart-fill text-danger').addClass('bi-heart');
                        showToast('Товар удален из избранного', 'info');
                    }
                } else {
                    if (response.redirect) {
                        window.location.href = response.redirect;
                    } else {
                        showToast(response.message || 'Произошла ошибка', 'error');
                    }
                }
            },
            error: function(xhr) {
                if (xhr.status === 403) {
                    // Пользователь не авторизован
                    window.location.href = '/accounts/login/';
                } else {
                    showToast('Произошла ошибка при обработке запроса', 'error');
                }
            }
        });
    });

    // Функция для отображения уведомлений
    function showToast(message, type) {
        // Создаем элемент уведомления
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} border-0"
                 role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        // Добавляем в контейнер для уведомлений
        if (!$('#toast-container').length) {
            $('body').append('<div id="toast-container" class="toast-container position-fixed top-0 end-0 p-3"></div>');
        }

        const $toast = $(toastHtml);
        $('#toast-container').append($toast);

        // Инициализируем и показываем уведомление
        const toast = new bootstrap.Toast($toast[0]);
        toast.show();

        // Удаляем уведомление после скрытия
        $toast.on('hidden.bs.toast', function() {
            $toast.remove();
        });
    }

    // Обновление состояния кнопок избранного при загрузке страницы
    function updateFavoriteButtons() {
        $('.favorite-btn').each(function() {
            const $btn = $(this);
            const productId = $btn.data('product-id');

            $.ajax({
                url: `/products/favorite/check/${productId}/`,
                type: 'GET',
                success: function(response) {
                    const $icon = $btn.find('i');
                    if (response.is_favorite) {
                        $icon.removeClass('bi-heart').addClass('bi-heart-fill text-danger');
                    } else {
                        $icon.removeClass('bi-heart-fill text-danger').addClass('bi-heart');
                    }
                }
            });
        });
    }

    // Обновляем состояние кнопок при загрузке страницы
    updateFavoriteButtons();
});
