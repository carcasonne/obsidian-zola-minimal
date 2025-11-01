"""
Metadata handlers: each function converts a metadata key into HTML for insertion in a page.
Now simplified — generates <meta> tags instead of badges.
"""

def modified(date: str) -> str:
    """Converts date into <meta> tag."""
    return f'<meta property="article:modified_time" content="{date}"/>'

def button(text: str) -> str:
    return f'<button class="button">{text}</button>'

def chips(chips_dict: dict) -> str:
    """Convert key-value dict into <meta name="key" content="value"/> entries."""
    return '\n'.join([_meta_tag(key, value) for key, value in chips_dict.items()])

def consumed(value: str) -> str:
    return _meta_tag("consumed", value)

def rating(value: str) -> str:
    return _meta_tag("rating", value)

def source(value):
    """Convert a URL or list of URLs to meta tags."""
    if isinstance(value, list):
        return '\n'.join([source(v) for v in value])
    return _meta_tag("source", value)

def aliases(list_of_aliases: list) -> str:
    return '\n'.join([_meta_tag("alias", alias) for alias in list_of_aliases])

def tags(tags_list: list) -> str:
    """Emit <meta name='tag' content='value'/> for each tag."""
    return '\n'.join([_meta_tag("tag", tag) for tag in tags_list])

# --- helpers ---

def _meta_tag(name: str, value: str) -> str:
    """Return an escaped <meta> tag."""
    name = str(name).strip()
    value = str(value).strip()
    return f'<meta name="{name}" content="{value}"/>'
