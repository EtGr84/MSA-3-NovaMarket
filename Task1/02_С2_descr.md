| Микросервис | Назначение | Основные события |
| --- | --- | --- |
| Inventory Service | Контроль наличия товарных запасов, выполнение и отмена резервирования. | `StockReserved`, `StockReservationFailed`, `StockReleased`, `StockLevelChanged`; consumes `OrderItemsValidated`, `PaymentFailed`, `RefundSucceeded`. |
| Cart Service | Управление временными списками покупок пользователей перед чекаутом. | `CartChanged`; передает состав корзины в команду создания заказа. |
| Auth Service | Управление правами доступа и проверка подлинности клиентов и мерчантов. | Не участвует в Saga оформления заказа. |
| Delivery Service | Оформление логистических запросов, трекинг отправлений и интеграция со службами доставки. | `DeliveryCreated`, `DeliveryCreationFailed`, `ShipmentStatusChanged`; consumes `PaymentSucceeded`. |
| Catalog Service | Управление товарными позициями, категориями, медиафайлами и актуальными ценами. Синхронизирует состояние на основе изменений остатков и оценок. | `ProductUpdated`, `PriceChanged`; consumes `StockLevelChanged`, `ProductRatingChanged`, `OrderCreated`. |
| Payment Service | Проведение транзакций, фиксация платежных попыток, обработка возвратов средств и карт. | `PaymentRequested`, `PaymentSucceeded`, `PaymentFailed`, `RefundSucceeded`, `RefundFailed`; consumes `StockReserved`, `DeliveryCreationFailed`. |
| Review Service | Аккумулирует клиентские отклики и вычисляет итоговую оценку продукции. | `ReviewCreated`, `ProductRatingChanged`. |
| Notification Service | Рассылка оповещений клиентам о статусах и отправка мерчантам информации о новых сборочных заданиях. | Consumes `OrderPaid`, `OrderReadyForDelivery`, `OrderCancelled`, `PaymentFailed`, `ShipmentStatusChanged`. |
| Order Service | Инициализация и ведение жизненного цикла заказов, запуск Саги и обработка статусов от смежных модулей. | `OrderCreated`, `OrderPaid`, `OrderReadyForDelivery`, `OrderCancelled`; consumes payment, inventory and delivery events. |
| Seller Service | Обработка заказов со стороны мерчантов и формирование перечня товаров к сборке. | Consumes `OrderReadyForDelivery`, `ShipmentStatusChanged`, `OrderCancelled`. |
