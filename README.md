# MusicGen-Studio

## Project Overview
MusicGen-Studio is a Python-based AI music generation project built for AWS EC2 Linux instances with NVIDIA GPUs.

The local Windows machine is used only for coding and project editing.
The AWS EC2 Linux + NVIDIA GPU environment is the actual runtime and testing target.

This project does not rely on hosted music generation APIs.
The initial output target is WAV audio files only.

## Runtime Environment

This project is developed locally on a Windows machine, but Windows is only the editing environment.

The target runtime for this project is an AWS EC2 Linux instance with an NVIDIA GPU.

All implementation, dependency, and runtime decisions should favor:
- Linux execution
- NVIDIA GPU compatibility
- AWS EC2 as the real testing and inference environment

If there is any conflict between local Windows convenience and EC2 Linux runtime compatibility, EC2 Linux compatibility takes priority.

## Development Workflow

This project uses a hybrid workflow:

- code is written and organized locally
- GPU-heavy testing and inference are run on AWS EC2
- the EC2 instance is started only when needed
- the EC2 instance should be stopped after testing to control cost

This means the local machine is used for editing and project management, while the EC2 Linux environment is used for actual runtime validation.

## Prerequisites

Before running this project in the target environment, make sure you have:

- an EC2 Linux instance with an NVIDIA GPU
- SSH access to that instance
- Python 3.10
- `venv`
- `pip`
- `git`
- `ffmpeg`

You should also be able to verify the GPU environment with:
- `nvidia-smi`
- PyTorch CUDA detection

## Target Environment

Recommended target environment:

- Ubuntu 22.04 LTS
- AWS EC2 `g5.xlarge` or similar
- NVIDIA A10G GPU
- EBS-backed storage for models and outputs
- Python 3.10
- virtual environment created with `venv`

This project should be designed and tested for Linux + NVIDIA first, even if the code is being edited from a different local machine.

## EC2 Setup

On the EC2 Linux instance, install the base system packages first:

```bash
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3-pip git ffmpeg
```

Then create and activate a virtual environment in the project folder:
- python3.10 -m venv .venv
- source .venv/bin/activate
- pip install --upgrade pip

## PyTorch Installation Note

Install PyTorch on the EC2 Linux instance using the official Linux CUDA install command from the PyTorch website.

Do not assume the default install command is correct.

Before installing PyTorch, verify that:
- the command is for Linux
- the command matches Python 3.10
- the build includes CUDA support

After installation, confirm that:
- `torch.cuda.is_available()` returns `True`
- the NVIDIA GPU is detected correctly

## Project Dependency Installation

After PyTorch is installed correctly in the virtual environment, install the remaining project dependencies:

```bash
pip install -r requirements.txt
```

## GPU Verification

Before testing MusicGen, verify that the EC2 environment can see the NVIDIA GPU correctly.

System-level check:

```bash
nvidia-smi
```

PyTorch-level check:
- python scripts/check_gpu.py

## MusicGen Load Test

After GPU verification succeeds, run the first controlled model test:

```bash
python scripts/test_musicgen.py
```

This test is meant to confirm that:
- the processor loads correctly
- the MusicGen model loads correctly
- tensors can be created on the target CUDA device
- a basic generation call returns output without failing immediately

## First Generation Run

After the GPU and model checks pass, run the generator script:

```bash
python -m app.generate --prompt "uplifting melodic edm with warm synths and a driving rhythm" --duration 10
```

Expected result:
- the script prints the target model and device
- the script prints the prompt and duration
- the script saves a WAV file into outputs/wav/

## Local Windows UI

A local Windows UI is available for submitting generation jobs to the EC2 backend.

Run it from the project root with the local virtual environment active:

```powershell
python -m app.local_ui
```
The UI allows you to:
- enter a text prompt
- choose a model preset
- set the generation duration
- submit the job to EC2
- download the generated WAV file back to the local machine