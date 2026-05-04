import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

import torchaudio
from scipy.io.wavfile import write as write_wav_file
from transformers import AutoProcessor, MusicgenForConditionalGeneration

from app.config import (
    DEFAULT_DEVICE,
    DEFAULT_DURATION_SECONDS,
    DEFAULT_MODEL_KEY,
    DEFAULT_OUTPUT_FILENAME_PREFIX,
    DEFAULT_OUTPUT_FORMAT,
    DEFAULT_PROMPT,
    DEFAULT_SAMPLE_RATE,
    HF_CACHE_DIR,
    MAX_DURATION_SECONDS,
    MIN_DURATION_SECONDS,
    MODEL_PRESETS,
    REQUIRED_DIRECTORIES,
    SUPPORTED_MODEL_KEYS,
    WAV_OUTPUT_DIR,
)
from app.prompt_logger import log_generation


def ensure_required_directories() -> None:
    for directory in REQUIRED_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)


def build_output_path() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{DEFAULT_OUTPUT_FILENAME_PREFIX}_{timestamp}.{DEFAULT_OUTPUT_FORMAT}"
    return str(WAV_OUTPUT_DIR / filename)


def validate_duration(duration_seconds: int) -> int:
    if duration_seconds < MIN_DURATION_SECONDS or duration_seconds > MAX_DURATION_SECONDS:
        raise ValueError(
            f"Duration must be between {MIN_DURATION_SECONDS} and {MAX_DURATION_SECONDS} seconds."
        )
    return duration_seconds


def validate_model_key(model_key: str) -> str:
    if model_key not in MODEL_PRESETS:
        raise ValueError(f"Model key must be one of: {', '.join(SUPPORTED_MODEL_KEYS)}")
    return model_key


def build_generation_kwargs(duration_seconds: int) -> Dict[str, int]:
    return {
        "max_new_tokens": duration_seconds * 50,
    }


def validate_input_audio_path(input_audio: Optional[str]) -> Optional[Path]:
    if not input_audio:
        return None
    
    audio_path = Path(input_audio).expanduser()
    if not audio_path.exists():
        raise FileNotFoundError(f"Input audio file not found: {audio_path}")
    
    if not audio_path.is_file():
        raise ValueError(f"Input audio is not a file: {audio_path}")
    
    return audio_path


def load_audio_guidance(input_audio_path: Path) -> Tuple[object, int]:
    waveform, sample_rate = torchaudio.load(str(input_audio_path))

    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    if sample_rate != DEFAULT_SAMPLE_RATE:
        waveform = torchaudio.functional.resample(
            waveform,
            orig_freq=sample_rate,
            new_freq=DEFAULT_SAMPLE_RATE,
        )
        sample_rate = DEFAULT_SAMPLE_RATE

    audio_array = waveform.squeeze(0).numpy().astype("float32")
    return audio_array, sample_rate


def load_model_and_processor(model_name: str):
    processor = AutoProcessor.from_pretrained(
        model_name,
        cache_dir=HF_CACHE_DIR,
    )
    model = MusicgenForConditionalGeneration.from_pretrained(
        model_name,
        cache_dir=HF_CACHE_DIR,
    )
    model = model.to(DEFAULT_DEVICE)
    return processor, model


def generate_from_text(
        prompt: str,
        duration_seconds: int,
        model_key: str,
        input_audio: Optional[str] = None,
) -> Tuple[object, str, str, str, Optional[str]]:
    validated_duration = validate_duration(duration_seconds)
    validated_model_key = validate_model_key(model_key)
    input_audio_path = validate_input_audio_path(input_audio)
    model_name = MODEL_PRESETS[validated_model_key]

    processor, model = load_model_and_processor(model_name)

    if input_audio_path:
        audio_array, sample_rate = load_audio_guidance(input_audio_path)
        inputs = processor(
            text=[prompt],
            audio=audio_array,
            sampling_rate=sample_rate,
            padding=True,
            return_tensors="pt",
        )
    else:
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
    input_audio_display = str(input_audio_path) if input_audio_path else None
    return audio_values, output_path, model_name, validated_model_key, input_audio_display


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
        help=f"Requested generation duration in seconds ({MIN_DURATION_SECONDS}-{MAX_DURATION_SECONDS}).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL_KEY,
        choices=SUPPORTED_MODEL_KEYS,
        help="Model preset to use.",
    )
    parser.add_argument(
        "--input-audio",
        type=str,
        default=None,
        help="Optional reference audio file for melody-guided generation.",
    )
    return parser.parse_args()


def print_generation_summary(
        model_name: str,
        prompt: str,
        duration_seconds: int,
        output_path: str,
        audio_values,
        input_audio: Optional[str] = None,
    ) -> None:
        print(f"Target model: {model_name}")
        print(f"Target device: {DEFAULT_DEVICE}")
        print(f"Prompt: {prompt}")
        print(f"Duration: {duration_seconds} seconds")
        print(f"Input audio: {input_audio or 'None'}")
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
    audio_values, output_path, model_name, model_preset, input_audio = generate_from_text(
        args.prompt,
        args.duration,
        args.model,
        args.input_audio,
    )
    print_generation_summary(model_name, args.prompt, args.duration, output_path, audio_values, input_audio)
    save_audio_to_wav(audio_values, output_path)

    log_generation(
        model_preset=model_preset,
        model_name=model_name,
        prompt=args.prompt,
        duration_seconds=args.duration,
        output_file=output_path,
        notes=f"Generated from CLI workflow. Input audio: {input_audio or 'None'}",
    )

    print(f"WAV file saved to: {output_path}")


if __name__ == "__main__":
    main()
