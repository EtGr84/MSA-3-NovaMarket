
## События

| Этап | Тип события | Название | Публикует | Основные потребители |
| --- | --- | --- | --- | --- |
| Заказ создан после подтверждения корзины | domain | `OrderCreated` | Order Service | Catalog Service, Order Service |
| Состав и цены заказа подтверждены | domain | `OrderItemsValidated` | Catalog Service | Inventory Service, Order Service |
| Состав или цена заказа не подтверждены | failure | `OrderItemsValidationFailed` | Catalog Service | Order Service, Notification Service |
| Товары зарезервированы | domain | `StockReserved` | Inventory Service | Payment Service, Order Service |
| Недостаточно товара для резерва | failure | `StockReservationFailed` | Inventory Service | Order Service, Notification Service |
| Запрошена оплата | domain | `PaymentRequested` | Payment Service | Order Service |
| Оплата прошла успешно | domain | `PaymentSucceeded` | Payment Service | Order Service, Delivery Service, Notification Service |
| Оплата отклонена | failure | `PaymentFailed` | Payment Service | Order Service, Inventory Service, Notification Service |
| Заказ отмечен как оплаченный | domain | `OrderPaid` | Order Service | Notification Service |
| Заявка на доставку создана | domain | `DeliveryCreated` | Delivery Service | Order Service, Notification Service |
| Логистический провайдер не создал доставку | failure | `DeliveryCreationFailed` | Delivery Service | Order Service, Payment Service, Notification Service |
| Заказ готовится к передаче в доставку | domain | `OrderReadyForDelivery` | Order Service | Seller Service, Notification Service |
| Запрошен возврат платежа | compensation | `RefundRequested` | Payment Service | Order Service |
| Возврат платежа выполнен | compensation | `RefundSucceeded` | Payment Service | Order Service, Inventory Service, Notification Service |
| Возврат платежа не выполнен автоматически | failure | `RefundFailed` | Payment Service | Order Service, Notification Service, Support process |
| Резерв товаров снят | compensation | `StockReleased` | Inventory Service | Catalog Service, Order Service |
| Заказ отменен | compensation | `OrderCancelled` | Order Service | Notification Service, Seller Service |
| Статус доставки изменился | domain | `ShipmentStatusChanged` | Delivery Service | Order Service, Notification Service, Seller Service |

## Правила обработки

| Правило | Описание |
| --- | --- |
| Идемпотентность | Каждый обработчик хранит `eventId` во входящем журнале и повторно не применяет одно и то же событие. |
| Outbox | Сервис сначала фиксирует изменение состояния и событие в своей БД, затем outbox-publisher отправляет событие в брокер. |
| Таймаут оплаты | Если после `PaymentRequested` нет `PaymentSucceeded` за заданное время, Payment Service публикует `PaymentFailed` с причиной `timeout`. |
| Компенсация до оплаты | При `OrderItemsValidationFailed` или `StockReservationFailed` заказ отменяется без возврата денег. |
| Компенсация после резерва | При `PaymentFailed` Inventory Service снимает резерв и публикует `StockReleased`. |
| Компенсация после оплаты | При `DeliveryCreationFailed` Payment Service делает возврат. После `RefundSucceeded` Inventory Service снимает резерв, а Order Service отменяет заказ. |
| Ручное вмешательство | `RefundFailed` переводит заказ в состояние `CompensationRequired`, чтобы поддержка вручную завершила возврат. |
