#include "CanteenService.h"
#include <string>

double CanteenService::calculatePriority(double waitingTime, double expectedTime, int itemsCount) {
    // Standard priority algorithm: expectedTime * 2 + itemsCount * 3 - waitingTime / 10
    double priority = (expectedTime * 2.0) + (itemsCount * 3.0) - (waitingTime / 10.0);
    return priority;
}

int CanteenService::calculateETA(int totalTime, int activeOrders) {
    // Dynamic ETA: totalTime + (active_orders * 2 minutes)
    return totalTime + (activeOrders * 2);
}

bool CanteenService::validateStatusFlow(const std::string& current, const std::string& next) {
    // Current allowed transitions:
    // WAITING -> ACCEPTED
    // WAITING -> CANCELLED
    // ACCEPTED -> PREPARING
    // ACCEPTED -> CANCELLED
    // PREPARING -> READY
    // READY -> COMPLETED

    if (current == "WAITING") {
        return (next == "ACCEPTED" || next == "CANCELLED");
    }
    if (current == "ACCEPTED") {
        return (next == "PREPARING" || next == "CANCELLED");
    }
    if (current == "PREPARING") {
        return (next == "READY");
    }
    if (current == "READY") {
        return (next == "COMPLETED");
    }
    
    return false;
}

bool CanteenService::verifyOTP(const std::string& input, const std::string& actual) {
    if (input.empty() || actual.empty()) return false;
    return (input == actual);
}
