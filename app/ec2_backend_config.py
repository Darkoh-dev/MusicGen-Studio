import os
from pathlib import Path

LOCAL_PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_OUTPUTS_DIR = LOCAL_PROJECT_ROOT / "outputs" / "wav"

EC2_SSH_USER = os.getenv("MUSICGEN_EC2_SSH_USER", "ubuntu")
EC2_KEY_PATH = os.getenv("MUSICGEN_EC2_KEY_PATH", "")
EC2_HOST = os.getenv("MUSICGEN_EC2_HOST", "")
EC2_PROJECT_ROOT = "/home/ubuntu/projects/MusicGen-Studio"
EC2_REMOTE_OUTPUT_DIR = f"{EC2_PROJECT_ROOT}/outputs/wav"
EC2_REMOTE_INPUT_AUDIO_DIR = f"{EC2_PROJECT_ROOT}/input_audio"

DEFAULT_REMOTE_PYTHON = f"{EC2_PROJECT_ROOT}/.venv/bin/python"
DEFAULT_REMOTE_GENERATE_MODULE = "app.generate"