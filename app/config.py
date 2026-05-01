from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
WAV_OUTPUT_DIR = OUTPUTS_DIR / "wav"
MP3_OUTPUT_DIR = OUTPUTS_DIR / "mp3"
INPUT_AUDIO_DIR = PROJECT_ROOT / "input_audio"

MODEL_PRESETS = {
    "small": "facebook/musicgen-small",
    "medium": "facebook/musicgen-medium",
    "melody": "facebook/musicgen-melody",
}

DEFAULT_MODEL_KEY = "small"
DEFAULT_MODEL_NAME = MODEL_PRESETS[DEFAULT_MODEL_KEY]
DEFAULT_PROMPT = "uplifting melodic edm with warm synths and a driving rhythm"

DEFAULT_DURATION_SECONDS = 10
MIN_DURATION_SECONDS = 1
MAX_DURATION_SECONDS = 30

DEFAULT_SAMPLE_RATE = 32000
DEFAULT_DEVICE = "cuda"
DEFAULT_OUTPUT_FORMAT = "wav"
DEFAULT_OUTPUT_FILENAME_PREFIX = "musicgen_output"

SUPPORTED_OUTPUT_FORMATS = ["wav"]
SUPPORTED_DEVICES = ["cuda", "cpu"]
SUPPORTED_MODEL_KEYS = list(MODEL_PRESETS.keys())

HF_CACHE_DIR = PROJECT_ROOT / "hf_cache"
REQUIRED_DIRECTORIES = [WAV_OUTPUT_DIR, MP3_OUTPUT_DIR, INPUT_AUDIO_DIR, HF_CACHE_DIR]