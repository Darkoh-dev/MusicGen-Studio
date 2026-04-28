import argparse

from datetime import datetime
from typing import Dict, Tuple

from scipy.io.wavfile import write as write_wav_file
from transformers import AutoProcessor, MusicgenForConditionalGeneration

from app.config import (
    DEFAULT_DEVICE,
    DEFAULT_DURATION_SECONDS,
    DEFAULT_MODEL_NAME,
    DEFAULT_OUTPUT_FILENAME_PREFIX,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_OUTPUT_FORMAT,
    HF_CACHE_DIR,
    REQUIRED_DIRECTORIES,
    WAV_OUTPUT_DIR,
)

DEFAULT_PROMPT = "uplifting melodic edm with warm synths and a driving rhythm"


def ensure_required_directories() -> None:
    for directory in REQUIRED_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)


def build_output_path() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{DEFAULT_OUTPUT_FILENAME_PREFIX}_{timestamp}.{DEFAULT_OUTPUT_FORMAT}"
    return str(WAV_OUTPUT_DIR / filename)


def validate_duration(duration_seconds: int) -> int:
    if duration_seconds <= 0:
        raise ValueError("Duration must be greater than 0 seconds.")
    return duration_seconds


def build_generation_kwargs(duration_seconds: int) -> Dict[str, int]:
    return {
        "max_new_tokens": duration_seconds * 50,
    }


def load_model_and_processor():
    processor = AutoProcessor.from_pretrained(
        DEFAULT_MODEL_NAME,
        cache_dir=HF_CACHE_DIR,
    )
    model = MusicgenForConditionalGeneration.from_pretrained(
        DEFAULT_MODEL_NAME,
        cache_dir=HF_CACHE_DIR,
    )
    model = model.to(DEFAULT_DEVICE)
    return processor, model


def generate_from_text(prompt: str, duration_seconds: int) -> Tuple[object, str]:
    validated_duration = validate_duration(duration_seconds)
    processor, model = load_model_and_processor()
    inputs = processor(
        text=[prompt],
        padding=True,
        return_tensors="pt",
    )
    inputs = {key: value.to(DEFAULT_DEVICE) for key, value in inputs.items()}
    generation_kwargs = build_generation_kwargs(validated_duration)
    audio_values = model.generate(
        **inputs,
        **generation_kwargs,
    )
    output_path = build_output_path()
    return audio_values, output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate music from a text prompt.")
    parser.add_argument(
        "--prompt",
        type=str,
        default=DEFAULT_PROMPT,
        help="Text prompt for music generation.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION_SECONDS,
        help="Requested generation duration in seconds.",
    )
    return parser.parse_args()


def print_generation_summary(prompt: str, duration_seconds: int, output_path: str, audio_values) -> None:
    print(f"Target model: {DEFAULT_MODEL_NAME}")
    print(f"Target device: {DEFAULT_DEVICE}")
    print(f"Prompt: {prompt}")
    print(f"Duration: {duration_seconds} seconds")
    print(f"Planned output path: {output_path}")
    print(f"Target sample rate: {DEFAULT_SAMPLE_RATE}")
    print(f"Generated tensor shape: {tuple(audio_values.shape)}")


def extract_audio_array(audio_values):
    audio_tensor = audio_values[0, 0].detach().cpu()
    audio_array = audio_tensor.numpy().astype("float32")
    return audio_array


def save_audio_to_wav(audio_values, output_path: str) -> None:
    audio_array = extract_audio_array(audio_values)
    write_wav_file(output_path, rate=DEFAULT_SAMPLE_RATE, data=audio_array)


def main() -> None:
    ensure_required_directories()
    args = parse_args()
    audio_values, output_path = generate_from_text(args.prompt, args.duration)
    print_generation_summary(args.prompt, args.duration, output_path, audio_values)
    save_audio_to_wav(audio_values, output_path)
    print(f"WAV file saved to: {output_path}")

if __name__ == "__main__":
    main()