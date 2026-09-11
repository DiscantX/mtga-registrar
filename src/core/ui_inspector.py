"""Standalone UI Inspector application for MTGA Registrar.

Provides a lightweight tkinter GUI to visualize and inspect UI element locations
defined in [`src/core/ui_locations.py`](src/core/ui_locations.py) overlaid on screen screenshots
by aspect ratio and screen classification.
"""

import os
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from PIL import Image, ImageTk

from src.core.ui_locations import (
    ASPECT_RATIO_REGISTRIES,
    AVAILABLE_SCREENS,
    SCREEN_IMAGE_MAPPING,
    get_location,
)


class UIInspectorApp:
    """Tkinter application for inspecting UI element bounding boxes on images."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the UI Inspector application.

        Args:
            root: Root tkinter window.
        """
        self.root = root
        self.root.title("MTGA Registrar - UI Location Inspector")
        self.root.geometry("1200x850")

        self.aspect_ratio_var = tk.StringVar(value="16:10")
        self.screen_var = tk.StringVar(value=AVAILABLE_SCREENS[0])
        self.show_all_var = tk.BooleanVar(value=True)

        self.original_image: Optional[Image.Image] = None
        self.tk_image: Optional[ImageTk.PhotoImage] = None
        self.image_width = 0
        self.image_height = 0

        self.create_widgets()
        self.load_image_and_redraw()

    def create_widgets(self) -> None:
        """Create GUI widgets (controls, canvas, element list)."""
        # Top control frame
        control_frame = ttk.LabelFrame(
            self.root, text="Controls & Configuration", padding=10
        )
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Aspect Ratio Selector
        ttk.Label(control_frame, text="Aspect Ratio:").grid(
            row=0, column=0, sticky=tk.W, padx=5
        )
        ar_combo = ttk.Combobox(
            control_frame,
            textvariable=self.aspect_ratio_var,
            values=list(ASPECT_RATIO_REGISTRIES.keys()),
            state="readonly",
            width=10,
        )
        ar_combo.grid(row=0, column=1, padx=5)
        ar_combo.bind(
            "<<ComboboxSelected>>", lambda e: self.on_config_changed()
        )

        # Screen Selector
        ttk.Label(control_frame, text="Screen:").grid(
            row=0, column=2, sticky=tk.W, padx=5
        )
        screen_combo = ttk.Combobox(
            control_frame,
            textvariable=self.screen_var,
            values=AVAILABLE_SCREENS,
            state="readonly",
            width=22,
        )
        screen_combo.grid(row=0, column=3, padx=5)
        screen_combo.bind(
            "<<ComboboxSelected>>", lambda e: self.on_config_changed()
        )

        reload_btn = ttk.Button(
            control_frame,
            text="Reload & Redraw",
            command=self.load_image_and_redraw,
        )
        reload_btn.grid(row=0, column=4, padx=5)

        show_all_chk = ttk.Checkbutton(
            control_frame,
            text="Show All Screens",
            variable=self.show_all_var,
            command=self.redraw,
        )
        show_all_chk.grid(row=0, column=5, padx=10)

        # Main content area
        content_frame = ttk.Frame(self.root, padding=10)
        content_frame.pack(
            side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5
        )

        # Canvas container with scrollbars
        canvas_frame = ttk.LabelFrame(content_frame, text="UI Preview", padding=5)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        self.canvas = tk.Canvas(
            canvas_frame, bg="#222222", scrollregion=(0, 0, 2000, 2000)
        )
        h_scroll = ttk.Scrollbar(
            canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )
        v_scroll = ttk.Scrollbar(
            canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        self.canvas.configure(
            xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set
        )

        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Right side: Elements registry viewer
        right_frame = ttk.LabelFrame(
            content_frame, text="Registered UI Elements", padding=5, width=350
        )
        right_frame.pack_propagate(False)
        right_frame.pack(
            side=tk.RIGHT, fill=tk.BOTH, expand=False
        )

        columns = ("name", "screen", "calibrated", "coords")
        self.tree = ttk.Treeview(
            right_frame, columns=columns, show="headings", height=20
        )
        self.tree.heading("name", text="Element")
        self.tree.heading("screen", text="Screen")
        self.tree.heading("calibrated", text="Cal.")
        self.tree.heading("coords", text="X, Y, W, H")
        self.tree.column("name", width=110)
        self.tree.column("screen", width=90)
        self.tree.column("calibrated", width=35, anchor=tk.CENTER)
        self.tree.column("coords", width=110)
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5))

        self.tree.bind("<<TreeviewSelect>>", self.on_element_select)

        info_text = (
            "Tip: Click an element in the list or canvas to highlight its box.\n"
            "Green = Calibrated, Orange = Uncalibrated."
        )
        info_label = ttk.Label(
            right_frame,
            text=info_text,
            wraplength=320,
            justify=tk.LEFT,
        )
        info_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

    def on_config_changed(self) -> None:
        """Handle aspect ratio or screen selection change."""
        self.load_image_and_redraw()

    def load_image_and_redraw(self) -> None:
        """Load the image for the selected aspect ratio and screen."""
        aspect_ratio = self.aspect_ratio_var.get()
        screen = self.screen_var.get()

        ar_mapping = SCREEN_IMAGE_MAPPING.get(aspect_ratio, {})
        image_path = ar_mapping.get(screen, "screens/16-10_deck_screen.png")

        if not os.path.exists(image_path):
            # Fallback
            image_path = "screens/16-10_deck_screen.png"

        try:
            self.original_image = Image.open(image_path)
            self.image_width, self.image_height = self.original_image.size
            self.tk_image = ImageTk.PhotoImage(self.original_image)

            self.canvas.config(
                scrollregion=(0, 0, self.image_width, self.image_height)
            )
            self.redraw()
            self.populate_treeview()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def populate_treeview(self) -> None:
        """Populate the treeview with UI elements for aspect ratio & screen."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        aspect_ratio = self.aspect_ratio_var.get()
        current_screen = self.screen_var.get()
        show_all = self.show_all_var.get()

        registry = ASPECT_RATIO_REGISTRIES.get(aspect_ratio, {})

        for name, loc in sorted(registry.items()):
            if not show_all and loc.screen != current_screen:
                continue

            cal_str = "Yes" if loc.calibrated else "No"
            x, y, w, h = get_location(
                name, self.image_width, self.image_height, aspect_ratio
            )
            coords_str = f"({x}, {y}, {w}, {h})"
            self.tree.insert(
                "",
                tk.END,
                values=(name, loc.screen, cal_str, coords_str),
                tags=(name,),
            )

    def redraw(self) -> None:
        """Redraw image and bounding boxes on the canvas."""
        if not self.original_image or not self.tk_image:
            return

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

        aspect_ratio = self.aspect_ratio_var.get()
        current_screen = self.screen_var.get()
        show_all = self.show_all_var.get()
        registry = ASPECT_RATIO_REGISTRIES.get(aspect_ratio, {})

        selected_items = self.tree.selection()
        selected_names = []
        for item in selected_items:
            vals = self.tree.item(item, "values")
            if vals:
                selected_names.append(vals[0])

        for name, loc in registry.items():
            if not show_all and loc.screen != current_screen:
                if name not in selected_names:
                    continue

            x, y, w, h = get_location(
                name, self.image_width, self.image_height, aspect_ratio
            )
            color = (
                "#00FF00" if loc.calibrated else "#FFA500"
            )  # Green / Orange
            if name in selected_names:
                color = "#00FFFF"  # Cyan for selected

            if w > 0 and h > 0:
                self.canvas.create_rectangle(
                    x, y, x + w, y + h, outline=color, width=3, tags=("box", name)
                )
                self.canvas.create_text(
                    x + 5,
                    y + 5,
                    anchor=tk.NW,
                    text=name,
                    fill=color,
                    font=("Arial", 10, "bold"),
                    tags=("text", name),
                )
            else:
                r = 6
                self.canvas.create_oval(
                    x - r,
                    y - r,
                    x + r,
                    y + r,
                    outline=color,
                    fill=color,
                    width=2,
                    tags=("point", name),
                )
                self.canvas.create_text(
                    x + r + 4,
                    y,
                    anchor=tk.W,
                    text=name,
                    fill=color,
                    font=("Arial", 10, "bold"),
                    tags=("text", name),
                )

    def on_element_select(self, _event: tk.Event) -> None:
        """Handle selection change in the treeview."""
        self.redraw()

    def on_canvas_click(self, event: tk.Event) -> None:
        """Handle canvas clicks to select matching UI elements."""
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        aspect_ratio = self.aspect_ratio_var.get()
        registry = ASPECT_RATIO_REGISTRIES.get(aspect_ratio, {})

        for name, _loc in registry.items():
            x, y, w, h = get_location(
                name, self.image_width, self.image_height, aspect_ratio
            )
            if w == 0:
                w, h = 12, 12
                x -= 6
                y -= 6

            if x <= canvas_x <= x + w and y <= canvas_y <= y + h:
                for item in self.tree.get_children():
                    vals = self.tree.item(item, "values")
                    if vals and vals[0] == name:
                        self.tree.selection_set(item)
                        self.tree.see(item)
                        self.redraw()
                        return


def main() -> None:
    """Run the UI Inspector standalone application."""
    root = tk.Tk()
    UIInspectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
