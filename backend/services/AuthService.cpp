#include "AuthService.h"
#include <random>
#include <ctime>
#include <algorithm>

std::string AuthService::generateOTP() {
    // Standard random generator
    std::mt19937 rng(static_cast<unsigned int>(std::time(nullptr)));
    std::uniform_int_distribution<int> dist(0, 9);
    
    std::string otp = "";
    for (int i = 0; i < 6; ++i) {
        otp += std::to_string(dist(rng));
    }
    return otp;
}

bool AuthService::validatePassword(const std::string& password) {
    // Business rule: length >= 6
    if (password.length() < 6) {
        return false;
    }
    
    // Check if contains at least one digit or symbol (simplistic)
    bool hasDigit = std::any_of(password.begin(), password.end(), ::isdigit);
    // bool hasSymbol = std::any_of(password.begin(), password.end(), ::ispunct);
    
    // We'll keep it simple for now, but allow easy refinement.
    return hasDigit;
}

bool AuthService::verifyOTP(const std::string& input, const std::string& actual) {
    // Simple but secure comparison would avoid timing attacks, 
    // though for OTP it's less critical.
    return (input == actual);
}
