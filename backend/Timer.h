#ifndef TIMER_H
#define TIMER_H
#include <chrono>

class Timer {
    std::chrono::time_point<std::chrono::high_resolution_clock> _start;
public:
    void   start() { _start = std::chrono::high_resolution_clock::now(); }
    double stop()  {
        auto end = std::chrono::high_resolution_clock::now();
        return (double)std::chrono::duration_cast<std::chrono::microseconds>(
            end - _start).count();
    }
};

#endif
