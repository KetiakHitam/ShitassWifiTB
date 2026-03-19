import sys
import os

# Pyinstaller --noconsole fix for speedtest-cli
# Prevents AttributeError: 'NoneType' object has no attribute 'fileno' 
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
