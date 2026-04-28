import subprocess
import os
from PyQt6.QtCore import QThread, pyqtSignal


class BackendWorker(QThread):

    result_ready   = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, nodes, target, packets, attack, mode):
        super().__init__()
        self.nodes   = nodes
        self.target  = target
        self.packets = packets
        self.attack  = attack
        self.mode    = mode

    def run(self):

        # Convert target list → "1,2,3"
        if isinstance(self.target, list):
            target_arg = ",".join(map(str, self.target))
        else:
            target_arg = str(self.target)

        # Search for engine.exe in several likely locations
        base = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(base, "backend", "engine.exe"),   # frontend/backend/
            os.path.join(base, "engine.exe"),               # frontend/
            os.path.join(os.getcwd(), "backend", "engine.exe"),
            os.path.join(os.getcwd(), "engine.exe"),
        ]

        engine_path = next((p for p in candidates if os.path.exists(p)), None)

        if engine_path is None:
            self.error_occurred.emit(
                "engine.exe not found. Searched in:\n"
                + "\n".join(candidates)
                + "\n\nRun build.bat inside your backend/ folder first."
            )
            return

        print(f"[Bridge] Using engine: {engine_path}")

        cmd = [
            engine_path,
            "--nodes",   str(self.nodes),
            "--target",  target_arg,
            "--packets", str(self.packets),
            "--attack",  self.attack,
        ]

        try:
            print("[Bridge] CMD:", " ".join(cmd))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=120
            )

            raw = result.stdout.strip()
            print("[Bridge] RAW OUTPUT:", raw)

            if not raw:
                self.error_occurred.emit("Empty output from backend engine")
                return

            parts = raw.split(",")

            # Expected format:
            # seq, omp, mpi, total, TP, FP, FN, accuracy, attack
            if len(parts) < 9:
                self.error_occurred.emit(
                    f"Unexpected backend output format:\n{raw}"
                )
                return

            data = {
                "seq"     : float(parts[0]),
                "omp"     : float(parts[1]),
                "mpi"     : float(parts[2]),
                "total"   : int(parts[3]),
                "tp"      : int(parts[4]),
                "fp"      : int(parts[5]),
                "fn"      : int(parts[6]),
                "accuracy": float(parts[7]),
                "type"    : parts[8].strip(),
            }

            self.result_ready.emit(data)

        except subprocess.TimeoutExpired:
            self.error_occurred.emit("Backend engine timed out (>120 sec)")

        except subprocess.CalledProcessError as e:
            err = e.stderr.strip() if e.stderr else "C++ engine returned non-zero exit code"
            self.error_occurred.emit(err)

        except ValueError as e:
            self.error_occurred.emit(f"Failed to parse backend output:\n{raw}\n\n{e}")

        except Exception as e:
            self.error_occurred.emit(str(e))