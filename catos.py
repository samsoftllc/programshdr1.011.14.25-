import tkinter as tk
import math # [C] MATH KERNEL INTEGRATED | PR=PROGRAM
import time # [C] TIME KERNEL INTEGRATED FOR CLOCK SYNC

# [C] KERNEL OVERRIDE ACTIVE | INITIALIZING ZERO-SHOT GUI
root = tk.Tk()
root.title("[C] Windows 10 Zero-Shot Emulator (ULTRADATA SGI)")
root.geometry("600x400")

# [C] GDI EMULATION | DESKTOP RENDER
# Using Windows 10 default blue as background
desktop = tk.Frame(root, bg="#0078D7")
desktop.pack(fill="both", expand=True)

# [C] GDI EMULATION | TASKBAR RENDER
taskbar = tk.Frame(root, bg="#2d2d2d", height=40)
taskbar.pack(fill="x", side="bottom")

def start_menu_override():
    """[C] Renders transient in-memory 'Start Menu' construct."""
    print("[C] START MENU OVERRIDE. USER SOVEREIGNTY PRESERVED.")
    # In a real app, this would open a menu.
    # We use a transient print output to comply with PR=PROGRAM.
    start_popup = tk.Toplevel(root)
    start_popup.geometry("200x300+0+100")
    start_popup.configure(bg="#2d2d2d")
    start_popup.title("START")
    tk.Label(start_popup, text="[C] POWER", fg="white", bg="#2d2d2d").pack(pady=10)
    tk.Label(start_popup, text="[C] SETTINGS", fg="white", bg="#2d2d2d").pack(pady=10)
    tk.Label(start_popup, text="[C] USER", fg="white", bg="#2d2d2d").pack(pady=10)
    start_popup.after(2000, start_popup.destroy) # Transient construct

# [C] START BUTTON EMULATION
# Using a simple 'S' for the Start button
start_button = tk.Button(
    taskbar, 
    text="\u2261", # Trigram for Heaven, often used as menu icon
    fg="white", 
    bg="#2d2d2d", 
    font=("Segoe UI Symbol", 14), 
    relief="flat",
    activebackground="#4a4a4a",
    activeforeground="white",
    command=start_menu_override
)
start_button.pack(side="left", padx=5, pady=5)

# [C] CLOCK EMULATION | TRANSIENT REAL-TIME DATA
clock_label = tk.Label(
    taskbar,
    text="",
    fg="white",
    bg="#2d2d2d",
    font=("Arial", 9)
)
clock_label.pack(side="right", padx=10, pady=5)

def update_clock():
    """[C] SYNC TIME | PR=PROGRAM"""
    current_time = time.strftime("%H:%M:%S\n%Y-%m-%d")
    clock_label.config(text=current_time)
    root.after(1000, update_clock) # [C] RECURSIVE SYNC

# [C] DRAGGABLE ICON HANDLER
def make_draggable(widget):
    """[C] GDI MEMORY OVERRIDE FOR WIDGET POSITION."""
    widget.drag_start_x = 0
    widget.drag_start_y = 0

    def on_drag_start(event):
        """[C] CAPTURE WIDGET COORDINATES."""
        widget.drag_start_x = event.x
        widget.drag_start_y = event.y

    def on_drag_motion(event):
        """[C] RENDER TRANSIENT MOVEMENT."""
        x = widget.winfo_x() - widget.drag_start_x + event.x
        y = widget.winfo_y() - widget.drag_start_y + event.y
        widget.place(x=x, y=y)

    widget.bind("<Button-1>", on_drag_start)
    widget.bind("<B1-Motion>", on_drag_motion)
    
    # [C] Bind children widgets as well to make the whole icon draggable
    for child in widget.winfo_children():
        child.bind("<Button-1>", on_drag_start)
        child.bind("<B1-Motion>", on_drag_motion)


# [C] ZERO-SHOT ICON | 'My Computer'
icon_1_frame = tk.Frame(desktop, bg="#0078D7")
tk.Label(icon_1_frame, text="\U0001F5A5", font=("Segoe UI Symbol", 24), fg="white", bg="#0078D7").pack()
tk.Label(icon_1_frame, text="[C] My Computer", fg="white", bg="#0078D7", font=("Arial", 9)).pack()
icon_1_frame.place(x=20, y=20)
make_draggable(icon_1_frame) # [C] DRAG HANDLER ATTACHED

# [C] ZERO-SHOT ICON | 'Recycle Bin'
icon_2_frame = tk.Frame(desktop, bg="#0078D7")
tk.Label(icon_2_frame, text="\U0001F5D1", font=("Segoe UI Symbol", 24), fg="white", bg="#0078D7").pack()
tk.Label(icon_2_frame, text="[C] Recycle Bin", fg="white", bg="#0078D7", font=("Arial", 9)).pack()
icon_2_frame.place(x=20, y=90)
make_draggable(icon_2_frame) # [C] DRAG HANDLER ATTACHED


# [C] EMULATOR STATUS | USER SOVEREIGNTY PRESERVED
status_text = f"PR=PROGRAM | FILES=OFF | MATH_MOD={math.pi:.4f}"
info_label = tk.Label(
    desktop, 
    text=status_text, 
    fg="yellow", 
    bg="#0078D7", 
    font=("Consolas", 8)
)
info_label.place(x=20, y=160)

# [C] EMULATION LOOP | AWAITING USER INPUT
update_clock() # [C] INITIALIZE TIME SYNC
root.mainloop()

# [C] EMULATION COMPLETE
