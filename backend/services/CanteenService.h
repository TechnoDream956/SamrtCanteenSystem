#ifndef CANTEEN_SERVICE_H
#define CANTEEN_SERVICE_H

#include <string>

class CanteenService {
public:
    /**
     * @brief Calculates priority for an order.
     * 
     * @param waitingTime Seconds since order creation.
     * @param expectedTime Total estimated prep time.
     * @param itemsCount Number of items in order.
     * @return double Calculated priority score.
     */
    static double calculatePriority(double waitingTime, double expectedTime, int itemsCount);

    /**
     * @brief Calculates dynamic ETA based on current load.
     * 
     * @param totalTime Sum of individual item times.
     * @param activeOrders Current orders in queue.
     * @return int Estimated time in minutes.
     */
    static int calculateETA(int totalTime, int activeOrders);

    /**
     * @brief Validates if an order can transition between statuses.
     * 
     * @param current Current status string.
     * @param next Next status string.
     * @return true if valid, false otherwise.
     */
    static bool validateStatusFlow(const std::string& current, const std::string& next);

    /**
     * @brief Verifies if the user-provided OTP matches the stored one.
     * 
     * @param input The OTP provided by the user.
     * @param actual The real OTP stored in memory/DB.
     * @return true if match, false otherwise.
     */
    static bool verifyOTP(const std::string& input, const std::string& actual);
};

#endif // CANTEEN_SERVICE_H
