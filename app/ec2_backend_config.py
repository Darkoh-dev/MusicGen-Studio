from pathlib import Path

LOCAL_PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_OUTPUTS_DIR = LOCAL_PROJECT_ROOT / "outputs" / "wav"

EC2_SSH_USER = "ubuntu"
EC2_KEY_PATH = r"C:\Users\ofcor\Documents\AWS\aws-gpu-music-key.pem"

EC2_HOST = "54.87.77.145"
EC2_PROJECT_ROOT = "/home/ubuntu/projects/MusicGen-Studio"
EC2_REMOTE_OUTPUT_DIR = f"{EC2_PROJECT_ROOT}/outputs/wav"

DEFAULT_REMOTE_PYTHON = f"{EC2_PROJECT_ROOT}/.venv/bin/python"
DEFAULT_REMOTE_GENERATE_MODULE = "app.generate"