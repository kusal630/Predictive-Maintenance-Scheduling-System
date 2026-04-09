"""
PMSS Run Simulator – starts the sensor simulator.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from simulator.sensor_simulator import run_simulator

if __name__ == "__main__":
    try:
        asyncio.run(run_simulator())
    except KeyboardInterrupt:
        print("\nSimulator stopped.")
