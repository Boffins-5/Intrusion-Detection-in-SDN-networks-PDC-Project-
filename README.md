# SDN Parallel Guard 🛡️

A real-time **Software Defined Network (SDN) intrusion detection system** that simulates network attacks and analyzes them using parallel computing techniques (OpenMP & MPI).

---

## 🗂️ Project Structure

```
MID_PDC_PROJECT/
├── frontend/
│   ├── main.py              ← App entry point
│   ├── attack_lab.py        ← Network topology + attack simulation
│   ├── performance_lab.py   ← HPC performance dashboard
│   ├── bridge.py            ← Python ↔ C++ communication
│   └── backend/
│       ├── main.cpp
│       ├── DetectionEngine.cpp / .h
│       ├── TrafficGenerator.cpp / .h
│       ├── Packet.h
│       ├── Timer.h
│       └── build.bat        ← Compile script
```

---

## ⚙️ Requirements

- Python 3.10+ with `PyQt6` and `matplotlib`
- g++ with OpenMP support (MinGW-w64 recommended on Windows)

Install Python dependencies:
```
pip install PyQt6 matplotlib
```

---

## 🚀 How to Run

**Step 1 — Build the C++ Backend**
```
Open the frontend/backend/ folder
Double-click build.bat
Wait for "engine.exe is ready" message
```

**Step 2 — Launch the Frontend**
```
cd frontend
python main.py
```

---

## 🎮 How to Use

1. On the **Attack Lab** screen, click any nodes on the canvas to mark them as targets (they turn red)
2. Choose your **Attack Type** (ICMP Flood, TCP SYN, Slowloris, Flow Overflow)
3. Adjust **packet count** and **animation duration** using the sliders
4. Click **⚡ Analyze** → confirm → watch the live packet animation
5. After animation ends, the C++ engine runs automatically
6. Results appear on the **📊 Performance** screen showing speedup and detection metrics

---

## 🔍 Supported Attack Types

| Attack | Detection Rule |
|--------|---------------|
| ICMP Flood | ICMP rate per source exceeds threshold |
| TCP SYN Flood | SYN / (SYN + ACK) ratio > 0.8 |
| Slowloris | Long session duration + very low packet rate |
| Flow Overflow | Statistical anomaly in packet count |
