#ifndef STRUCTS_H
#define STRUCTS_H

#include <stdint.h>
#include <stdbool.h>

// ─────────────────────────────────────────
//  ENUMS
// ─────────────────────────────────────────

typedef enum {
    PROTOCOL_TCP  = 0,
    PROTOCOL_UDP  = 1,
    PROTOCOL_ICMP = 2,
    PROTOCOL_HTTP = 3
} Protocol;

typedef enum {
    NODE_HOST       = 0,
    NODE_SWITCH     = 1,
    NODE_CONTROLLER = 2
} NodeType;

typedef enum {
    STATUS_NORMAL      = 0,
    STATUS_UNDER_ATTACK = 1,
    STATUS_COMPROMISED = 2
} NodeStatus;

typedef enum {
    ATTACK_SYN_FLOOD  = 0,
    ATTACK_UDP_FLOOD  = 1,
    ATTACK_ICMP_FLOOD = 2,
    ATTACK_HTTP_FLOOD = 3
} AttackType;

typedef enum {
    SEVERITY_LOW      = 0,
    SEVERITY_MEDIUM   = 1,
    SEVERITY_HIGH     = 2,
    SEVERITY_CRITICAL = 3
} Severity;

// ─────────────────────────────────────────
//  PACKET STRUCT
//  Represents one network packet
// ─────────────────────────────────────────

typedef struct {
    char     src_ip[16];       // source IP e.g "192.168.1.1"
    char     dst_ip[16];       // destination IP
    uint16_t src_port;         // source port 0-65535
    uint16_t dst_port;         // destination port 0-65535
    Protocol protocol;         // TCP, UDP, ICMP, HTTP
    uint16_t size;             // packet size in bytes (64-1500)
    double   timestamp;        // seconds since simulation start
    bool     is_attack;        // ground truth — is this an attack packet?
    float    rate;             // packets/sec from this source IP
    int      src_node_id;      // which node sent this packet
    int      dst_node_id;      // which node receives this packet
} Packet;

// ─────────────────────────────────────────
//  NODE STRUCT
//  Represents one virtual network device
// ─────────────────────────────────────────

typedef struct {
    int        id;                    // unique node ID
    char       ip[16];                // IP address
    char       mac[18];               // MAC address e.g "AA:BB:CC:DD:EE:FF"
    NodeType   type;                  // HOST, SWITCH, CONTROLLER
    NodeStatus status;                // NORMAL, UNDER_ATTACK, COMPROMISED
    int        connections[10];       // IDs of connected nodes
    int        connection_count;      // how many connections
    int        packets_received;      // total packets received
    int        packets_sent;          // total packets sent
    float      current_load;          // current traffic load 0.0-1.0
} Node;

// ─────────────────────────────────────────
//  FLOW TABLE ENTRY
//  SDN controller routing rules
// ─────────────────────────────────────────

typedef struct {
    char     src_ip[16];      // match source IP
    char     dst_ip[16];      // match destination IP
    uint16_t dst_port;        // match destination port
    int      action;          // 0=forward, 1=drop, 2=alert
    int      forward_to;      // node ID to forward to
    int      priority;        // rule priority (higher = checked first)
} FlowEntry;

// ─────────────────────────────────────────
//  ATTACK EVENT
//  One detected attack record
// ─────────────────────────────────────────

typedef struct {
    double     time_sec;          // when attack was detected
    AttackType attack_type;       // SYN, UDP, ICMP, HTTP
    char       src_ip[16];        // attacker IP
    char       target_ip[16];     // victim IP
    Severity   severity;          // LOW, MEDIUM, HIGH, CRITICAL
    int        packets_count;     // how many attack packets
    int        target_node_id;    // which node is under attack
} AttackEvent;

// ─────────────────────────────────────────
//  SIM RESULT
//  Output of each detection method
// ─────────────────────────────────────────

typedef struct {
    double time_ms;            // execution time in milliseconds
    int    detected;           // true positives
    int    false_positives;    // false alarms
    int    false_negatives;    // missed attacks
    int    total_packets;      // total packets scanned
    double speedup;            // vs sequential baseline
    double efficiency;         // speedup / number of cores
    double throughput;         // packets per second
    int    cores_used;         // threads or processes used
} SimResult;

// ─────────────────────────────────────────
//  SIMULATION CONFIG
//  Settings chosen by user in GUI
// ─────────────────────────────────────────

typedef struct {
    int        total_packets;      // how many packets to generate
    float      attack_ratio;       // 0.0 to 1.0 (e.g 0.3 = 30% attack)
    AttackType attack_type;        // which attack to simulate
    int        num_nodes;          // how many network nodes
    int        openmp_threads;     // threads for OpenMP
    int        mpi_processes;      // processes for MPI
    int        seed;               // random seed for reproducibility
} SimConfig;

// ─────────────────────────────────────────
//  CONSTANTS
// ─────────────────────────────────────────

#define MAX_PACKETS     1000000    // maximum packets in simulation
#define MAX_NODES       50         // maximum network nodes
#define MAX_FLOW_RULES  100        // maximum SDN flow table entries
#define MAX_EVENTS      10000      // maximum attack events recorded

#endif // STRUCTS_H