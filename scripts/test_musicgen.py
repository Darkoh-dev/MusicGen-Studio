from transformers import AutoProcessor, MusicgenForConditionalGeneration

MODEL_NAME = "facebook/musicgen-small"
TEST_PROMPT = "bright melodic electronic loop with soft synth layers"
TARGET_DEVICE = "cuda"


def main() -> None:
    print("MusicGen-Studio model load test")
    print(f"Target model: {MODEL_NAME}")
    print(f"Target device: {TARGET_DEVICE}")

    processor = AutoProcessor.from_pretrained(MODEL_NAME)
    model = MusicgenForConditionalGeneration.from_pretrained(MODEL_NAME)
    model = model.to(TARGET_DEVICE)

    inputs = processor(
        text=[TEST_PROMPT],
        padding=True,
        return_tensors="pt",
    )
    inputs = {key: value.to(TARGET_DEVICE) for key, value in inputs.items()}

    audio_values = model.generate(
        **inputs,
        max_new_tokens=256,
    )

    print("Model load test completed.")
    print(f"Prompt: {TEST_PROMPT}")
    print(f"Generated tensor shape: {tuple(audio_values.shape)}")

if __name__ == "__main__":
    main()