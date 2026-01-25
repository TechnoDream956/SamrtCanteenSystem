#ifndef ORDER_H
#define ORDER_H

enum OrderStatus {
    CREATED,
    ACCEPTED,
    READY,
    COMPLETED
};

struct Order {
    int orderId;
    int canteenId;
    int itemId;

    OrderStatus status;

    int expectedPrepTime;
    int finalPrice;

    long acceptedTime;
    long readyTime;
    long pickupTime;
};

#endif
