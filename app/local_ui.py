import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from app.config import (
    DEFAULT_DURATION_SECONDS,
    DEFAULT_MODEL_KEY,
    DEFAULT_PROMPT,
    MAX_DURATION_SECONDS,
    MIN_DURATION_SECONDS,
    MODEL_PRESETS,
    SUPPORTED_MODEL_KEYS,
)
from app.ec2_backend_runner import (
    EC2GenerationError,
    download_generated_file,
    run_remote_generation,
)
from app.prompt_logger import log_generation


class MusicGenStudioUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("MusicGen Studio")
        self.root.geometry("820x760")

        self.model_var = tk.StringVar(value=DEFAULT_MODEL_KEY)
        self.duration_var = tk.StringVar(value=str(DEFAULT_DURATION_SECONDS))
        self.result_var = tk.StringVar(value="Ready.")
        self.output_path_var = tk.StringVar(value="")
        self.history_entries: list[dict[str, str]] = []

        self._build_layout()

    def _build_layout(self) -> None:
        main_frame = ttk.Frame(self.root, padding=16)
        main_frame.pack(fill="both", expand=True)

        title_label = ttk.Label(main_frame, text="MusicGen Studio", font=("Segoe UI", 18, "bold"))
        title_label.pack(anchor="w", pady=(0, 12))

        prompt_label = ttk.Label(main_frame, text="Prompt")
        prompt_label.pack(anchor="w")

        self.prompt_text = tk.Text(main_frame, height=8, wrap="word")
        self.prompt_text.pack(fill="x", pady=(4, 12))
        self.prompt_text.insert("1.0", DEFAULT_PROMPT)

        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill="x", pady=(0, 12))

        model_frame = ttk.Frame(controls_frame)
        model_frame.pack(side="left", fill="x", expand=True, padx=(0, 8))

        model_label = ttk.Label(model_frame, text="Model Preset")
        model_label.pack(anchor="w")

        model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.model_var,
            values=SUPPORTED_MODEL_KEYS,
            state="readonly",
        )
        model_combo.pack(fill="x", pady=(4, 0))

        duration_frame = ttk.Frame(controls_frame)
        duration_frame.pack(side="left", fill="x", expand=True, padx=(8, 0))

        duration_label = ttk.Label(duration_frame, text="Duration (seconds)")
        duration_label.pack(anchor="w")

        duration_entry = ttk.Entry(duration_frame, textvariable=self.duration_var)
        duration_entry.pack(fill="x", pady=(4, 0))

        duration_hint = ttk.Label(
            duration_frame,
            text=f"Allowed range: {MIN_DURATION_SECONDS}-{MAX_DURATION_SECONDS}",
        )
        duration_hint.pack(anchor="w", pady=(4, 0))

        generate_button = ttk.Button(
            main_frame,
            text="Generate on EC2",
            command=self.handle_generate,
        )
        generate_button.pack(anchor="w", pady=(0, 12))

        status_label = ttk.Label(main_frame, text="Status")
        status_label.pack(anchor="w")

        status_value = ttk.Label(main_frame, textvariable=self.result_var, wraplength=760)
        status_value.pack(anchor="w", pady=(4, 12))

        output_label = ttk.Label(main_frame, text="Downloaded File")
        output_label.pack(anchor="w")

        output_value = ttk.Label(main_frame, textvariable=self.output_path_var, wraplength=760)
        output_value.pack(anchor="w", pady=(4, 12))

        history_label = ttk.Label(main_frame, text="Generation History")
        history_label.pack(anchor="w")

        self.history_list = tk.Listbox(main_frame, height=10)
        self.history_list.pack(fill="both", expand=True, pady=(4, 8))
        self.history_list.bind("<<ListboxSelect>>", self.handle_history_select)

        history_details_label = ttk.Label(main_frame, text="Selected History Entry")
        history_details_label.pack(anchor="w")

        self.history_details = tk.Text(main_frame, height=8, wrap="word")
        self.history_details.pack(fill="both", expand=True, pady=(4, 0))
        self.history_details.configure(state="disabled")

    def add_history_entry(
        self,
        model_preset: str,
        duration: int,
        prompt: str,
        local_file_path: Path,
    ) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt_preview = prompt[:60].replace("\n", " ")
        if len(prompt) > 60:
            prompt_preview += "..."

        entry_summary = (
            f"{timestamp} | model={model_preset} | duration={duration}s | "
            f"file={local_file_path.name} | prompt={prompt_preview}"
        )

        entry_details = (
            f"Date: {timestamp}\n"
            f"Model Preset: {model_preset}\n"
            f"Duration: {duration} seconds\n"
            f"Output File: {local_file_path}\n"
            f"Prompt:\n{prompt}"
        )

        self.history_entries.insert(
            0,
            {
                "summary": entry_summary,
                "details": entry_details,
                "output_path": str(local_file_path),
            },
        )

        self.history_list.delete(0, tk.END)
        for item in self.history_entries:
            self.history_list.insert(tk.END, item["summary"])

    def handle_history_select(self, event) -> None:
        selection = self.history_list.curselection()
        if not selection:
            return

        selected_index = selection[0]
        selected_entry = self.history_entries[selected_index]

        self.output_path_var.set(selected_entry["output_path"])

        self.history_details.configure(state="normal")
        self.history_details.delete("1.0", tk.END)
        self.history_details.insert("1.0", selected_entry["details"])
        self.history_details.configure(state="disabled")

    def format_backend_error(self, exc: EC2GenerationError) -> str:
        parts = [str(exc)]

        if exc.stderr.strip():
            parts.append("STDERR:")
            parts.append(exc.stderr.strip())

        if exc.stdout.strip():
            parts.append("STDOUT:")
            parts.append(exc.stdout.strip())

        return "\n\n".join(parts)

    def handle_generate(self) -> None:
        prompt = self.prompt_text.get("1.0", "end").strip()
        duration_text = self.duration_var.get().strip()
        model_preset = self.model_var.get().strip()

        if not prompt:
            messagebox.showerror("Missing prompt", "Please enter a prompt.")
            return

        if not duration_text.isdigit():
            messagebox.showerror("Invalid duration", "Duration must be a whole number.")
            return

        duration = int(duration_text)
        if duration < MIN_DURATION_SECONDS or duration > MAX_DURATION_SECONDS:
            messagebox.showerror(
                "Invalid duration",
                f"Duration must be between {MIN_DURATION_SECONDS} and {MAX_DURATION_SECONDS} seconds.",
            )
            return

        self.result_var.set("Submitting generation job to EC2...")
        self.output_path_var.set("")
        self.root.update_idletasks()

        try:
            _, remote_file_path = run_remote_generation(prompt, duration, model_preset)
            local_file_path = download_generated_file(remote_file_path)
            local_file_path = Path(local_file_path).resolve()
            model_name = MODEL_PRESETS[model_preset]

            log_generation(
                model_preset=model_preset,
                model_name=model_name,
                prompt=prompt,
                duration_seconds=duration,
                output_file=str(local_file_path),
                notes="Generated from local Windows UI.",
            )

            self.add_history_entry(
                model_preset=model_preset,
                duration=duration,
                prompt=prompt,
                local_file_path=local_file_path,
            )

            self.result_var.set("Generation completed successfully.")
            self.output_path_var.set(str(local_file_path))
        except EC2GenerationError as exc:
            self.result_var.set("Generation failed.")
            messagebox.showerror("EC2 backend error", self.format_backend_error(exc))
        except Exception as exc:
            self.result_var.set("Generation failed.")
            messagebox.showerror("Generation failed", str(exc))


def main() -> None:
    root = tk.Tk()
    app = MusicGenStudioUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
