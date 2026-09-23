---

# Перечень микросервисов

| Микросервис | Назначение | Основные события |
| --- | --- | --- |
| Auth Service | Аутентификация покупателей и продавцов, роли доступа. | Не участвует в Saga оформления заказа. |
| Catalog Service | Карточки товаров, категории, текущие цены, описание, фото. Поддерживает актуальность каталога через события остатков и рейтинга. | `ProductUpdated`, `PriceChanged`; consumes `StockLevelChanged`, `ProductRatingChanged`, `OrderCreated`. |
| Review Service | Хранит отзывы, пересчитывает рейтинг товара. | `ReviewCreated`, `ProductRatingChanged`. |
| Cart Service | Хранит корзины покупателей до оформления заказа. | `CartChanged`; передает состав корзины в команду создания заказа. |
| Order Service | Создает заказ, хранит статус, публикует стартовое событие Saga и реагирует на результаты других сервисов. | `OrderCreated`, `OrderPaid`, `OrderReadyForDelivery`, `OrderCancelled`; consumes payment, inventory and delivery events. |
| Seller Service | Хранит заказы продавца и список товаров, которые нужно подготовить к отправке. | Consumes `OrderReadyForDelivery`, `ShipmentStatusChanged`, `OrderCancelled`. |
| Inventory Service | Проверяет доступность товаров, резервирует и освобождает остатки. | `StockReserved`, `StockReservationFailed`, `StockReleased`, `StockLevelChanged`; consumes `OrderItemsValidated`, `PaymentFailed`, `RefundSucceeded`. |
| Payment Service | Запускает оплату, хранит платежные попытки, работает с привязанными картами и возвратами. | `PaymentRequested`, `PaymentSucceeded`, `PaymentFailed`, `RefundSucceeded`, `RefundFailed`; consumes `StockReserved`, `DeliveryCreationFailed`. |
| Delivery Service | Создает заявку на доставку, получает трек-номер и обновления от логистики. | `DeliveryCreated`, `DeliveryCreationFailed`, `ShipmentStatusChanged`; consumes `PaymentSucceeded`. |
| Notification Service | Уведомляет покупателя о статусах и продавца о заказе, который нужно подготовить. | Consumes `OrderPaid`, `OrderReadyForDelivery`, `OrderCancelled`, `PaymentFailed`, `ShipmentStatusChanged`. |39 minutes ago

---

# Ключевые решения

| Решение | Обоснование |
| --- | --- |
| Брокер событий как центральный транспорт | Несколько сервисов потребляют одни и те же события: например, `OrderReadyForDelivery` нужен заказам, продавцу и уведомлениям. Это упрощает подключение будущих сервисов рекомендаций, аналитики и антифрода. |
| Собственное хранилище на сервис | Сервисы масштабируются и эволюционируют независимо. Для пользовательских экранов используются локальные read-модели, обновляемые событиями. |
| Saga-хореография вместо оркестратора | Для MVP меньше инфраструктурной сложности, а границы ответственности остаются в доменных сервисах. Компенсации оформлены отдельными событиями. |
| Синхронные REST-запросы только для пользовательских команд и чтения | Действия пользователя должны получить быстрый ответ, а длительные этапы оформления заказа продолжаются асинхронно через события. |

---
