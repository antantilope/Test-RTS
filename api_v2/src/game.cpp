
#include <iostream>
#include <string>

#include "constants.hpp"
#include "game.hpp"
#include "uuid.hpp"
#include "logging.hpp"


using namespace std;

Game::Game(bool isUnitTesting) {
    isTest = isUnitTesting;
    phase = constants::PHASE_0_LOBBY;
    logger = logging::new_ad_hoc_logger(id, isUnitTesting);
    logger->info("logger created for game " + id);
    logger->flush();
}

int Game::getPhase() {
    return phase;
}


