# main.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tkinter as tk
from gerenjizhang.gui import init_gui, BillApp

if __name__ == "__main__":
    init_gui()
    root = tk.Tk()
    app = BillApp(root)
    root.mainloop()
