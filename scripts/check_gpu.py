import platform

import torch



def main() -> None:
    print("MusicGen-Studio GPU Environment Check")
    print(f"Platform: {platform.platform()}")
    print(f"Python CUDA available: {torch.cuda.is_available()}")
    print(f"PyTorch version: {torch.__version__}")

    if torch.cuda.is_available():
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"Current CUDA device: {torch.cuda.current_device()}")
        print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
    else:
        print("No CUDA-enabled GPU detected.")

if __name__ == "__main__":
    main()