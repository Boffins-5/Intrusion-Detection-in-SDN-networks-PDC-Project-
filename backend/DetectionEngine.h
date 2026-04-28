#ifndef DETECTION_ENGINE_H
#define DETECTION_ENGINE_H

// FIX: removed #include "DetectionEngine.h" (was causing self-include)
#include <vector>
#include <string>
#include "Packet.h"

class DetectionEngine {
public:
    // Each function runs all 3 approaches and returns results
    static DetectionResult runSequential   (const std::vector<Packet>& buf, const std::string& attack);
    static DetectionResult runParallelOMP  (const std::vector<Packet>& buf, const std::string& attack);
    static DetectionResult runSimulatedMPI (const std::vector<Packet>& buf, const std::string& attack);

private:
    // ── Per-packet classification (rule-based) ──
    // These receive pre-computed thresholds derived from aggregate stats
    static bool classifyICMP      (int src, const std::vector<int>& icmpCountBySrc, int threshold);
    static bool classifyTCPSYN    (int src, const std::vector<int>& synBySrc,
                                             const std::vector<int>& ackBySrc,   double ratio);
    static bool classifySlowloris (int src, const std::vector<double>& firstSeen,
                                             const std::vector<double>& lastSeen,
                                             const std::vector<int>&    pktBySrc,
                                             double durationThresh, double rateThresh);
    static bool classifyAnomaly   (int src, const std::vector<int>& countBySrc,
                                             double mean, double stddev);
};

#endif
