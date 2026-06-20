import os
import sys
import warnings
import static_ffmpeg
from ui.gui_app import App
from utils.error_handler import setup_global_error_handling

# In windowed mode (EXE), sys.stdout and sys.stderr are None. 
# static_ffmpeg tries to write to stdout, causing a crash. We mock them here.
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

# Add ffmpeg to PATH automatically
static_ffmpeg.add_paths()

# Suppress warnings for cleaner console output
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
warnings.filterwarnings("ignore", category=DeprecationWarning)

if __name__ == "__main__":
    setup_global_error_handling()
    app = App()
    app.mainloop()
