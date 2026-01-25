#include "TimeEngine.h"
#include <ctime>

void TimeEngine::markAccepted(Order &order) {
    order.acceptedTime = std::time(nullptr);
    order.status = ACCEPTED;
}

void TimeEngine::markReady(Order &order) {
    order.readyTime = std::time(nullptr);
    order.status = READY;
}

void TimeEngine::markPickedUp(Order &order) {
    order.pickupTime = std::time(nullptr);
    order.status = COMPLETED;
}

int TimeEngine::calculatePrepDelay(const Order &order) {
    int actualMinutes = (order.readyTime - order.acceptedTime) / 60;
    if (actualMinutes > order.expectedPrepTime)
        return actualMinutes - order.expectedPrepTime;
    return 0;
}
