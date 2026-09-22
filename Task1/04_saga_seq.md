# Sequence-диаграммы Saga-хореографии оформления заказа

## Успешное оформление заказа

```mermaid
sequenceDiagram
autonumber
actor Buyer as Покупатель
participant Mobile as Mobile App
participant Gateway as API Gateway
participant Order as Order Service
participant Broker as Event Broker
participant Catalog as Catalog Service
participant Inventory as Inventory Service
participant Payment as Payment Service
participant PayGate as Платежный шлюз
participant Delivery as Delivery Service
participant Logistics as Логистический провайдер
participant Seller as Seller Service
participant Notify as Notification Service

Buyer->>Mobile: Подтверждает оформление заказа
Mobile->>Gateway: POST /orders
Gateway->>Order: CreateOrder(cartId, address, deliveryMethod, paymentMethod)
Order->>Order: Создать заказ со статусом PendingValidation
Order-->>Broker: OrderCreated

Broker-->>Catalog: OrderCreated
Catalog->>Catalog: Проверить товары, цены и доступность карточек
Catalog-->>Broker: OrderItemsValidated

Broker-->>Inventory: OrderItemsValidated
Inventory->>Inventory: Зарезервировать товары
Inventory-->>Broker: StockReserved

Broker-->>Payment: StockReserved
Payment->>Payment: Создать платежную попытку
Payment-->>Broker: PaymentRequested
Payment->>PayGate: Capture payment
PayGate-->>Payment: Payment accepted
Payment-->>Broker: PaymentSucceeded

Broker-->>Order: PaymentSucceeded
Order->>Order: Обновить статус на Paid
Order-->>Broker: OrderPaid

Broker-->>Delivery: PaymentSucceeded
Delivery->>Logistics: CreateShipment(address, items)
Logistics-->>Delivery: trackingNumber, eta
Delivery-->>Broker: DeliveryCreated

Broker-->>Order: DeliveryCreated
Order->>Order: Обновить статус на ReadyForDelivery
Order-->>Broker: OrderReadyForDelivery

Broker-->>Seller: OrderReadyForDelivery
Broker-->>Notify: OrderReadyForDelivery
Notify-->>Buyer: Push: заказ оплачен и готовится к отправке
Notify-->>Seller: Уведомление: подготовить товар к отправке

Note over Order,Delivery: Дальше Delivery Service публикует ShipmentStatusChanged,<br/>а Order Service обновляет видимый статус заказа.
```

## Ошибка до оплаты: цена изменилась или товара не хватает

```mermaid
sequenceDiagram
autonumber
actor Buyer as Покупатель
participant Mobile as Mobile App
participant Gateway as API Gateway
participant Order as Order Service
participant Broker as Event Broker
participant Catalog as Catalog Service
participant Inventory as Inventory Service
participant Notify as Notification Service

Buyer->>Mobile: Подтверждает оформление заказа
Mobile->>Gateway: POST /orders
Gateway->>Order: CreateOrder(cartId, address, deliveryMethod, paymentMethod)
Order->>Order: Создать заказ со статусом PendingValidation
Order-->>Broker: OrderCreated

alt Цена или состав заказа устарели
  Broker-->>Catalog: OrderCreated
  Catalog->>Catalog: Проверить товары и актуальные цены
  Catalog-->>Broker: OrderItemsValidationFailed
  Broker-->>Order: OrderItemsValidationFailed
  Order->>Order: Обновить статус на Cancelled
  Order-->>Broker: OrderCancelled
  Broker-->>Notify: OrderCancelled
  Notify-->>Buyer: Push: заказ отменен, цена или товар изменились
else Недостаточно товара на складе
  Broker-->>Catalog: OrderCreated
  Catalog-->>Broker: OrderItemsValidated
  Broker-->>Inventory: OrderItemsValidated
  Inventory->>Inventory: Попытаться зарезервировать товары
  Inventory-->>Broker: StockReservationFailed
  Broker-->>Order: StockReservationFailed
  Order->>Order: Обновить статус на Cancelled
  Order-->>Broker: OrderCancelled
  Broker-->>Notify: OrderCancelled
  Notify-->>Buyer: Push: заказ отменен, товара недостаточно
end

Note over Order,Inventory: Денег еще не списывали, поэтому компенсация ограничивается отменой заказа.
```

## Ошибка оплаты: резерв нужно снять

```mermaid
sequenceDiagram
autonumber
participant Order as Order Service
participant Broker as Event Broker
participant Inventory as Inventory Service
participant Payment as Payment Service
participant PayGate as Платежный шлюз
participant Notify as Notification Service
actor Buyer as Покупатель

Order-->>Broker: OrderCreated
Broker-->>Inventory: OrderItemsValidated
Inventory->>Inventory: Зарезервировать товары
Inventory-->>Broker: StockReserved
Broker-->>Payment: StockReserved
Payment-->>Broker: PaymentRequested
Payment->>PayGate: Capture payment
PayGate-->>Payment: Payment declined
Payment-->>Broker: PaymentFailed

Broker-->>Order: PaymentFailed
Order->>Order: Обновить статус на Cancelled
Order-->>Broker: OrderCancelled

Broker-->>Inventory: PaymentFailed
Inventory->>Inventory: Снять резерв
Inventory-->>Broker: StockReleased

Broker-->>Notify: OrderCancelled
Notify-->>Buyer: Push: оплата не прошла, заказ отменен

Note over Payment,Inventory: PaymentFailed может быть также опубликован по таймауту оплаты.
```

## Ошибка доставки после оплаты: нужен возврат

```mermaid
sequenceDiagram
autonumber
participant Order as Order Service
participant Broker as Event Broker
participant Inventory as Inventory Service
participant Payment as Payment Service
participant PayGate as Платежный шлюз
participant Delivery as Delivery Service
participant Logistics as Логистический провайдер
participant Notify as Notification Service
actor Buyer as Покупатель

Order-->>Broker: OrderCreated
Broker-->>Inventory: OrderItemsValidated
Inventory-->>Broker: StockReserved
Broker-->>Payment: StockReserved
Payment->>PayGate: Capture payment
PayGate-->>Payment: Payment accepted
Payment-->>Broker: PaymentSucceeded

Broker-->>Delivery: PaymentSucceeded
Delivery->>Logistics: CreateShipment(address, items)
Logistics-->>Delivery: Delivery rejected
Delivery-->>Broker: DeliveryCreationFailed

Broker-->>Order: DeliveryCreationFailed
Order->>Order: Обновить статус на DeliveryFailedPendingRefund

Broker-->>Payment: DeliveryCreationFailed
Payment-->>Broker: RefundRequested
Payment->>PayGate: Refund payment

alt Возврат выполнен
  PayGate-->>Payment: Refund accepted
  Payment-->>Broker: RefundSucceeded
  Broker-->>Inventory: RefundSucceeded
  Inventory->>Inventory: Снять резерв
  Inventory-->>Broker: StockReleased
  Broker-->>Order: RefundSucceeded
  Order->>Order: Обновить статус на Cancelled
  Order-->>Broker: OrderCancelled
  Broker-->>Notify: OrderCancelled
  Notify-->>Buyer: Push: доставка недоступна, деньги возвращены
else Возврат не выполнен автоматически
  PayGate-->>Payment: Refund rejected
  Payment-->>Broker: RefundFailed
  Broker-->>Order: RefundFailed
  Order->>Order: Обновить статус на CompensationRequired
  Broker-->>Notify: RefundFailed
  Notify-->>Buyer: Push: заказ требует проверки, поддержка свяжется с вами
end
```
