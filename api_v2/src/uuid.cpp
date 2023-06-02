#include <random>
#include <sstream>

#include "uuid.hpp"


static std::random_device              rd;
static std::mt19937                    gen(rd());
static std::uniform_int_distribution<> dis(0, 15);
static std::uniform_int_distribution<> dis2(8, 11);

void uuid::v4(std::stringstream& strstream) {
    /* Move data onto a stringsteam.
    */

    int i;
    strstream << std::hex;
    for (i = 0; i < 8; i++) {
        strstream << dis(gen);
    }
    strstream << "-";
    for (i = 0; i < 4; i++) {
        strstream << dis(gen);
    }
    strstream << "-4";
    for (i = 0; i < 3; i++) {
        strstream << dis(gen);
    }
    strstream << "-";
    strstream << dis2(gen);
    for (i = 0; i < 3; i++) {
        strstream << dis(gen);
    }
    strstream << "-";
    for (i = 0; i < 12; i++) {
        strstream << dis(gen);
    };
}
