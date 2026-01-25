#ifndef ORDER_SERVICE_H
#define ORDER_SERVICE_H

#include "../core/Order.h"

class OrderService {
public:
    static Order createOrder(int orderId, int canteenId, int itemId, int expectedTime);
    static void acceptOrder(Order &order);
    static void markReady(Order &order);
    static void completeOrder(Order &order, int basePrice);
};

#endif
