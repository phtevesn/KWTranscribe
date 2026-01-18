
import os
import threading
from tkinter import Label as TkLabel, StringVar, Button as TkButton, font
from tkinter import filedialog
from tkinter.ttk import (
    Progressbar, Button, Label, Radiobutton, Frame,
    Combobox
)
from tkinterdnd2 import DND_FILES, TkinterDnD

from faster_whisper import WhisperModel

from spot import (
    MODEL_SIZES, C_TYPE, HW, FILETYPES,
    MIN_FONT, MAX_FONT
)
from text.whisper_service import load_model, transcribe
from text.filetype_service import (
    valid_filetype, 
    create_out_file_path,
    handle_filetype
)

model = None 
app = TkinterDnD.Tk()
app.title("KW Transcribe")
app.geometry("1040x580")
app.model = None
app.files = None
app.size = 14
default_font = font.nametofont("TkDefaultFont")
default_font.configure(size = app.size)
#--Handlers--
def on_submit():
    selected_size = model_size.get()
    if not selected_size:
        print("Select an option")
        return 
    
    options_frame.pack_forget()

    loading_frame.pack(fill="x", padx=12, pady=12)
    progress.start(10)
    def worker():
        try:
            model = load_model(selected_size, HW, C_TYPE)
            if not model:
                print("model not loaded")
            else:
                print("model loaded")
            app.model = model
            
        finally:
            app.after(0, finish_loading)

    def finish_loading():
        progress.stop()
        loading_frame.pack_forget()
        home_frame.pack(fill="x", padx=12, pady=12)

    threading.Thread(target=worker, daemon=True).start()

def lower_font_size():
    if app.size > MIN_FONT:
        app.size-=2
        default_font.configure(size = app.size)
    
def raise_font_size():
    if app.size < MAX_FONT:
        app.size+=2
        default_font.configure(size = app.size)


def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        save_dir.set(folder)

def choose_model():
    home_frame.pack_forget()
    options_frame.pack(fill="x", padx=12, pady=12)

def on_click_label(event=None):
    file_paths = filedialog.askopenfilenames(
        title="Select audio file",
        filetypes=[
            ("Audio files", "*.wav *.mp3 *.m4a *.flac"),
            ("All files", "*.*"),
        ],
    )
    if file_paths:
        status.set(f"Files to transcribe: {len(file_paths)}")
        app.files = file_paths

def on_drop(event):
    dropped_files = event.data
    
    files = dropped_files.split(" ")
    for file in files:
        if not valid_filetype(file):
            status.set(f"Invalid file type {file} \n Select OR Drag & drop an audio files here")
            return
    status.set(f"Files to transcribe: {len(files)}")
    app.files = files

def start_transcription():
    model = app.model

    files = app.files
    save_directory = save_dir.get()
    save_filetype = save_type.get()

    if not model:
        print("Error finding model, restart app")
        return
    if not files:
        print("Select or DND an audio file")
        return
    if not save_filetype:
        print("Error selecting save filetype")
        return 
    
    out_file_path = create_out_file_path(files, save_directory, save_filetype)
    if not out_file_path:
        print("invalid file save location")
        return
    
    def worker():
        try:
            segments = transcribe(model, files)
            handle_filetype(save_filetype, segments, out_file_path)
            app.after(0, lambda: on_transcription_done(out_file_path))
        except Exception as e:
            app.after(0, lambda: on_transcription_error(e))
    
    home_frame.pack_forget()
    t_progress.start(10)
    t_frame.pack(fill="x", padx=12, pady=12)
    t_status.set("Transcribing... (This may take a while)")
    threading.Thread(target=worker, daemon=True).start()

def on_transcription_done(out_file_path):
    t_progress.stop()
    t_status.set(f"Finished. Wrote to: {out_file_path}")
    t_refresh_btn.pack(pady=(12, 0))

def on_transcription_error(e):
    t_progress.stop()
    t_status.set(f"Transcription failed: {e}")
    t_refresh_btn.pack(pady=(12, 0))

def reset_ui():
    t_refresh_btn.pack_forget()
    in_file_path.set("")
    save_dir.set("")
    status.set("Select OR Drag & drop an audio files here")
    t_frame.pack_forget()
    home_frame.pack(fill="x", padx=12, pady=12)
    

#--Frames--
options_frame = Frame(app)
options_frame.pack(fill="x", padx=12, pady=12)
model_size = StringVar(value="")
form_label = Label(options_frame, text="Choose model size: ")
form_label.pack(pady=(0,6), anchor="w")
for opt in MODEL_SIZES:
    rb = Radiobutton(options_frame, text=opt, value=opt, variable=model_size)
    rb.pack(anchor="w", padx=6)
submit_btn = Button(options_frame, text="Generate Transcription Model",
                    command=on_submit)
submit_btn.pack(pady=(12,0))


loading_frame = Frame(app)
loading_label= Label(loading_frame, text="Loading model...")
loading_label.pack(pady=(12,6))
progress = Progressbar(loading_frame, mode="indeterminate")
progress.pack(fill="x", padx=12)

home_frame = Frame(app)

model_row = Frame(home_frame)
model_row.pack(padx=2, pady=(1, 1), anchor='w', fill='x')
model_button = TkButton(  
    model_row,
    text="...",
    command=choose_model,
    borderwidth=1,
    highlightthickness=0
)
model_button.pack(padx=(0,2), side="left", anchor='w')
model_colon = Label(model_row, text="Current model size: ")
model_colon.pack(side="left", anchor='w')
model_label = Label(model_row, textvariable=model_size)
model_label.pack(padx=2, side="left", anchor='w')
font_size_label = Label(model_row, text="Font Size: ")
font_size_down = TkButton(model_row, text="-", command=lower_font_size)
font_size_up = TkButton(model_row, text="+", command=raise_font_size)
font_size_down.pack(padx=1,side="right", anchor='e')
font_size_up.pack(padx=1, side="right", anchor='e')
font_size_label.pack(padx=1, side="right", anchor='e')


status = StringVar(value="Select OR Drag & drop an audio files here")
save_dir = StringVar(value="") 
btn = Button(home_frame, text="Choose New Save Folder", command=choose_folder)
btn.pack(pady=(2,0))
save_label = Label(home_frame, textvariable=save_dir, wraplength=480)
save_label.pack(pady=(0, 10))

in_file_path = StringVar(value="")
label = TkLabel(
    home_frame,
    textvariable=status,
    relief="ridge",
    width=62,
    height=6
)
label.pack(padx=20)
label.bind("<Button-1>", on_click_label)
label.configure(cursor="hand2") 
label.drop_target_register(DND_FILES)
label.dnd_bind("<<Drop>>", on_drop)

row = Frame(home_frame)
row.pack(padx=6, pady=(10, 10))
save_type = StringVar(value="")
save_dropdown = Combobox(
    row,
    textvariable=save_type,
    values=FILETYPES,
    state="readonly",
    width=18
)
save_dropdown.pack(side="right")

save_dropdown_label = Label(row, text="File type of transcription: ")
save_dropdown_label.pack(side="left", padx=(10, 0))
save_dropdown.current(0)

transcribe_btn = Button(home_frame, text="Start transcription", 
                           command=start_transcription)
transcribe_btn.pack(pady=(12,0))

t_status = StringVar(value="")
t_frame = Frame(app)
t_loading_label= Label(t_frame, textvariable=t_status)
t_loading_label.pack(pady=(12,6))
t_progress = Progressbar(t_frame, mode="indeterminate")
t_progress.pack(fill="x", padx=12)
t_refresh_btn = Button(t_frame, text="Create new transcription",
                       command = reset_ui)
t_refresh_btn.pack_forget()

app.mainloop()