import posixpath
import re
import shlex
import subprocess
from pathlib import Path
from typing import Optional

from app.ec2_backend_config import (
    DEFAULT_REMOTE_GENERATE_MODULE,
    DEFAULT_REMOTE_PYTHON,
    EC2_HOST,
    EC2_KEY_PATH,
    EC2_PROJECT_ROOT,
    EC2_REMOTE_INPUT_AUDIO_DIR,
    EC2_SSH_USER,
    LOCAL_OUTPUTS_DIR,
)


class EC2GenerationError(Exception):
    def __init__(self, message: str, stdout: str = "", stderr: str = "") -> None:
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr


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


def build_remote_generate_command(
        prompt: str,
        duration: int,
        model: str,
        input_audio_path: Optional[str] = None,
) -> str:
    command_parts = [
        shlex.quote(DEFAULT_REMOTE_PYTHON),
        "-m",
        shlex.quote(DEFAULT_REMOTE_GENERATE_MODULE),
        "--prompt",
        shlex.quote(prompt),
        "--duration",
        str(duration),
        "--model",
        shlex.quote(model),
    ]

    if input_audio_path:
        command_parts.extend(["--input-audio", shlex.quote(input_audio_path)])

    return f"cd {shlex.quote(EC2_PROJECT_ROOT)} && {' '.join(command_parts)}"


def extract_saved_wav_path(command_output: str) -> str:
    match = re.search(r"WAV file saved to: (.+\.wav)", command_output)
    if not match:
        raise EC2GenerationError(
            "Could not find generated WAV path in EC2 output.",
            stdout=command_output,
            stderr="",
        )
    return match.group(1).strip()


def build_remote_mkdir_command(remote_directory: str) -> str:
    return f"mkdir -p {shlex.quote(remote_directory)}"


def ensure_remote_input_audio_dir() -> None:
    ssh_command = build_ssh_command(build_remote_mkdir_command(EC2_REMOTE_INPUT_AUDIO_DIR))

    try:
        subprocess.run(
            ssh_command,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise EC2GenerationError(
            "Failed to prepare EC2 input audio directory.",
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
        ) from exc
    

def upload_input_audio_file(local_audio_path: str) -> str:
    local_path = Path(local_audio_path).expanduser()

    if not local_path.exists():
        raise EC2GenerationError(f"Input file not found: {local_path}")
    
    if not local_path.is_file():
        raise EC2GenerationError(f"Input audio path is not a file: {local_path}")
    
    ensure_remote_input_audio_dir()

    scp_command = [
        "scp",
        "-i",
        EC2_KEY_PATH,
        str(local_path),
        f"{EC2_SSH_USER}@{EC2_HOST}:{EC2_REMOTE_INPUT_AUDIO_DIR}/",
    ]

    try:
        subprocess.run(
            scp_command,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise EC2GenerationError(
            "Failed to upload input audio file to EC2.",
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
        ) from exc
    
    return posixpath.join(EC2_REMOTE_INPUT_AUDIO_DIR, local_path.name)


def run_remote_generation(
        prompt:str,
        duration: int,
        model: str,
        input_audio_path: Optional[str] = None,
) -> tuple[str, str]:
    remote_input_audio_path = None

    if input_audio_path:
        remote_input_audio_path = upload_input_audio_file(input_audio_path)

    remote_command = build_remote_generate_command(
        prompt,
        duration,
        model,
        remote_input_audio_path,
    )
    ssh_command = build_ssh_command(remote_command)

    try:
        result = subprocess.run(
            ssh_command,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise EC2GenerationError(
            "Remote generation command failed.",
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
        ) from exc
    
    saved_wav_path = extract_saved_wav_path(result.stdout)
    return result.stdout, saved_wav_path


def download_generated_file(remote_file_path: str) -> Path:
    LOCAL_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    scp_command = build_scp_command(remote_file_path, LOCAL_OUTPUTS_DIR)

    try:
        subprocess.run(
            scp_command,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise EC2GenerationError(
            "Failed to download generated WAV file from EC2.",
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
        ) from exc

    return LOCAL_OUTPUTS_DIR / Path(remote_file_path).name