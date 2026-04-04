#include "../services/AuthService.h"
#include "../services/CanteenService.h"
#include <iostream>
#include <string>

void printHelp() {
    std::cout << "Usage: canteen_tool [options]" << std::endl;
    std::cout << "Authentication Options:" << std::endl;
    std::cout << "  --generate-otp              Generate a numeric 6-digit OTP" << std::endl;
    std::cout << "  --validate-password <pass>  Validate password strength" << std::endl;
    std::cout << "Canteen Options:" << std::endl;
    std::cout << "  --calc-priority <wait> <exp> <n>  Calculate order priority" << std::endl;
    std::cout << "  --calc-eta <total> <active>       Calculate dynamic ETA" << std::endl;
    std::cout << "  --validate-flow <curr> <next>     Validate status transition" << std::endl;
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
        if (argc < 3) return 1;
        return AuthService::validatePassword(argv[2]) ? 0 : 1;
    }
    else if (command == "--calc-priority") {
        if (argc < 5) return 1;
        double wait = std::stod(argv[2]);
        double exp  = std::stod(argv[3]);
        int n       = std::stoi(argv[4]);
        std::cout << CanteenService::calculatePriority(wait, exp, n);
        return 0;
    }
    else if (command == "--calc-eta") {
        if (argc < 4) return 1;
        int total  = std::stoi(argv[2]);
        int active = std::stoi(argv[3]);
        std::cout << CanteenService::calculateETA(total, active);
        return 0;
    }
    else if (command == "--validate-flow") {
        if (argc < 4) return 1;
        return CanteenService::validateStatusFlow(argv[2], argv[3]) ? 0 : 1;
    }
    else if (command == "--verify-otp") {
        if (argc < 4) return 1;
        return CanteenService::verifyOTP(argv[2], argv[3]) ? 0 : 1;
    }
    else {
        printHelp();
        return 1;
    }

    return 0;
}
