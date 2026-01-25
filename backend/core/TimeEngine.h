#ifndef TIME_ENGINE_H
#define TIME_ENGINE_H

#include "Order.h"

class TimeEngine {
public:
    static void markAccepted(Order &order);
    static void markReady(Order &order);
    static void markPickedUp(Order &order);
    static int calculatePrepDelay(const Order &order);
};

#endif
