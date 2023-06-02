
#include <ctime>
#include <string>

#include "logging.hpp"



std::shared_ptr<spdlog::logger> logging::new_ad_hoc_logger(
    const std::string gameID,
    const bool isTest
) {
    /*
        Create a new logger instance
        that points to a new log file.

        log file name structure:
        TIMESTAMP_IDPREFIX_game-info.log
    */


    // std::time is not guranteed to work by the language
    // but we can expect it to work on Linux.
    const std::string nowUnixTS = std::to_string(std::time(nullptr));


    const std::string fileName = nowUnixTS + "_" + gameID.substr(0, 3) + "_game-info.log";
    const std::string loggerName = "game";
    std::shared_ptr<spdlog::logger> logger;
    if (isTest) {
        logger = spdlog::null_logger_mt(loggerName);
    } else {
        logger = spdlog::basic_logger_mt(loggerName, "logs/" + fileName);
        logger->set_level(spdlog::level::info);
    }
    return logger;
}
