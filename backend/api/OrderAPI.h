#ifndef ORDER_API_H
#define ORDER_API_H

#include "../core/Order.h"

class OrderAPI {
public:
    static Order createOrderAPI(
        int orderId,
        int canteenId,
        int itemId,
        int expectedPrepTime
    );

    static void acceptOrderAPI(Order &order);
    static void markReadyAPI(Order &order);
    static void pickupOrderAPI(
        Order &order,
        int basePrice
    );
};

#endif
