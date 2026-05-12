# tkblocks

A scrollable, collapsible section-based content renderer for tkinter.

Ever found yourself almost ready to ship a tk app and having to deal with more code just to include a plain FAQ?
Deal with it no more.

tkblocks is a simple tkinter implementation, tested and predictable.
Import tkblocks
Pass a notebook tab or plain frame.
Provide content with json, yaml, toml or directly through python API (*example below).
This package will handle the rendering and comply with master theme/style.

Usefull for:

Changelogs / release notes
FAQ panels
Settings/help dialogs
Onboarding flows
Dashboards with collapsible data sections
Debug/log viewers

## Installation

```bash
pip install tkblocks
```

Optional dependencies based on content types used:

```bash
pip install pyyaml    # for .yaml/.yml content files
pip install requests  # for WebImageContent
```

## Usage

### Python API

```python
from tkblocks import Blocks, SectionData, TextContent, LinkContent, LocalImageContent

sections = [
    SectionData(
        title="Getting Started",
        contents=[
            TextContent(text="Welcome to the app."),
            LinkContent(text="Documentation", url="https://example.com"),
        ],
    ),
    SectionData(
        title="Resources",
        contents=[
            LocalImageContent(text="Overview", path="media/overview.png"),
        ],
    ),
]

blocks = Blocks(parent, sections_data=sections, title="📖 User Guide")
blocks.pack(fill="both", expand=True)
```

### Loading from file

```python
from tkblocks import Blocks, load_sections

blocks = Blocks(parent, sections_data=load_sections("guide.toml"), title="📖 User Guide")
blocks.pack(fill="both", expand=True)
```

Supported formats: `.json`, `.yaml`, `.yml`, `.toml`

### Example TOML file

```toml
[[sections]]
title = "Getting Started"

[[sections.contents]]
type = "text"
text = """
Welcome to the app.
This is a multiline description.
"""

[[sections.contents]]
type = "link"
text = "Documentation"
url = "https://example.com"

[[sections]]
title = "Resources"

[[sections.contents]]
type = "local_image"
text = "Overview diagram"
path = "media/overview.png"
```

## Importing

Always import from the top-level package:
```python
from tkblocks import Blocks, load_sections  # ✅
from tkblocks.blocks import Blocks          # ❌ not guaranteed stable
```

## Content block types

| Type | Class | Required fields |
|---|---|---|
| Plain text | `TextContent` | `text` |
| Copyable text | `CopyableContent` | `text` |
| Hyperlink | `LinkContent` | `text`, `url` |
| Local image | `LocalImageContent` | `path` |
| Web image | `WebImageContent` | `url` |

## Requirements

- Python >= 3.11
- Pillow
- Pydantic

## License

Apache 2.0 — see [LICENSE](LICENSE) for details.