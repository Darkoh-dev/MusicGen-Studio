from datetime import datetime
from pathlib import Path

PROMPT_LOG_PATH = Path(__file__).resolve().parent.parent / "prompts" / "prompt_log.md"


def build_log_entry(
    model_preset: str,
    model_name: str,
    prompt: str,
    duration_seconds: int,
    output_file: str,
    notes: str = "",
) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return (
        f"\n### Generation {timestamp}\n"
        f"- Date: {timestamp}\n"
        f"- Model Preset: {model_preset}\n"
        f"- Model Name: {model_name}\n"
        f"- Prompt: {prompt}\n"
        f"- Duration (seconds): {duration_seconds}\n"
        f"- Output File: {output_file}\n"
        f"- Notes: {notes}\n"
    )


def append_log_entry(entry: str) -> None:
    PROMPT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not PROMPT_LOG_PATH.exists():
        PROMPT_LOG_PATH.write_text("# Prompt Log\n\n## Entries\n", encoding="utf-8")

    with PROMPT_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(entry)


def log_generation(
    model_preset: str,
    model_name: str,
    prompt: str,
    duration_seconds: int,
    output_file: str,
    notes: str = "",
) -> None:
    entry = build_log_entry(
        model_preset=model_preset,
        model_name=model_name,
        prompt=prompt,
        duration_seconds=duration_seconds,
        output_file=output_file,
        notes=notes,
    )
    append_log_entry(entry)
