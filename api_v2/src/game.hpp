
#ifndef GAME_H
#define GAME_H

#include <string>
#include "spdlog/logger.h"
#include "base_models.hpp"


using namespace std;


class Game: public BaseModel
{
    protected:
        bool isTest;
        shared_ptr<spdlog::logger> logger;

        int phase;


    public:
        Game(bool testing);
        int getPhase();
};

#endif

