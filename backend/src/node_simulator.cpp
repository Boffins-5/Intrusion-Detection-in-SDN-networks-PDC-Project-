#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "../include/structs.h"

// ─────────────────────────────────────────
//  GLOBAL NETWORK
// ─────────────────────────────────────────

Node network[MAX_NODES];
int  node_count = 0;

// ─────────────────────────────────────────
//  CREATE ONE NODE
// ─────────────────────────────────────────

Node create_node(int id, const char* ip, const char* mac, NodeType type) {
    Node n;
    n.id               = id;
    n.type             = type;
    n.status           = STATUS_NORMAL;
    n.connection_count = 0;
    n.packets_received = 0;
    n.packets_sent     = 0;
    n.current_load     = 0.0f;

    strncpy(n.ip,  ip,  15);
    strncpy(n.mac, mac, 17);

    // zero out connections
    for (int i = 0; i < 10; i++)
        n.connections[i] = -1;

    return n;
}

// ─────────────────────────────────────────
//  CONNECT TWO NODES
// ─────────────────────────────────────────

void connect_nodes(int id_a, int id_b) {
    // add b to a's connections
    if (network[id_a].connection_count < 10) {
        network[id_a].connections[network[id_a].connection_count] = id_b;
        network[id_a].connection_count++;
    }
    // add a to b's connections
    if (network[id_b].connection_count < 10) {
        network[id_b].connections[network[id_b].connection_count] = id_a;
        network[id_b].connection_count++;
    }
}

// ─────────────────────────────────────────
//  BUILD TOPOLOGY
//  Structure:
//  1 Controller → 3 Switches → 5 Hosts each
//  Total: 1 + 3 + 15 = 19 nodes
// ─────────────────────────────────────────

void build_topology() {
    node_count = 0;

    // ── Controller (node 0) ──
    network[0] = create_node(0,
        "192.168.0.1",
        "AA:BB:CC:00:00:01",
        NODE_CONTROLLER);
    node_count++;

    // ── 3 Switches (nodes 1, 2, 3) ──
    char ip[16], mac[18];

    for (int s = 1; s <= 3; s++) {
        sprintf(ip,  "192.168.%d.1", s);
        sprintf(mac, "AA:BB:CC:00:0%d:01", s);
        network[s] = create_node(s, ip, mac, NODE_SWITCH);
        node_count++;
        // connect switch to controller
        connect_nodes(0, s);
    }

    // ── 5 Hosts per Switch (nodes 4-18) ──
    int node_id = 4;
    for (int s = 1; s <= 3; s++) {
        for (int h = 1; h <= 5; h++) {
            sprintf(ip,  "192.168.%d.%d", s, h + 1);
            sprintf(mac, "AA:BB:CC:0%d:00:%02d", s, h);
            network[node_id] = create_node(
                node_id, ip, mac, NODE_HOST
            );
            node_count++;
            // connect host to its switch
            connect_nodes(s, node_id);
            node_id++;
        }
    }
}

// ─────────────────────────────────────────
//  SET NODE STATUS
// ─────────────────────────────────────────

void set_node_status(int node_id, NodeStatus status) {
    if (node_id >= 0 && node_id < node_count)
        network[node_id].status = status;
}

// ─────────────────────────────────────────
//  GET NODE TYPE STRING
// ─────────────────────────────────────────

const char* node_type_str(NodeType t) {
    switch(t) {
        case NODE_HOST:       return "HOST";
        case NODE_SWITCH:     return "SWITCH";
        case NODE_CONTROLLER: return "CONTROLLER";
        default:              return "UNKNOWN";
    }
}

// ─────────────────────────────────────────
//  GET NODE STATUS STRING
// ─────────────────────────────────────────

const char* node_status_str(NodeStatus s) {
    switch(s) {
        case STATUS_NORMAL:       return "NORMAL";
        case STATUS_UNDER_ATTACK: return "UNDER_ATTACK";
        case STATUS_COMPROMISED:  return "COMPROMISED";
        default:                  return "UNKNOWN";
    }
}

// ─────────────────────────────────────────
//  OUTPUT TOPOLOGY AS JSON
//  Python reads this to draw the map
// ─────────────────────────────────────────

void output_topology_json() {
    printf("{\n");
    printf("  \"node_count\": %d,\n", node_count);
    printf("  \"nodes\": [\n");

    for (int i = 0; i < node_count; i++) {
        Node* n = &network[i];
        printf("    {\n");
        printf("      \"id\": %d,\n",            n->id);
        printf("      \"ip\": \"%s\",\n",         n->ip);
        printf("      \"mac\": \"%s\",\n",        n->mac);
        printf("      \"type\": \"%s\",\n",       node_type_str(n->type));
        printf("      \"status\": \"%s\",\n",     node_status_str(n->status));
        printf("      \"load\": %.2f,\n",         n->current_load);
        printf("      \"connections\": [");

        for (int c = 0; c < n->connection_count; c++) {
            printf("%d", n->connections[c]);
            if (c < n->connection_count - 1)
                printf(", ");
        }
        printf("]\n");
        printf("    }");
        if (i < node_count - 1) printf(",");
        printf("\n");
    }

    printf("  ]\n");
    printf("}\n");
}

// ─────────────────────────────────────────
//  PRINT TOPOLOGY (for debugging)
// ─────────────────────────────────────────

void print_topology() {
    fprintf(stderr, "\n=== NETWORK TOPOLOGY ===\n");
    fprintf(stderr, "Total nodes: %d\n\n", node_count);
    for (int i = 0; i < node_count; i++) {
        Node* n = &network[i];
        fprintf(stderr, "[%02d] %-12s  IP: %-15s  Type: %-12s  Status: %s\n",
            n->id, n->mac, n->ip,
            node_type_str(n->type),
            node_status_str(n->status));
    }
    fprintf(stderr, "========================\n\n");
}

// ─────────────────────────────────────────
//  MAIN
// ─────────────────────────────────────────

int main() {
    build_topology();
    print_topology();       // prints to stderr (debug)
    output_topology_json(); // prints to stdout (Python reads this)
    return 0;
}