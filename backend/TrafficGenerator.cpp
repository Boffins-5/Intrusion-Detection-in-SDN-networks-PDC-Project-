#include "TrafficGenerator.h"
#include <cstdlib>
#include <ctime>
#include <vector>
#include <algorithm>
#include <random>

std::vector<Packet> TrafficGenerator::generate(
    int nodes,
    std::vector<int> targets,
    const std::string& attack,
    int count
) {
    std::vector<Packet> buffer;
    buffer.reserve(count);

    std::srand((unsigned)std::time(nullptr));

    int attackCount  = (int)(count * 0.40);
    int normalCount  = count - attackCount;

    int icmpCount = attackCount / 3;
    int synCount  = attackCount / 3;
    int slowCount = attackCount - icmpCount - synCount;

    double timestamp = 0.0;

    // =========================================================
    // 1. NORMAL TRAFFIC (GUARANTEED CLEAN DATA)
    // =========================================================
    for (int i = 0; i < normalCount; i++) {
        Packet p;

        p.sourceId = std::rand() % nodes;
        p.targetId = std::rand() % nodes;

        p.isMalicious = false;
        p.timestamp = timestamp += 0.001;

        p.protocol = 1;
        p.flags = (std::rand() % 2) ? FLAG_ACK : FLAG_SYN;
        p.size = 100 + std::rand() % 400;
        p.payload = "NORMAL";

        buffer.push_back(p);
    }

    // =========================================================
    // 2. ICMP FLOOD ATTACK
    // =========================================================
    for (int i = 0; i < icmpCount; i++) {
        Packet p;

        p.sourceId = std::rand() % nodes;
        p.targetId = targets[rand() % targets.size()];

        p.isMalicious = true;
        p.timestamp = timestamp += 0.0005; // faster burst

        p.protocol = 3;
        p.flags = 0;
        p.size = 64;
        p.payload = "ICMP_FLOOD";

        buffer.push_back(p);
    }

    // =========================================================
    // 3. TCP SYN FLOOD ATTACK
    // =========================================================
    for (int i = 0; i < synCount; i++) {
        Packet p;

        p.sourceId = std::rand() % nodes;
        p.targetId = targets[rand() % targets.size()];

        p.isMalicious = true;
        p.timestamp = timestamp += 0.0005;

        p.protocol = 1;
        p.flags = FLAG_SYN;   // half-open attack
        p.size = 60;
        p.payload = "SYN_FLOOD";

        buffer.push_back(p);
    }

    // =========================================================
    // 4. SLOWLORIS ATTACK
    // =========================================================
    for (int i = 0; i < slowCount; i++) {
        Packet p;

        p.sourceId = std::rand() % nodes;
        p.targetId = targets[rand() % targets.size()];

        p.isMalicious = true;

        // slow but continuous timeline (IMPORTANT FIX)
        timestamp += 0.05;
        p.timestamp = timestamp;

        p.protocol = 0;
        p.flags = FLAG_SYN;
        p.size = 512;
        p.payload = "SLOWLORIS";

        buffer.push_back(p);
    }

    // =========================================================
    // FINAL SHUFFLE (VERY IMPORTANT)
    // =========================================================
    std::random_device rd;
std::mt19937 g(rd());

std::shuffle(buffer.begin(), buffer.end(), g);


    return buffer;
}