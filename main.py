import os
import sys
import warnings
from ui.gui_app import App
from utils.error_handler import setup_global_error_handling

# Suppress warnings for cleaner console output
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
warnings.filterwarnings("ignore", category=DeprecationWarning)

if __name__ == "__main__":
    setup_global_error_handling()
    app = App()
    app.mainloop()
