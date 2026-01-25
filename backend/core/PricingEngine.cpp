#include "PricingEngine.h"

int PricingEngine::calculateFinalPrice(int basePrice, int delayMinutes) {
    if (delayMinutes <= 0)
        return basePrice;

    int discount = delayMinutes * 2;
    int maxDiscount = basePrice / 2;

    if (discount > maxDiscount)
        discount = maxDiscount;

    return basePrice - discount;
}
