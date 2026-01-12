import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QProgressBar,
    QVBoxLayout, QFileDialog
)

from faster_whisper import WhisperModel

SUPPORTED_EXTS = (".wav", ".mp3", ".m4a", ".flac")


# ---- Worker thread ----
class TranscribeWorker(QThread):
    status = Signal(str)      # live status messages
    done = Signal(str)        # output file path when finished
    error = Signal(str)       # error text

    def __init__(self, model: WhisperModel, file_path: str, save_dir: str):
        super().__init__()
        self.model = model
        self.file_path = file_path
        self.save_dir = save_dir

    def run(self):
        try:
            self.status.emit("Transcribing...")

            segments, info = self.model.transcribe(
                self.file_path,
                language="en",
                beam_size=5,
                vad_filter=True
            )

            base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            out_dir = (self.save_dir or "").strip()

            if not out_dir or not os.path.isdir(out_dir):
                out_dir = os.path.dirname(self.file_path)

            out_file = os.path.join(out_dir, base_name + ".txt")

            last_end = 0.0
            with open(out_file, "w", encoding="utf-8") as f:
                for seg in segments:
                    last_end = seg.end
                    f.write(f"[{seg.start:.2f} -> {seg.end:.2f}] {seg.text}\n")
                    self.status.emit(f"Transcribing... reached ~{last_end:.1f}s")

            self.done.emit(out_file)

        except Exception as e:
            self.error.emit(str(e))


# ---- Drop zone widget ----
class DropZone(QLabel):
    clicked = Signal()
    file_dropped = Signal(str)

    def __init__(self, text: str):
        super().__init__(text)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.PointingHandCursor)

        # simple styling so it looks like your ridge box
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #888;
                border-radius: 8px;
                padding: 14px;
            }
        """)

        self.setMinimumHeight(120)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        # take the first file
        file_path = urls[0].toLocalFile()
        if file_path:
            self.file_dropped.emit(file_path)


# ---- Main UI ----
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Whisper Audio Transcriber")
        self.setFixedSize(520, 260)

        # ---- Load Whisper model once ----
        self.model = WhisperModel(
            "large-v3",
            device="cpu",
            compute_type="int8"
        )

        self.save_dir = ""     # empty => same as audio file folder
        self.worker = None     # holds active thread

        # Widgets
        self.choose_btn = QPushButton("Choose Save Folder")
        self.save_label = QLabel("")
        self.save_label.setWordWrap(True)

        self.status_text = "Select OR Drag & drop an audio file here"
        self.drop_zone = DropZone(self.status_text)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # indeterminate
        self.progress.setVisible(False)

        self.refresh_btn = QPushButton("Create New Transcription")
        self.refresh_btn.setVisible(False)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 15, 18, 12)
        layout.setSpacing(8)

        layout.addWidget(self.choose_btn)
        layout.addWidget(self.save_label)
        layout.addWidget(self.drop_zone)
        layout.addWidget(self.progress)
        layout.addWidget(self.refresh_btn)

        self.setLayout(layout)

        # Wiring
        self.choose_btn.clicked.connect(self.choose_folder)
        self.drop_zone.clicked.connect(self.pick_file)
        self.drop_zone.file_dropped.connect(self.start_transcription)
        self.refresh_btn.clicked.connect(self.reset_ui)

    # ---- Helpers ----
    def set_status(self, msg: str):
        self.drop_zone.setText(msg)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Save Folder")
        if folder:
            self.save_dir = folder
            self.save_label.setText(folder)

    def pick_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select audio file",
            "",
            "Audio files (*.wav *.mp3 *.m4a *.flac);;All files (*.*)"
        )
        if file_path:
            self.start_transcription(file_path)

    def start_transcription(self, file_path: str):
        file_path = file_path.strip()

        if not file_path.lower().endswith(SUPPORTED_EXTS):
            self.set_status("Unsupported file type")
            return

        if not os.path.exists(file_path):
            self.set_status("File not found")
            return

        # UI state for new job
        self.refresh_btn.setVisible(False)
        self.progress.setVisible(True)
        self.set_status("Transcribing...")

        # Start worker
        self.worker = TranscribeWorker(self.model, file_path, self.save_dir)
        self.worker.status.connect(self.set_status)
        self.worker.done.connect(self.on_done)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_done(self, out_file: str):
        self.progress.setVisible(False)
        self.set_status(f"Done! Saved: {out_file}")
        self.refresh_btn.setVisible(True)

    def on_error(self, err: str):
        self.progress.setVisible(False)
        self.set_status(f"Error: {err}")
        self.refresh_btn.setVisible(True)

    def reset_ui(self):
        self.set_status("Select OR Drag & drop an audio file here")
        self.refresh_btn.setVisible(False)


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
