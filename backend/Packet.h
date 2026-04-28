#ifndef PACKET_H
#define PACKET_H

#include <string>

// =========================================================
// TCP Flags (bitmask)
// =========================================================
#define FLAG_SYN  0x01
#define FLAG_ACK  0x02
#define FLAG_FIN  0x04

// =========================================================
// PACKET
// =========================================================
struct Packet {
    int    sourceId;
    int    targetId;
    std::string payload;

    bool   isMalicious;   // ground truth (set by TrafficGenerator)

    int    protocol;      // 0=HTTP/Slowloris  1=TCP  2=Flow  3=ICMP
    int    size;
    int    flags;         // TCP flags bitmask (FLAG_SYN / FLAG_ACK)
    double timestamp;     // simulated time (seconds)
};

// =========================================================
// DETECTION RESULT
// =========================================================
struct DetectionResult {
    int TP = 0;
    int FP = 0;
    int FN = 0;
    int TN = 0;

    double executionTime = 0.0;   // microseconds
};

#endif
