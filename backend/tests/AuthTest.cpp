#include "../services/AuthService.h"
#include <iostream>
#include <cassert>

void testOTP() {
    std::string otp = AuthService::generateOTP();
    std::cout << "[INFO] Generated OTP: " << otp << std::endl;
    assert(otp.length() == 6);
}

void testPassword() {
    assert(AuthService::validatePassword("abc123") == true);
    assert(AuthService::validatePassword("abc") == false);
}

int main() {
    std::cout << "--- [C++ AuthService Unit Test] ---" << std::endl;
    testOTP();
    testPassword();
    std::cout << "[SUCCESS] Unit tests passed." << std::endl;
    return 0;
}
