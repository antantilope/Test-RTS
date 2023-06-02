
#ifndef WARNINGS_H
#define WARNINGS_H
    #define W_IGNORE_START _Pragma("GCC diagnostic push")
    #define NO_WAGGREGATE_RETURN _Pragma("GCC diagnostic ignored \"-Waggregate-return\"")
    #define W_IGNORE_STOP _Pragma("GCC diagnostic pop")
#endif
