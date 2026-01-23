# KW Transcribe
Local Windows 11 desktop application for transcribing audio files using
[faster-whisper](https://github.com/SYSTRAN/faster-whisper).

## Requirments 
- Python                    3.11.9
- faster-whisper            1.2.1
- tkinterdnd2               0.4.3 
- reportlab                 4.4.7
- python-docx               1.2.0
- huggingface_hub           1.2.4

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourname/kw-transcribe.git
   cd kw-transcribe

2. Create and activate virtual environment:
   ```bash
   py -3.11.9 -m  venv .venv
   .venv\Scripts\activate.bat

3. Install dependencies:
   ```bash
   pip install requirements.txt

4. Install faster-whisper models from hugging face:
   ```bash
   py huggingface.py

5. Start app:
   ```bash
   py app.py

### Creating an executable (Optional)

6. Install pyinstaller:
   ```bash
   pip install pyinstaller

7. Create executable:
   ```bash
   pyinstaller app.py --onefile

8. Copy executable and models into separate folder:

  Create a new folder (for example: KW_Transcribe) and place the
  generated executable and the downloaded models/ directory inside it.

  Your final folder structure should look like this:
  ```text
  KW_Transcribe/
  │
  ├── app.exe
  └── models/
      ├── faster-whisper-base/
      ├── faster-whisper-small/
      └── ...
```
## Usage


     
