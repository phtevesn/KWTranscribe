import os
import threading
from tkinter import Label, StringVar
from tkinter import filedialog
from tkinter.ttk import Progressbar, Button
from tkinterdnd2 import DND_FILES, TkinterDnD

from faster_whisper import WhisperModel


# ---- Load Whisper model once ----
model = WhisperModel(
    "large-v3",          
    device="cpu",
    compute_type="int8"
)

SUPPORTED_EXTS = (".wav", ".mp3", ".m4a", ".flac")


def safe_set(var, value):
    """Update Tk variables on the main thread safely."""
    app.after(0, var.set, value)


def start_spinner():
    app.after(0, lambda: (progress.start(10), progress.grid()))


def stop_spinner():
    app.after(0, lambda: (progress.stop(), progress.grid_remove()))


def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        save_dir.set(folder)

def start_transcription(file_path: str):
    file_path = file_path.strip().strip("{}").strip()

    if not file_path.lower().endswith(SUPPORTED_EXTS):
        status.set("Unsupported file type")
        return

    if not os.path.exists(file_path):
        status.set("File not found")
        return

    # hide the "new transcription" button whenever a new job starts
    refresh_btn.pack_forget()

    threading.Thread(
        target=transcribe,
        args=(file_path,),
        daemon=True
    ).start()

def transcribe(file_path):
    safe_set(status, "Transcribing...")
    start_spinner()

    try:
        segments, info = model.transcribe(
            file_path,
            language="en",
            beam_size=5,
            vad_filter=True
        )

        # ---- Decide output path ----
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        out_dir = save_dir.get().strip()

        if not out_dir or not os.path.isdir(out_dir):
            # fallback: same folder as audio file
            out_dir = os.path.dirname(file_path)

        out_file = os.path.join(out_dir, base_name + ".txt")

        # ---- Write transcript ----
        with open(out_file, "w", encoding="utf-8") as f:
            last_end = 0.0
            for seg in segments:
                last_end = seg.end
                f.write(f"[{seg.start:.2f} -> {seg.end:.2f}] {seg.text}\n")

                # Optional “live-ish” feedback (not true % progress, but reassuring)
                safe_set(status, f"Transcribing... reached ~{last_end:.1f}s")

        safe_set(status, f"Done! Saved: {out_file}")

    except Exception as e:
        safe_set(status, f"Error: {e}")

    finally:
        stop_spinner()
        app.after(0, lambda: refresh_btn.pack(pady=(15,5)))


def on_drop(event):
    file_path = event.data

    # If multiple files are dropped, take the first one (simple handling)
    # TkDnD often formats this like: "{file1} {file2}"
    if file_path.startswith("{") and "} " in file_path:
        file_path = file_path.split("} ")[0] + "}"

    start_transcription(file_path)

def on_click_label(event=None):
    file_path = filedialog.askopenfilename(
        title="Select audio file",
        filetypes=[
            ("Audio files", "*.wav *.mp3 *.m4a *.flac"),
            ("All files", "*.*"),
        ],
    )
    if file_path:
        start_transcription(file_path)

def reset_ui():
    status.set("Select OR Drag & drop an audio file here")
    refresh_btn.pack_forget()

# ---- UI ----
app = TkinterDnD.Tk()
app.title("Whisper Audio Transcriber")
app.geometry("520x260")

status = StringVar(value="Select OR Drag & drop an audio file here")
save_dir = StringVar(value="")  # empty means “same as audio file folder”

# Top controls
btn = Button(app, text="Choose Save Folder", command=choose_folder)
btn.pack(pady=(15, 5))

save_label = Label(app, textvariable=save_dir, wraplength=480)
save_label.pack(pady=(0, 10))

# Drop zone
label = Label(
    app,
    textvariable=status,
    relief="ridge",
    width=62,
    height=6
)
label.pack(padx=20, pady=(5, 10))
label.bind("<Button-1>", on_click_label)
label.configure(cursor="hand2")  # makes it feel clickable (optional)

refresh_btn = Button(app, text="Create New Transctiption", command=reset_ui)
refresh_btn.pack(pady=(15, 5))
refresh_btn.pack_forget()

label.drop_target_register(DND_FILES)
label.dnd_bind("<<Drop>>", on_drop)

# Progress bar (indeterminate)
progress = Progressbar(app, mode="indeterminate", length=420)
progress.grid_remove()  # hidden until needed
progress.pack(pady=(0, 10))

app.mainloop()
