"""
PHANTOM  --  Main Entry Point
==============================
Proactive Hybrid Anomaly & Threat Management Operations Network

Usage:
  1. First time: python main.py --train    (pretrains models)
  2. Run demo:   python main.py            (launches dashboard)
  3. Direct:     streamlit run dashboard/dashboard.py

Enhancements over base spec:
   Pretrained Models  --  No training during demo
   Identity-Based Tracking  --  User + session, not just IP
   Multi-Network Awareness  --  Cross-zone lateral movement detection
"""

import os
import sys
import subprocess

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)


def print_banner():
    print("""
    ==============================================================
    |                                                              |
    |     PPPP  H   H  AAA  N   N TTTTT  OOO  M   M               |
    |     P   P H   H A   A NN  N   T   O   O MM MM               |
    |     PPPP  HHHHH AAAAA N N N   T   O   O M M M               |
    |     P     H   H A   A N  NN   T   O   O M   M               |
    |     P     H   H A   A N   N   T    OOO  M   M               |
    |                                                              |
    |  Proactive Hybrid Anomaly & Threat Management Operations     |
    |  Network -- Hack Malenadu '26                                |
    |                                                              |
    |  >> Pretrained Models (no training during demo)              |
    |  >> Identity-Based Tracking (user + session, not just IP)    |
    |  >> Multi-Network Awareness (cross-zone detection)           |
    |                                                              |
    ==============================================================
    """)


def check_models_exist() -> bool:
    """Check if pretrained models are available."""
    models_dir = os.path.join(ROOT_DIR, "models")
    required = ["ae_network.pt", "ae_application.pt", "ae_endpoint.pt",
                 "scaler.pkl", "thresholds.json"]
    return all(os.path.exists(os.path.join(models_dir, f)) for f in required)


def train_models():
    """Run the pretraining pipeline."""
    print("\n[PHANTOM] Pretraining specialist guards...")
    print("[PHANTOM] This trains on synthetic benign data  --  run once, demo forever.\n")

    from models.train_autoencoders import train_all
    train_all()


def launch_dashboard():
    """Launch the Streamlit SOC dashboard."""
    print("\n[PHANTOM] Launching SOC Dashboard...")
    print("[PHANTOM] Dashboard URL: http://localhost:8501\n")

    dashboard_path = os.path.join(ROOT_DIR, "dashboard", "dashboard.py")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        dashboard_path,
        "--server.headless", "true",
        "--server.port", "8501",
        "--theme.base", "dark",
        "--theme.primaryColor", "#ff1744",
        "--theme.backgroundColor", "#0a0e17",
        "--theme.secondaryBackgroundColor", "#161b22",
        "--theme.textColor", "#e0e0e0",
    ])


def main():
    print_banner()

    # Parse args
    args = sys.argv[1:]

    if "--train" in args:
        train_models()
        print("\n[PHANTOM]  Models pretrained. Run `python main.py` to launch dashboard.")
        return

    if "--help" in args or "-h" in args:
        print("Usage:")
        print("  python main.py --train    Pretrain models (run once)")
        print("  python main.py            Launch SOC dashboard")
        print("  python main.py --help     Show this help")
        return

    # Check if models exist
    if not check_models_exist():
        print("[PHANTOM]   Pretrained models not found!")
        print("[PHANTOM] Running pretraining first (this takes ~30 seconds)...\n")
        train_models()

    # Launch dashboard
    launch_dashboard()


if __name__ == "__main__":
    main()
