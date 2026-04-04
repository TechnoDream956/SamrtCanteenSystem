#include "../services/AuthService.h"
#include <iostream>
#include <string>
#include <vector>

void printHelp() {
    std::cout << "Usage: auth_tool [options]" << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  --generate-otp              Generate a numeric 6-digit OTP" << std::endl;
    std::cout << "  --validate-password <pass>  Validate password strength" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        printHelp();
        return 1;
    }

    std::string command = argv[1];

    if (command == "--generate-otp") {
        std::cout << AuthService::generateOTP();
        return 0;
    } 
    else if (command == "--validate-password") {
        if (argc < 3) {
            std::cerr << "Error: Password missing" << std::endl;
            return 1;
        }
        std::string password = argv[2];
        if (AuthService::validatePassword(password)) {
            // std::cout << "Valid" << std::endl;
            return 0; // Success
        } else {
            // std::cout << "Invalid" << std::endl;
            return 1; // Failure
        }
    } 
    else {
        printHelp();
        return 1;
    }

    return 0;
}
