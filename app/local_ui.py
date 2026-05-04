import os
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

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
        self.input_audio_path_var = tk.StringVar(value="")
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

        input_audio_label = ttk.Label(main_frame, text="Reference Audio for Melody")
        input_audio_label.pack(anchor="w")

        input_audio_frame = ttk.Frame(main_frame)
        input_audio_frame.pack(fill="x", pady=(4, 12))

        input_audio_value = ttk.Label(
            input_audio_frame,
            textvariable=self.input_audio_path_var,
            wraplength=620,
        )
        input_audio_value.pack(side="left", fill="x", expand=True)

        browse_audio_button = ttk.Button(
            input_audio_frame,
            text="Browse",
            command=self.handle_browse_input_audio,
        )
        browse_audio_button.pack(side="left", padx=(8, 0))

        clear_audio_button = ttk.Button(
            input_audio_frame,
            text="Clear",
            command=self.handle_clear_input_audio,
        )
        clear_audio_button.pack(side="left", padx=(8, 0))

        self.generate_button = ttk.Button(
            main_frame,
            text="Generate on EC2",
            command=self.handle_generate,
        )
        self.generate_button.pack(anchor="w", pady=(0, 12))

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

        history_actions_frame = ttk.Frame(main_frame)
        history_actions_frame.pack(fill="x", pady=(0, 8))

        copy_output_button = ttk.Button(
            history_actions_frame,
            text="Copy Output Path",
            command=self.handle_copy_selected_output_path,
        )
        copy_output_button.pack(side="left")

        open_output_folder_button = ttk.Button(
            history_actions_frame,
            text="Open Output Folder",
            command=self.handle_open_selected_output_folder,
        )
        open_output_folder_button.pack(side="left", padx=(8, 0))

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
        input_audio_path: str | None = None,
    ) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt_preview = prompt[:60].replace("\n", " ")
        if len(prompt) > 60:
            prompt_preview += "..."

        input_audio_name = Path(input_audio_path).name if input_audio_path else "None"
        
        entry_summary = (
            f"{timestamp} | model={model_preset} | duration={duration}s | "
            f"input={input_audio_name} | file={local_file_path.name} | prompt={prompt_preview}"
        )

        entry_details = (
            f"Date: {timestamp}\n"
            f"Model Preset: {model_preset}\n"
            f"Duration: {duration} seconds\n"
            f"Input Audio: {input_audio_path or 'None'}\n"
            f"Output File: {local_file_path}\n"
            f"Prompt:\n{prompt}"
        )

        self.history_entries.insert(
            0,
            {
                "summary": entry_summary,
                "details": entry_details,
                "output_path": str(local_file_path),
                "input_audio_path": input_audio_path or "",
                "model_preset": model_preset,
                "duration": str(duration),
                "prompt": prompt,
            },
        )

        self.history_list.delete(0, tk.END)
        for item in self.history_entries:
            self.history_list.insert(tk.END, item["summary"])

    def get_selected_history_entry(self) -> dict[str, str] | None:
        selection = self.history_list.curselection()
        if not selection:
            return None
        
        selected_index = selection[0]
        return self.history_entries[selected_index]

    def handle_history_select(self, event) -> None:
        selected_entry = self.get_selected_history_entry()
        if not selected_entry:
            return

        self.output_path_var.set(selected_entry["output_path"])

        self.history_details.configure(state="normal")
        self.history_details.delete("1.0", tk.END)
        self.history_details.insert("1.0", selected_entry["details"])
        self.history_details.configure(state="disabled")

    def handle_copy_selected_output_path(self) -> None:
        selected_entry = self.get_selected_history_entry()
        if not selected_entry:
            messagebox.showinfo("No history selected", "Please select a history entry first.")
            return
        
        output_path = selected_entry["output_path"]
        self.root.clipboard_clear()
        self.root.clipboard_append(output_path)
        self.result_var.set("Copied output path to clipboard.")

    def handle_open_selected_output_folder(self) -> None:
        selected_entry = self.get_selected_history_entry()
        if not selected_entry:
            messagebox.showinfo("No history selected", "Please select a history entry first.")
            return
        
        output_path = Path(selected_entry["output_path"])
        output_folder = output_path.parent

        if not output_folder.exists():
            messagebox.showerror("Folder not found", f"Output folder not found:\n{output_folder}")
            return
        
        os.startfile(output_folder)

    def format_backend_error(self, exc: EC2GenerationError) -> str:
        parts = [str(exc)]

        if exc.stderr.strip():
            parts.append("STDERR:")
            parts.append(exc.stderr.strip())

        if exc.stdout.strip():
            parts.append("STDOUT:")
            parts.append(exc.stdout.strip())

        return "\n\n".join(parts)
    
    def handle_browse_input_audio(self) -> None:
        selected_path = filedialog.askopenfilename(
            title="Choose reference audio",
            filetypes=[
                ("Audio files", "*.wav *.mp3 *.flac *.ogg *.m4a"),
                ("All files", "*.*"),
            ],
        )

        if selected_path:
            self.input_audio_path_var.set(selected_path)

    def handle_clear_input_audio(self) -> None:
        self.input_audio_path_var.set("")

    def handle_generate(self) -> None:
        prompt = self.prompt_text.get("1.0", "end").strip()
        duration_text = self.duration_var.get().strip()
        model_preset = self.model_var.get().strip()
        selected_input_audio = self.input_audio_path_var.get().strip()
        input_audio_path = selected_input_audio if model_preset == "melody" else None

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
        
        if model_preset == "melody" and not input_audio_path:
            messagebox.showerror(
                "Missing reference audio",
                "Please choose a reference audio file for the melody model.",
            )
            return

        self.result_var.set("Submitting generation job to EC2...")
        self.output_path_var.set("")
        self.generate_button.configure(state="disabled")
        self.root.update_idletasks()

        generation_thread = threading.Thread(
            target=self.run_generation_job,
            args=(prompt, duration, model_preset, input_audio_path),
            daemon=True,
        )
        generation_thread.start()


    def run_generation_job(
            self,
            prompt: str,
            duration: int,
            model_preset: str,
            input_audio_path: str | None,
    ) -> None:
        try:
            _, remote_file_path = run_remote_generation(
                prompt,
                duration,
                model_preset,
                input_audio_path,
            )
            local_file_path = download_generated_file(remote_file_path)
            local_file_path = Path(local_file_path).resolve()

            self.root.after(
                0,
                self.handle_generation_success,
                prompt,
                duration,
                model_preset,
                input_audio_path,
                local_file_path,
            )
        except EC2GenerationError as exc:
            self.root.after(0, self.handle_generation_backend_error, exc)
        except Exception as exc:
            self.root.after(0, self.handle_generation_unexpected_error, exc)

    
    def handle_generation_success(
            self,
            prompt: str,
            duration: int,
            model_preset: str,
            input_audio_path: str | None,
            local_file_path: Path,
    ) -> None:
        model_name = MODEL_PRESETS[model_preset]

        log_generation(
            model_preset=model_preset,
            model_name=model_name,
            prompt=prompt,
            duration_seconds=duration,
            output_file=str(local_file_path),
            notes=f"Generated from local Windows UI. Input audio: {input_audio_path or 'None'}",
        )

        self.add_history_entry(
            model_preset=model_preset,
            duration=duration,
            prompt=prompt,
            local_file_path=local_file_path,
            input_audio_path=input_audio_path,
        )

        self.result_var.set("Generation completed successfully.")
        self.output_path_var.set(str(local_file_path))
        self.generate_button.configure(state="normal")


    def handle_generation_backend_error(self, exc: EC2GenerationError) -> None:
        self.result_var.set("Generation failed.")
        self.generate_button.configure(state="normal")
        messagebox.showerror("EC2 backend error", self.format_backend_error(exc))


    def handle_generation_unexpected_error(self, exc: Exception) -> None:
        self.result_var.set("Generation failed.")
        self.generate_button.configure(state="normal")
        messagebox.showerror("Generation failed", str(exc))


def main() -> None:
    root = tk.Tk()
    app = MusicGenStudioUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
