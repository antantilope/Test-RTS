
#include <iostream>

#include "game.hpp"


using namespace std;

Game::Game(const bool& isUnitTesting) {
    isTest = isUnitTesting;
    phase = constants::PHASE_0_LOBBY;

    W_IGNORE_START NO_WAGGREGATE_RETURN
    logger = logging::new_ad_hoc_logger(id, isUnitTesting);
    logger->info("logger created for game " + id);
    W_IGNORE_STOP
    logger->flush();
}

const int& Game::getPhase() {
    return phase;
}
