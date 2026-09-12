"""Standalone UI Inspector application for MTGA Registrar.

Provides a lightweight tkinter GUI to visualize and inspect UI element locations
defined in [`src/core/ui_locations.py`](src/core/ui_locations.py) overlaid on screen screenshots
by aspect ratio and screen classification, with interactive move/resize drag handlers
and manual property editing.
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
    update_location,
)


class UIInspectorApp:
    """Tkinter application for inspecting and editing UI element bounding boxes on images."""

    def __init__(self, root: tk.Tk) -> None:
        """Initialize the UI Inspector application.

        Args:
            root: Root tkinter window.
        """
        self.root = root
        self.root.title("MTGA Registrar - UI Location Inspector & Editor")
        self.root.geometry("1250x900")

        self.aspect_ratio_var = tk.StringVar(value="16:10")
        self.screen_var = tk.StringVar(value=AVAILABLE_SCREENS[0])
        self.show_all_var = tk.BooleanVar(value=False)

        self.original_image: Optional[Image.Image] = None
        self.tk_image: Optional[ImageTk.PhotoImage] = None
        self.image_width = 0
        self.image_height = 0

        self.selected_element: Optional[str] = None
        self.dragging_mode: Optional[str] = None  # "move" or "resize"
        self.drag_start_x: float = 0.0
        self.drag_start_y: float = 0.0
        self.orig_x = 0
        self.orig_y = 0
        self.orig_w = 0
        self.orig_h = 0

        self.edit_x_var = tk.IntVar(value=0)
        self.edit_y_var = tk.IntVar(value=0)
        self.edit_w_var = tk.IntVar(value=0)
        self.edit_h_var = tk.IntVar(value=0)
        self.edit_cal_var = tk.BooleanVar(value=True)

        self.create_widgets()
        self.load_image_and_redraw()

    def create_widgets(self) -> None:
        """Create GUI widgets (controls, canvas, element list, property editor)."""
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
        canvas_frame = ttk.LabelFrame(
            content_frame,
            text="UI Preview (Drag body to move, drag BR handle to resize)",
            padding=5,
        )
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

        self.canvas.bind("<Button-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Right side: Elements registry viewer & property editor
        right_frame = ttk.LabelFrame(
            content_frame, text="Registered UI Elements", padding=5, width=380
        )
        right_frame.pack_propagate(False)
        right_frame.pack(
            side=tk.RIGHT, fill=tk.BOTH, expand=False
        )

        columns = ("name", "screen", "calibrated", "coords")
        self.tree = ttk.Treeview(
            right_frame, columns=columns, show="headings", height=14
        )
        self.tree.heading("name", text="Element")
        self.tree.heading("screen", text="Screen")
        self.tree.heading("calibrated", text="Cal.")
        self.tree.heading("coords", text="X, Y, W, H")
        self.tree.column("name", width=110)
        self.tree.column("screen", width=90)
        self.tree.column("calibrated", width=35, anchor=tk.CENTER)
        self.tree.column("coords", width=115)
        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5))

        self.tree.bind("<<TreeviewSelect>>", self.on_element_select)

        # Property Editor Frame
        editor_frame = ttk.LabelFrame(
            right_frame, text="Element Editor & Persistence", padding=8
        )
        editor_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        ttk.Label(
            editor_frame, text="X:"
        ).grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        ttk.Entry(
            editor_frame, textvariable=self.edit_x_var, width=8
        ).grid(row=0, column=1, padx=2, pady=2)

        ttk.Label(
            editor_frame, text="Y:"
        ).grid(row=0, column=2, sticky=tk.W, padx=2, pady=2)
        ttk.Entry(
            editor_frame, textvariable=self.edit_y_var, width=8
        ).grid(row=0, column=3, padx=2, pady=2)

        ttk.Label(
            editor_frame, text="Width:"
        ).grid(row=1, column=0, sticky=tk.W, padx=2, pady=2)
        ttk.Entry(
            editor_frame, textvariable=self.edit_w_var, width=8
        ).grid(row=1, column=1, padx=2, pady=2)

        ttk.Label(
            editor_frame, text="Height:"
        ).grid(row=1, column=2, sticky=tk.W, padx=2, pady=2)
        ttk.Entry(
            editor_frame, textvariable=self.edit_h_var, width=8
        ).grid(row=1, column=3, padx=2, pady=2)

        ttk.Checkbutton(
            editor_frame, text="Calibrated", variable=self.edit_cal_var
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=2, pady=5)

        save_btn = ttk.Button(
            editor_frame, text="Save & Persist", command=self.save_manual_edit
        )
        save_btn.grid(row=2, column=2, columnspan=2, sticky=tk.E, padx=2, pady=5)

        info_text = (
            "Tip: Select element, drag box to move, "
            "or drag BR handle to resize.\n"
            "Saves to config/ui_locations.json."
        )
        info_label = ttk.Label(
            right_frame,
            text=info_text,
            wraplength=360,
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
        selected_name = self.selected_element
        for item in self.tree.get_children():
            self.tree.delete(item)

        aspect_ratio = self.aspect_ratio_var.get()
        current_screen = self.screen_var.get()
        show_all = self.show_all_var.get()

        registry = ASPECT_RATIO_REGISTRIES.get(aspect_ratio, {})

        item_to_select = None
        for name, loc in sorted(registry.items()):
            if not show_all and loc.screen != current_screen:
                continue

            cal_str = "Yes" if loc.calibrated else "No"
            x, y, w, h = get_location(
                name, self.image_width, self.image_height, aspect_ratio
            )
            coords_str = f"({x}, {y}, {w}, {h})"
            item_id = self.tree.insert(
                "",
                tk.END,
                values=(name, loc.screen, cal_str, coords_str),
                tags=(name,),
            )
            if name == selected_name:
                item_to_select = item_id

        if item_to_select:
            self.tree.selection_set(item_to_select)
            self.tree.see(item_to_select)

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

        for name, loc in registry.items():
            if not show_all and loc.screen != current_screen:
                if name != self.selected_element:
                    continue

            x, y, w, h = get_location(
                name, self.image_width, self.image_height, aspect_ratio
            )
            color = (
                "#00FF00" if loc.calibrated else "#FFA500"
            )  # Green / Orange
            if name == self.selected_element:
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
                # Draw resize handle at bottom-right if selected
                if name == self.selected_element:
                    handle_size = 6
                    self.canvas.create_rectangle(
                        x + w - handle_size,
                        y + h - handle_size,
                        x + w + handle_size,
                        y + h + handle_size,
                        fill="#00FFFF",
                        outline="#FFFFFF",
                        tags=("resize_handle", name),
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
        selected_items = self.tree.selection()
        if not selected_items:
            return
        vals = self.tree.item(selected_items[0], "values")
        if not vals:
            return

        name = vals[0]
        self.selected_element = name

        aspect_ratio = self.aspect_ratio_var.get()
        x, y, w, h = get_location(
            name, self.image_width, self.image_height, aspect_ratio
        )
        registry = ASPECT_RATIO_REGISTRIES.get(aspect_ratio, {})
        loc = registry.get(name)

        self.edit_x_var.set(x)
        self.edit_y_var.set(y)
        self.edit_w_var.set(w)
        self.edit_h_var.set(h)
        if loc:
            self.edit_cal_var.set(loc.calibrated)

        self.redraw()

    def on_canvas_press(self, event: tk.Event) -> None:
        """Handle mouse press on canvas for moving or resizing boxes."""
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        aspect_ratio = self.aspect_ratio_var.get()
        registry = ASPECT_RATIO_REGISTRIES.get(aspect_ratio, {})

        # Check if clicking resize handle of selected element first
        if self.selected_element and self.selected_element in registry:
            x, y, w, h = get_location(
                self.selected_element, self.image_width, self.image_height, aspect_ratio
            )
            hs = 8
            if x + w - hs <= cx <= x + w + hs and y + h - hs <= cy <= y + h + hs:
                self.dragging_mode = "resize"
                self.drag_start_x = cx
                self.drag_start_y = cy
                self.orig_x = x
                self.orig_y = y
                self.orig_w = w
                self.orig_h = h
                return

        # Check if clicking any element box/point
        for name, _loc in registry.items():
            x, y, w, h = get_location(
                name, self.image_width, self.image_height, aspect_ratio
            )
            if w == 0:
                w, h = 16, 16
                x -= 8
                y -= 8

            if x <= cx <= x + w and y <= cy <= y + h:
                self.selected_element = name
                # Select in treeview
                for item in self.tree.get_children():
                    vals = self.tree.item(item, "values")
                    if vals and vals[0] == name:
                        self.tree.selection_set(item)
                        self.tree.see(item)
                        break

                self.dragging_mode = "move"
                self.drag_start_x = cx
                self.drag_start_y = cy
                self.orig_x = x
                self.orig_y = y
                self.orig_w = w
                self.orig_h = h

                self.edit_x_var.set(x)
                self.edit_y_var.set(y)
                self.edit_w_var.set(w)
                self.edit_h_var.set(h)
                if _loc:
                    self.edit_cal_var.set(_loc.calibrated)

                self.redraw()
                return

        # Clicked empty space
        self.selected_element = None
        self.tree.selection_remove(self.tree.selection())
        self.dragging_mode = None
        self.redraw()

    def on_canvas_drag(self, event: tk.Event) -> None:
        """Handle dragging for moving or resizing the selected element."""
        if not self.selected_element or not self.dragging_mode:
            return

        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        dx = cx - self.drag_start_x
        dy = cy - self.drag_start_y

        aspect_ratio = self.aspect_ratio_var.get()
        registry = ASPECT_RATIO_REGISTRIES.get(aspect_ratio, {})
        if self.selected_element not in registry:
            return

        loc = registry[self.selected_element]

        if self.dragging_mode == "move":
            new_x = int(max(0, self.orig_x + dx))
            new_y = int(max(0, self.orig_y + dy))
            loc.rel_x = new_x / self.image_width if self.image_width > 0 else 0.0
            loc.rel_y = new_y / self.image_height if self.image_height > 0 else 0.0
            self.edit_x_var.set(new_x)
            self.edit_y_var.set(new_y)
        elif self.dragging_mode == "resize":
            new_w = max(5, self.orig_w + int(dx))
            new_h = max(5, self.orig_h + int(dy))
            loc.rel_width = new_w / self.image_width if self.image_width > 0 else 0.0
            loc.rel_height = new_h / self.image_height if self.image_height > 0 else 0.0
            self.edit_w_var.set(new_w)
            self.edit_h_var.set(new_h)

        loc.calibrated = True
        self.edit_cal_var.set(True)
        self.redraw()

    def on_canvas_release(self, _event: tk.Event) -> None:
        """Handle mouse release, saving changes to config/ui_locations.json."""
        if self.selected_element and self.dragging_mode:
            self.save_current_selection_to_config()
        self.dragging_mode = None

    def save_manual_edit(self) -> None:
        """Save manual edits from entry fields to config/ui_locations.json."""
        if not self.selected_element:
            messagebox.showwarning("No Selection", "Please select a UI element first.")
            return

        try:
            x = self.edit_x_var.get()
            y = self.edit_y_var.get()
            w = self.edit_w_var.get()
            h = self.edit_h_var.get()
            cal = self.edit_cal_var.get()

            rel_x = x / self.image_width if self.image_width > 0 else 0.0
            rel_y = y / self.image_height if self.image_height > 0 else 0.0
            rel_w = w / self.image_width if self.image_width > 0 else 0.0
            rel_h = h / self.image_height if self.image_height > 0 else 0.0
            aspect_ratio = self.aspect_ratio_var.get()

            update_location(
                name=self.selected_element,
                aspect_ratio=aspect_ratio,
                rel_x=rel_x,
                rel_y=rel_y,
                rel_width=rel_w,
                rel_height=rel_h,
                calibrated=cal,
            )
            self.populate_treeview()
            self.redraw()
            messagebox.showinfo(
                "Success",
                f"Updated and persisted '{self.selected_element}' "
                "to config/ui_locations.json.",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save location: {e}")

    def save_current_selection_to_config(self) -> None:
        """Persist current drag modifications to config/ui_locations.json."""
        if not self.selected_element:
            return
        aspect_ratio = self.aspect_ratio_var.get()
        registry = ASPECT_RATIO_REGISTRIES.get(aspect_ratio, {})
        loc = registry.get(self.selected_element)
        if loc:
            update_location(
                name=self.selected_element,
                aspect_ratio=aspect_ratio,
                rel_x=loc.rel_x,
                rel_y=loc.rel_y,
                rel_width=loc.rel_width,
                rel_height=loc.rel_height,
                calibrated=loc.calibrated,
            )
            self.populate_treeview()


def main() -> None:
    """Run the UI Inspector standalone application."""
    root = tk.Tk()
    UIInspectorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
