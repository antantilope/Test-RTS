
#ifndef LOGGING_H
#define LOGGING_H

#include<string>

#include "spdlog/common.h"
#include "spdlog/logger.h"
#include "spdlog/sinks/basic_file_sink.h"
#include "spdlog/sinks/null_sink.h"

namespace logging
{
    std::shared_ptr<spdlog::logger> new_ad_hoc_logger(std::string gameID, bool isTest);
}

#endif
