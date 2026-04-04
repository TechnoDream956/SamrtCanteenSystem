#ifndef AUTH_SERVICE_H
#define AUTH_SERVICE_H

#include <string>
#include <vector>

class AuthService {
public:
    /**
     * @brief Generates a secure random 6-digit OTP.
     * 
     * @return std::string 6-digit code.
     */
    static std::string generateOTP();

    /**
     * @brief Validates a password against security rules.
     * 
     * @param password The password to check.
     * @return true if valid, false otherwise.
     */
    static bool validatePassword(const std::string& password);

    /**
     * @brief Verifies that two OTPs match.
     * 
     * @param input User input.
     * @param actual Stored OTP.
     * @return true if match, false otherwise.
     */
    static bool verifyOTP(const std::string& input, const std::string& actual);
};

#endif // AUTH_SERVICE_H
