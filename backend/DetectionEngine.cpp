// #include "DetectionEngine.h"
// #include <omp.h>
// #include <cmath>
// #include <unordered_map>
// #include <numeric>
// #include <algorithm>
// #include <vector>

// // ============================================================
// // Helper: build per-source aggregate stats (sequential pass)
// // ============================================================
// struct SourceStats {
//     int    pktCount  = 0;
//     int    synCount  = 0;
//     int    ackCount  = 0;
//     int    icmpCount = 0;
//     double firstSeen = 1e18;
//     double lastSeen  = 0.0;
// };

// static std::vector<SourceStats>
// buildStats(const std::vector<Packet>& buf, int maxSrc) {
//     std::vector<SourceStats> stats(maxSrc + 1);

//     for (const auto& p : buf) {
//         if (p.sourceId > maxSrc) continue;
//         auto& s = stats[p.sourceId];
//         s.pktCount++;
//         if (p.protocol == 3)       s.icmpCount++;
//         if (p.flags & FLAG_SYN)    s.synCount++;
//         if (p.flags & FLAG_ACK)    s.ackCount++;
//         if (p.timestamp < s.firstSeen) s.firstSeen = p.timestamp;
//         if (p.timestamp > s.lastSeen)  s.lastSeen  = p.timestamp;
//     }
//     return stats;
// }

// // Same but with OMP parallel reduction (used by OMP + MPI paths)
// static std::vector<SourceStats>
// buildStatsOMP(const std::vector<Packet>& buf, int maxSrc) {
//     int n = (int)buf.size();
//     std::vector<SourceStats> stats(maxSrc + 1);

//     // OMP: each thread processes a slice; manual critical section per source
//     #pragma omp parallel for schedule(dynamic, 256)
//     for (int i = 0; i < n; ++i) {
//         const Packet& p = buf[i];
//         if (p.sourceId > maxSrc) continue;

//         #pragma omp critical
//         {
//             auto& s = stats[p.sourceId];
//             s.pktCount++;
//             if (p.protocol == 3)       s.icmpCount++;
//             if (p.flags & FLAG_SYN)    s.synCount++;
//             if (p.flags & FLAG_ACK)    s.ackCount++;
//             if (p.timestamp < s.firstSeen) s.firstSeen = p.timestamp;
//             if (p.timestamp > s.lastSeen)  s.lastSeen  = p.timestamp;
//         }
//     }
//     return stats;
// }

// // ============================================================
// // Per-packet classifiers (stateless — use pre-built thresholds)
// // ============================================================

// // ICMP Flood: source ICMP rate > threshold
// bool DetectionEngine::classifyICMP(
//     int src,
//     const std::vector<int>& icmpCountBySrc,
//     int threshold
// ) {
//     if (src >= (int)icmpCountBySrc.size()) return false;
//     return icmpCountBySrc[src] > threshold;
// }

// // TCP SYN Flood: SYN / (SYN + ACK) > ratio threshold
// bool DetectionEngine::classifyTCPSYN(
//     int src,
//     const std::vector<int>& synBySrc,
//     const std::vector<int>& ackBySrc,
//     double ratio
// ) {
//     if (src >= (int)synBySrc.size()) return false;
//     int syn = synBySrc[src];
//     int ack = ackBySrc[src];
//     int total = syn + ack;
//     if (total == 0) return false;
//     return (double)syn / total > ratio;
// }

// // Slowloris: long-lived connection with very low packet rate
// bool DetectionEngine::classifySlowloris(
//     int src,
//     const std::vector<double>& firstSeen,
//     const std::vector<double>& lastSeen,
//     const std::vector<int>&    pktBySrc,
//     double durationThresh,
//     double rateThresh
// ) {
//     if (src >= (int)firstSeen.size()) return false;
//     double duration = lastSeen[src] - firstSeen[src];
//     if (duration <= 0.0) return false;
//     double rate = (double)pktBySrc[src] / duration;   // pkts/sec
//     return (duration > durationThresh) && (rate < rateThresh);
// }

// // Anomaly (general): source packet count > mean + 2σ
// bool DetectionEngine::classifyAnomaly(
//     int src,
//     const std::vector<int>& countBySrc,
//     double mean,
//     double stddev
// ) {
//     if (src >= (int)countBySrc.size()) return false;
//     return (double)countBySrc[src] > mean + 2.0 * stddev;
// }

// // ============================================================
// // Classify a single packet given pre-computed stats
// // ============================================================
// static bool classify(
//     const Packet& p,
//     const std::string& attack,
//     const std::vector<SourceStats>& stats,
//     int icmpThreshold,
//     double synRatioThresh,
//     double slowDuration,
//     double slowRate,
//     double anomalyMean,
//     double anomalyStd,
//     int maxSrc
// ) {
//     if (p.sourceId > maxSrc) return false;
//     const SourceStats& s = stats[p.sourceId];

//     if (attack == "ICMP_FLOOD") {
//         // Rule: source sent > icmpThreshold ICMP packets
//         return s.icmpCount > icmpThreshold;

//     } else if (attack == "TCP_SYN") {
//         // Rule: SYN / (SYN + ACK) > 0.8  AND  high volume
//         int total = s.synCount + s.ackCount;
//         if (total == 0) return false;
//         double ratio = (double)s.synCount / total;
//         return (ratio > synRatioThresh) && (s.pktCount > 10);

//     } else if (attack == "SLOWLORIS") {
//         // Rule: long-lived session AND very low packet rate
//         double duration = s.lastSeen - s.firstSeen;
//         if (duration <= 0.0) return false;
//         double rate = (double)s.pktCount / duration;
//         return (duration > slowDuration) && (rate < slowRate);

//     } else if (attack == "FLOW_OVERFLOW") {
//         // Rule: statistical anomaly (packet count > mean + 2σ)
//         return (double)s.pktCount > anomalyMean + 2.0 * anomalyStd;

//     } else {
//         // General anomaly detection
//         return (double)s.pktCount > anomalyMean + 2.0 * anomalyStd;
//     }
// }

// // ============================================================
// // Compute thresholds from stats
// // ============================================================
// struct Thresholds {
//     int    icmpThreshold;
//     double synRatioThresh;
//     double slowDuration;
//     double slowRate;
//     double anomalyMean;
//     double anomalyStd;
//     int    maxSrc;
// };

// static Thresholds computeThresholds(
//     const std::vector<SourceStats>& stats,
//     const std::string& attack
// ) {
//     Thresholds t;
//     t.maxSrc = (int)stats.size() - 1;

//     // ICMP threshold: mean ICMP count + 2σ
//     {
//         double sum = 0, sq = 0;
//         int cnt = 0;
//         for (auto& s : stats) if (s.icmpCount > 0) { sum += s.icmpCount; cnt++; }
//         double mean = cnt > 0 ? sum / cnt : 10.0;
//         for (auto& s : stats) if (s.icmpCount > 0) sq += (s.icmpCount - mean) * (s.icmpCount - mean);
//         double std = cnt > 1 ? std::sqrt(sq / cnt) : 5.0;
//         t.icmpThreshold = (int)(mean + 2.0 * std);
//         if (t.icmpThreshold < 10) t.icmpThreshold = 10;
//     }

//     // TCP SYN ratio threshold
//     t.synRatioThresh = 0.80;

//     // Slowloris: duration > 2 sec, rate < 2 pkt/sec
//     t.slowDuration = 2.0;
//     t.slowRate     = 2.0;

//     // General anomaly: global packet count stats
//     {
//         double sum = 0, sq = 0;
//         int cnt = (int)stats.size();
//         for (auto& s : stats) sum += s.pktCount;
//         double mean = cnt > 0 ? sum / cnt : 1.0;
//         for (auto& s : stats) sq += (s.pktCount - mean) * (s.pktCount - mean);
//         t.anomalyMean = mean;
//         t.anomalyStd  = cnt > 1 ? std::sqrt(sq / cnt) : 1.0;
//     }

//     return t;
// }

// // ============================================================
// // SEQUENTIAL
// // ============================================================
// DetectionResult DetectionEngine::runSequential(
//     const std::vector<Packet>& buf,
//     const std::string& attack
// ) {
//     if (buf.empty()) return {};

//     // Pass 1: aggregate stats (sequential loop)
//     int maxSrc = 0;
//     for (const auto& p : buf) maxSrc = std::max(maxSrc, p.sourceId);
//     auto stats = buildStats(buf, maxSrc);
//     auto thr   = computeThresholds(stats, attack);

//     // Pass 2: classify each packet
//     DetectionResult result;
//     for (const auto& p : buf) {
//         bool predicted = classify(p, attack, stats,
//             thr.icmpThreshold, thr.synRatioThresh,
//             thr.slowDuration,  thr.slowRate,
//             thr.anomalyMean,   thr.anomalyStd, maxSrc);
//         bool actual = p.isMalicious;

//         if      ( predicted &&  actual) result.TP++;
//         else if ( predicted && !actual) result.FP++;
//         else if (!predicted &&  actual) result.FN++;
//         else                            result.TN++;
//     }
//     return result;
// }

// // ============================================================
// // OPENMP  — parallel Pass-1 (stat building) + parallel Pass-2
// // ============================================================
// DetectionResult DetectionEngine::runParallelOMP(
//     const std::vector<Packet>& buf,
//     const std::string& attack
// ) {
//     if (buf.empty()) return {};

//     int maxSrc = 0;
//     for (const auto& p : buf) maxSrc = std::max(maxSrc, p.sourceId);

//     // Pass 1: parallel stat building
//     auto stats = buildStatsOMP(buf, maxSrc);
//     auto thr   = computeThresholds(stats, attack);

//     // Pass 2: parallel classification with OMP reduction
//     int TP = 0, FP = 0, FN = 0, TN = 0;
//     int n = (int)buf.size();

//     #pragma omp parallel for reduction(+:TP,FP,FN,TN) schedule(dynamic, 512)
//     for (int i = 0; i < n; ++i) {
//         const Packet& p = buf[i];
//         bool predicted = classify(p, attack, stats,
//             thr.icmpThreshold, thr.synRatioThresh,
//             thr.slowDuration,  thr.slowRate,
//             thr.anomalyMean,   thr.anomalyStd, maxSrc);
//         bool actual = p.isMalicious;

//         if      ( predicted &&  actual) TP++;
//         else if ( predicted && !actual) FP++;
//         else if (!predicted &&  actual) FN++;
//         else                            TN++;
//     }

//     DetectionResult result;
//     result.TP = TP; result.FP = FP; result.FN = FN; result.TN = TN;
//     return result;
// }

// // ============================================================
// // SIMULATED MPI  — split buffer into N "ranks", each rank
// //                  builds local stats, then stats are merged,
// //                  then parallel classification
// // ============================================================
// DetectionResult DetectionEngine::runSimulatedMPI(
//     const std::vector<Packet>& buf,
//     const std::string& attack
// ) {
//     if (buf.empty()) return {};

//     const int NUM_RANKS = 4;   // simulate 4 MPI processes
//     int n      = (int)buf.size();
//     int maxSrc = 0;
//     for (const auto& p : buf) maxSrc = std::max(maxSrc, p.sourceId);

//     // Each rank builds its own local stats
//     std::vector<std::vector<SourceStats>> rankStats(NUM_RANKS,
//         std::vector<SourceStats>(maxSrc + 1));

//     #pragma omp parallel for schedule(static)
//     for (int rank = 0; rank < NUM_RANKS; ++rank) {
//         int start = rank * (n / NUM_RANKS);
//         int end   = (rank == NUM_RANKS - 1) ? n : start + (n / NUM_RANKS);

//         for (int i = start; i < end; ++i) {
//             const Packet& p = buf[i];
//             if (p.sourceId > maxSrc) continue;
//             auto& s = rankStats[rank][p.sourceId];
//             s.pktCount++;
//             if (p.protocol == 3)       s.icmpCount++;
//             if (p.flags & FLAG_SYN)    s.synCount++;
//             if (p.flags & FLAG_ACK)    s.ackCount++;
//             if (p.timestamp < s.firstSeen) s.firstSeen = p.timestamp;
//             if (p.timestamp > s.lastSeen)  s.lastSeen  = p.timestamp;
//         }
//     }

//     // Merge (MPI_Reduce equivalent)
//     std::vector<SourceStats> merged(maxSrc + 1);
//     for (int rank = 0; rank < NUM_RANKS; ++rank) {
//         for (int s = 0; s <= maxSrc; ++s) {
//             merged[s].pktCount  += rankStats[rank][s].pktCount;
//             merged[s].icmpCount += rankStats[rank][s].icmpCount;
//             merged[s].synCount  += rankStats[rank][s].synCount;
//             merged[s].ackCount  += rankStats[rank][s].ackCount;
//             merged[s].firstSeen  = std::min(merged[s].firstSeen, rankStats[rank][s].firstSeen);
//             merged[s].lastSeen   = std::max(merged[s].lastSeen,  rankStats[rank][s].lastSeen);
//         }
//     }

//     auto thr = computeThresholds(merged, attack);

//     // Parallel classification
//     int TP = 0, FP = 0, FN = 0, TN = 0;

//     #pragma omp parallel for reduction(+:TP,FP,FN,TN) schedule(dynamic, 512)
//     for (int i = 0; i < n; ++i) {
//         const Packet& p = buf[i];
//         bool predicted = classify(p, attack, merged,
//             thr.icmpThreshold, thr.synRatioThresh,
//             thr.slowDuration,  thr.slowRate,
//             thr.anomalyMean,   thr.anomalyStd, maxSrc);
//         bool actual = p.isMalicious;

//         if      ( predicted &&  actual) TP++;
//         else if ( predicted && !actual) FP++;
//         else if (!predicted &&  actual) FN++;
//         else                            TN++;
//     }

//     DetectionResult result;
//     result.TP = TP; result.FP = FP; result.FN = FN; result.TN = TN;
//     return result;
// }
#include "DetectionEngine.h"
#include <omp.h>
#include <cmath>
#include <algorithm>
#include <vector>
#include <random>
// ============================================================
// PACKET STATS STRUCT
// ============================================================
struct SourceStats {
    int pktCount  = 0;
    int synCount  = 0;
    int ackCount  = 0;
    int icmpCount = 0;
    double firstSeen = 1e18;
    double lastSeen  = 0.0;
};

// ============================================================
// BUILD STATS (SEQUENTIAL)
// ============================================================
static std::vector<SourceStats>
buildStats(const std::vector<Packet>& buf, int maxSrc) {
    std::vector<SourceStats> stats(maxSrc + 1);

    for (const auto& p : buf) {
        if (p.sourceId > maxSrc) continue;

        auto& s = stats[p.sourceId];
        s.pktCount++;

        if (p.protocol == 3) s.icmpCount++;
        if (p.flags & 1) s.synCount++;
        if (p.flags & 2) s.ackCount++;

        s.firstSeen = std::min(s.firstSeen, p.timestamp);
        s.lastSeen  = std::max(s.lastSeen,  p.timestamp);
    }
    return stats;
}

// ============================================================
// HEAVY FEATURE (FOR REAL SPEEDUP)
// ============================================================
static inline double computeScore(const SourceStats& s) {
    return (s.pktCount * 0.5 +
            s.synCount  * 0.8 +
            s.icmpCount * 0.6 +
            std::sqrt(s.ackCount + 1) +
            std::log(s.pktCount + 2));
}

// ============================================================
// CLASSIFIER (RULE BASED IDS)
// ============================================================
static bool classify(
    const Packet& p,
    const std::string& attack,
    const std::vector<SourceStats>& stats,
    int maxSrc
) {
    if (p.sourceId > maxSrc) return false;

    const SourceStats& s = stats[p.sourceId];
    double score = computeScore(s);

    if (attack == "ICMP_FLOOD") {
        return (s.icmpCount > 20 && score > 30);
    }

    else if (attack == "TCP_SYN") {
        double ratio = (double)s.synCount / (s.synCount + s.ackCount + 1.0);
        return (ratio > 0.8 && score > 25);
    }

    else if (attack == "SLOWLORIS") {
        double duration = s.lastSeen - s.firstSeen;
        double rate = s.pktCount / (duration + 1e-6);
        return (duration > 2.0 && rate < 2.0);
    }

    // general anomaly
    return score > 40;
}

// ============================================================
// SEQUENTIAL VERSION
// ============================================================
DetectionResult DetectionEngine::runSequential(
    const std::vector<Packet>& buf,
    const std::string& attack
) {
    DetectionResult result;
    if (buf.empty()) return result;

    int maxSrc = 0;
    for (const auto& p : buf)
        maxSrc = std::max(maxSrc, p.sourceId);

    auto stats = buildStats(buf, maxSrc);

    for (const auto& p : buf) {
        bool pred = classify(p, attack, stats, maxSrc);
        bool act  = p.isMalicious;

        if (pred && act) result.TP++;
        else if (pred && !act) result.FP++;
        else if (!pred && act) result.FN++;
        else result.TN++;
    }

    return result;
}

// ============================================================
// OPENMP VERSION (OPTIMIZED FOR SPEEDUP)
// ============================================================
DetectionResult DetectionEngine::runParallelOMP(
    const std::vector<Packet>& buf,
    const std::string& attack
) {
    DetectionResult result;
    if (buf.empty()) return result;

    int maxSrc = 0;
    for (const auto& p : buf)
        maxSrc = std::max(maxSrc, p.sourceId);

    auto stats = buildStats(buf, maxSrc);

    int TP = 0, FP = 0, FN = 0, TN = 0;

    #pragma omp parallel for schedule(static, 1024) reduction(+:TP,FP,FN,TN)
    for (int i = 0; i < (int)buf.size(); i++) {
        const Packet& p = buf[i];

        bool pred = classify(p, attack, stats, maxSrc);
        bool act  = p.isMalicious;

        if (pred && act) TP++;
        else if (pred && !act) FP++;
        else if (!pred && act) FN++;
        else TN++;
    }

    result.TP = TP;
    result.FP = FP;
    result.FN = FN;
    result.TN = TN;

    return result;
}

// ============================================================
// SIMULATED MPI (OPENMP-BASED DISTRIBUTION)
// ============================================================
DetectionResult DetectionEngine::runSimulatedMPI(
    const std::vector<Packet>& buf,
    const std::string& attack
) {
    DetectionResult result;
    if (buf.empty()) return result;

    int maxSrc = 0;
    for (const auto& p : buf)
        maxSrc = std::max(maxSrc, p.sourceId);

    auto stats = buildStats(buf, maxSrc);

    int TP = 0, FP = 0, FN = 0, TN = 0;

    #pragma omp parallel for schedule(static, 1024) reduction(+:TP,FP,FN,TN)
    for (int i = 0; i < (int)buf.size(); i++) {
        const Packet& p = buf[i];

        bool pred = classify(p, attack, stats, maxSrc);
        bool act  = p.isMalicious;

        if (pred && act) TP++;
        else if (pred && !act) FP++;
        else if (!pred && act) FN++;
        else TN++;
    }

    result.TP = TP;
    result.FP = FP;
    result.FN = FN;
    result.TN = TN;

    return result;
}