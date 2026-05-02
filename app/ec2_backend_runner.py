import re
import subprocess
from pathlib import Path

from app.ec2_backend_config import (
    DEFAULT_REMOTE_GENERATE_MODULE,
    DEFAULT_REMOTE_PYTHON,
    EC2_HOST,
    EC2_KEY_PATH,
    EC2_PROJECT_ROOT,
    EC2_SSH_USER,
    LOCAL_OUTPUTS_DIR,
)


def build_ssh_command(remote_command: str) -> list[str]:
    return [
        "ssh",
        "-i",
        EC2_KEY_PATH,
        f"{EC2_SSH_USER}@{EC2_HOST}",
        remote_command,
    ]


def build_scp_command(remote_file_path: str, local_directory: Path) -> list[str]:
    return [
        "scp",
        "-i",
        EC2_KEY_PATH,
        f"{EC2_SSH_USER}@{EC2_HOST}:{remote_file_path}",
        str(local_directory),
    ]


def build_remote_generate_command(prompt: str, duration: int, model: str) -> str:
    escaped_prompt = prompt.replace('"', '\\"')
    return (
        f"cd {EC2_PROJECT_ROOT} && "
        f"{DEFAULT_REMOTE_PYTHON} -m {DEFAULT_REMOTE_GENERATE_MODULE} "
        f'--prompt "{escaped_prompt}" --duration {duration} --model {model}'
    )


def extract_saved_wav_path(command_output: str) -> str:
    match = re.search(r"WAV file saved to: (.+\\.wav)", command_output)
    if not match:
        raise ValueError("Could not find generated WAV path in EC2 output.")
    return match.group(1).strip()


def run_remote_generation(prompt: str, duration: int, model: str) -> tuple[str, str]:
    remote_command = build_remote_generate_command(prompt, duration, model)
    ssh_command = build_ssh_command(remote_command)

    result = subprocess.run(
        ssh_command,
        capture_output=True,
        text=True,
        check=True,
    )

    saved_wav_path = extract_saved_wav_path(result.stdout)
    return result.stdout, saved_wav_path


def download_generated_file(remote_file_path: str) -> Path:
    LOCAL_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    scp_command = build_scp_command(remote_file_path, LOCAL_OUTPUTS_DIR)

    subprocess.run(
        scp_command,
        capture_output=True,
        text=True,
        check=True,
    )

    return LOCAL_OUTPUTS_DIR / Path(remote_file_path).name