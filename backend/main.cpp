#include <iostream>
#include <vector>
#include <string>
#include <sstream>

#include "TrafficGenerator.h"
#include "DetectionEngine.h"
#include "Timer.h"

int main(int argc, char* argv[]) {

    // ── Default config ──
    int         nodes   = 10;
    int         packets = 100000;
    std::string attack  = "ICMP_FLOOD";
    std::vector<int> targets;

    // ── Argument parsing ──
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];

        if (arg == "--nodes"   && i + 1 < argc) nodes   = std::stoi(argv[++i]);
        if (arg == "--packets" && i + 1 < argc) packets = std::stoi(argv[++i]);
        if (arg == "--attack"  && i + 1 < argc) attack  = argv[++i];

        if (arg == "--target"  && i + 1 < argc) {
            std::stringstream ss(argv[++i]);
            std::string item;
            while (std::getline(ss, item, ','))
                targets.push_back(std::stoi(item));
        }
    }

    // ── Traffic generation ──
    auto buffer = TrafficGenerator::generate(nodes, targets, attack, packets);

    // ── Sequential ──
    Timer seqTimer;
    seqTimer.start();
    DetectionResult resSeq = DetectionEngine::runSequential(buffer, attack);
    double t_seq = seqTimer.stop();

    // ── OpenMP ──
    Timer ompTimer;
    ompTimer.start();
    DetectionResult resOmp = DetectionEngine::runParallelOMP(buffer, attack);
    double t_omp = ompTimer.stop();

    // ── Simulated MPI ──
    Timer mpiTimer;
    mpiTimer.start();
    DetectionResult resMpi = DetectionEngine::runSimulatedMPI(buffer, attack);
    double t_mpi = mpiTimer.stop();

    // ── Metrics (from sequential run — ground truth) ──
    int total    = resSeq.TP + resSeq.FP + resSeq.FN + resSeq.TN;
    double accuracy = total > 0
        ? (double)(resSeq.TP + resSeq.TN) / total
        : 0.0;

    // ── Output (CSV for Python bridge) ──
    // Format: seq, omp, mpi, total, TP, FP, FN, accuracy, attack
    std::cout
        << t_seq     << ","
        << t_omp     << ","
        << t_mpi     << ","
        << total     << ","
        << resSeq.TP << ","
        << resSeq.FP << ","
        << resSeq.FN << ","
        << accuracy  << ","
        << attack
        << std::endl;

    return 0;
}
