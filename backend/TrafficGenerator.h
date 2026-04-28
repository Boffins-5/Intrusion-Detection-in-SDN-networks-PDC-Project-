#ifndef TRAFFIC_GENERATOR_H
#define TRAFFIC_GENERATOR_H

#include <vector>
#include <string>
#include "Packet.h"    // FIX: uppercase P to match filename

class TrafficGenerator {
public:
    static std::vector<Packet> generate(
        int                nodes,
        std::vector<int>   targets,
        const std::string& attack,
        int                count
    );
};

#endif
