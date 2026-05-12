from pydantic import BaseModel
from typing import Literal

from PIL import Image, ImageTk
from tkinter import ttk
import tkinter as tk

from pathlib import Path
import webbrowser
import os


class TextContent(BaseModel):
    """A plain text block."""

    type: Literal["text"] = "text"
    text: str


class CopyableContent(BaseModel):
    """A copyable text block rendered with a copy-to-clipboard button."""

    type: Literal["copyable"] = "copyable"
    text: str


class LinkContent(BaseModel):
    """A clickable hyperlink block that opens in the default browser."""

    type: Literal["link"] = "link"
    text: str
    url: str


class WebImageContent(BaseModel):
    """An image block loaded from a remote URL."""

    type: Literal["web_image"] = "web_image"
    text: str = ""
    url: str


class LocalImageContent(BaseModel):
    """An image block loaded from a local file path."""

    type: Literal["local_image"] = "local_image"
    text: str = ""
    path: str


class SectionData(BaseModel):
    """A collapsible section with a title and a list of content blocks."""

    title: str
    contents: list[
        TextContent
        | CopyableContent
        | LinkContent
        | WebImageContent
        | LocalImageContent
    ]


def load_sections(source: str | Path) -> list[SectionData]:
    """
    Loads a list of SectionData from a JSON, YAML or TOML file.

    Args:
        source: Path to the content file. Format is inferred from extension.
                Supported extensions: .json, .yaml, .yml, .toml

    Returns:
        list[SectionData]

    Dependencies:
        .yaml/.yml  requires: pyyaml
        .toml       requires: tomllib (stdlib Python 3.11+) or tomli (<3.11)
        yaml and toml are lazy-imported — only required if that format is used.

    Raises:
        FileNotFoundError: if the file does not exist.
        ValueError: if the format is unsupported or the file fails to parse.
    """
    path = Path(source)
    suffix = path.suffix.lower()

    try:
        with open(path, encoding="utf-8") as f:
            if suffix == ".json":
                import json

                data = json.load(f)
            elif suffix in (".yaml", ".yml"):
                import yaml

                data = yaml.safe_load(f)
            elif suffix == ".toml":
                import tomllib

                data = tomllib.loads(f.read())
            else:
                raise ValueError(
                    f"Unsupported format: '{suffix}'. Use .json, .yaml or .toml."
                )

    except FileNotFoundError:
        raise FileNotFoundError(f"Content file not found: {path}")
    except Exception as e:
        raise ValueError(f"Failed to parse '{path.name}': {e}")

    return [SectionData.model_validate(section) for section in data]


class CollapsibleSection(tk.Frame):
    """A toggleable section widget with a header button and collapsible content frame."""

    def __init__(self, parent, title, **kwargs):
        super().__init__(parent, **kwargs)
        self.expanded = False

        # Toggle button as header
        self.toggle_btn = tk.Button(
            self,
            text=f"▶  {title}",
            anchor="w",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            command=self.toggle,
        )
        self.toggle_btn.pack(fill="x", ipady=6)

        # Content frame (hidden by default)
        self.content = tk.Frame(self, padx=16, pady=8)

    def toggle(self):
        """Toggle the visibility of the section content frame."""
        if self.expanded:
            self.content.pack_forget()
            title = self.toggle_btn["text"].replace("▼", "▶")
        else:
            self.content.pack(fill="x")
            title = self.toggle_btn["text"].replace("▶", "▼")
        self.toggle_btn.config(text=title)
        self.expanded = not self.expanded

    def add_text(self, text):
        """Render a plain text label. Wraplength adjusts dynamically on resize."""
        lbl = tk.Label(
            self.content,
            text=text,
            wraplength=800,
            justify="left",
            anchor="w",
        )
        lbl.pack(fill="x", pady=2)
        # Update wraplength dynamically on resize
        lbl.bind("<Configure>", lambda e: lbl.config(wraplength=e.width))

    def add_link(self, text, url):
        """Render a clickable hyperlink label that opens url in the default browser."""
        link = tk.Label(
            self.content,
            text=text,
            fg="#59b0fd",
            font=("TkDefaultFont", 9),
            cursor="hand2",
            anchor="w",
        )
        link.pack(anchor="w")
        link.bind("<Button-1>", lambda e: webbrowser.open(url))
        link.bind(
            "<Enter>", lambda e: link.config(font=("TkDefaultFont", 9, "underline"))
        )
        link.bind("<Leave>", lambda e: link.config(font=("TkDefaultFont", 9)))

    def add_web_image(self, text: str, url: str, width=None):
        """
        Downloads and displays an image from a URL.
        Optionally resizes to a given width while preserving aspect ratio.
        Supports PNG, JPG, BMP, TIFF, WebP (requires Pillow).
        Note: SVG format is not supported.
        """
        # text is intentionally rendered even when empty — acts as visual separator.
        self.add_text(text=text)

        try:
            import requests
            from io import BytesIO

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))

            if width:
                ratio = width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((width, new_height), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(self.content, image=photo)
            lbl.image = photo  # type: ignore
            lbl.pack(pady=(10, 25), anchor="w")

        except Exception as e:
            tk.Label(
                self.content,
                text=f"⚠ Could not load image: {e}",
                fg="red",
                anchor="w",
            ).pack(fill="x", pady=2)

    def add_local_image(self, text: str, path: str, width=None):
        """
        Loads an image from a local file path.
        Optionally resizes to a given width while preserving aspect ratio.
        Supports PNG, JPG, BMP, TIFF, WebP (requires Pillow).
        """
        # text is intentionally rendered even when empty — acts as visual separator.
        self.add_text(text=text)
        abs_path = os.path.abspath(path)

        if not os.path.isfile(abs_path):
            tk.Label(
                self.content,
                text=f"⚠ Image not found: {abs_path}",
                bg="white",
                fg="red",
                anchor="w",
            ).pack(fill="x", pady=2)
            return

        try:
            img = Image.open(abs_path)

            if width:
                ratio = width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((width, new_height), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(self.content, image=photo)
            lbl.image = photo  # type: ignore
            lbl.pack(pady=(10, 25), anchor="w")

        except Exception as e:
            tk.Label(
                self.content,
                text=f"⚠ Could not load image: {e}",
                bg="white",
                fg="red",
                anchor="w",
            ).pack(fill="x", pady=2)

    def add_copyable_text(self, text):
        """Render a read-only code block with a copy-to-clipboard button."""
        # --- Code block container ---
        block = tk.Frame(self.content, bd=1, relief="solid")
        block.pack(anchor="w", pady=(0, 6))

        # Code text (read-only, selectable)
        code_text = tk.Text(
            block,
            height=max(1, text.count("\n") + 1),  # auto-height
            wrap="none",
            font=("Consolas", 9),
            relief="flat",
            padx=8,
            pady=6,
            state="normal",
            cursor="arrow",
            width=max([len(part) for part in text.split(" \n")]),
        )
        code_text.insert("1.0", text)
        code_text.config(state="disabled")
        code_text.pack(side="left")

        # --- Copy button ---
        def copy_to_clipboard():
            self.content.clipboard_clear()
            self.content.clipboard_append(text)
            self.content.update()
            copy_btn.config(text="✔ Copied!", bg="#71cd74")
            self.content.after(2000, lambda: copy_btn.config(text="Copy", bg="#535353"))

        copy_btn = tk.Button(
            block,
            text="Copy",
            command=copy_to_clipboard,
            font=("Segoe UI", 9),
            bg="#535353",
            relief="flat",
            padx=10,
            cursor="hand2",
            activebackground="#606060",
        )
        copy_btn.pack(side="right", padx=6, pady=6, anchor="w")


class Blocks(ttk.Frame):
    """
    A scrollable, collapsible section-based content renderer for tkinter.
    Accepts a list of SectionData and renders each as a CollapsibleSection.
    """

    def __init__(self, parent, sections_data: list[SectionData], title="", **kwargs):
        super().__init__(parent, **kwargs)

        # --- Scrollable canvas setup ---
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_resize(event):
            canvas.itemconfig(window_id, width=event.width)

        canvas.bind("<Configure>", on_resize)

        def on_frame_configure(*_):
            canvas.configure(scrollregion=canvas.bbox("all"))

        inner.bind("<Configure>", on_frame_configure)

        def on_mousewheel(event):
            x, y = self.winfo_pointerxy()
            widget_under_cursor = self.winfo_containing(x, y)
            if widget_under_cursor and str(widget_under_cursor).startswith(str(self)):
                if canvas.yview() != (0.0, 1.0):
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                # "break" prevents the event reaching parent scrollable containers.
                return "break"

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Title
        if title:
            tk.Label(
                inner,
                text=title,
                font=("Segoe UI", 14, "bold"),
                pady=12,
            ).pack(fill="x", padx=16)

        # Sections
        dispatch = {
            TextContent: lambda c: section.add_text(c.text),
            CopyableContent: lambda c: section.add_copyable_text(c.text),
            LinkContent: lambda c: section.add_link(c.text, c.url),
            LocalImageContent: lambda c: section.add_local_image(c.text, c.path),
            WebImageContent: lambda c: section.add_web_image(c.text, c.url),
        }
        for section_data in sections_data:
            section = CollapsibleSection(inner, title=section_data.title, pady=2)
            section.pack(fill="x", padx=16, pady=3)

            # Section contents
            for content_data in section_data.contents:
                dispatch[type(content_data)](content_data)

        # Handle destroyed event
        self.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))
