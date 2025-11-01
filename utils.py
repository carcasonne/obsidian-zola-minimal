import json
import math
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from inspect import getmembers, isfunction
from os import environ
from pathlib import Path
from pprint import PrettyPrinter
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import quote, unquote

from slugify import slugify
import yaml

import metadata_handlers

site_dir = Path(__file__).parent.absolute() / "build"
raw_dir = site_dir / "__vault_export"
content_dir = site_dir / "content"

# ---------------------------------------------------------------------------- #
#                                 General Utils                                #
# ---------------------------------------------------------------------------- #

def to_prerender_links(links: List[str]) -> str:
    """converts links to prerender links"""
    x = ''.join([f'<link rel="prerender" href="{link}" as="document"/>\n' for link in links])
    print(x)
    return x

pp = PrettyPrinter(indent=4, compact=False).pprint

def convert_metadata_to_html(metadata: dict) -> str:
    """convert yaml metadata to HTML depending on metadata type"""
    parsed_metadata = ""
    handlers = get_metadata_handlers()

    for metadata_key in metadata:
        if metadata_key.lower() in [name for name, _ in handlers]:
            func = [func for name, func in handlers if name.lower() == metadata_key.lower()][0]
            parsed_metadata += str(func(metadata[metadata_key])).strip().replace("\n", " ") + "\n"
    return parsed_metadata

def get_metadata_handlers():
    return [(name, func) for name, func in getmembers(metadata_handlers, isfunction) if not name.startswith("_")]

def slugify_path(path: Union[str, Path], no_suffix: bool, lowercase=False) -> Path:
    """slugifies every component of a path. no_suffix=True when path is URL or directory"""
    path = Path(str(path))
    if Settings.is_true("SLUGIFY"):
        if no_suffix:
            os_path = "/".join(slugify(item, lowercase=lowercase) for item in path.parts)
            name = ""
            suffix = ""
        else:
            os_path = "/".join(slugify(item, lowercase=lowercase) for item in str(path.parent).split("/"))
            name = ".".join(slugify(item, lowercase=lowercase) for item in path.stem.split("."))
            suffix = path.suffix

        if name != "" and suffix != "":
            return Path(os_path) / f"{name}{suffix}"
        elif suffix == "":
            return Path(os_path) / name
        else:
            return Path(os_path)
    else:
        return path

# ---------------------------------------------------------------------------- #
#                               Document Classes                               #
# ---------------------------------------------------------------------------- #

@dataclass
class DocLink:
    """internal links inside markdown [xxxx](yyyy<.md?>#zzzz)"""
    combined: str
    title: str
    url: str
    md: str
    header: str

    @classmethod
    def get_links(cls, line: str) -> List["DocLink"]:
        return [
            cls(f"[{combined})", title, url, md, header)
            for combined, title, url, md, header in re.findall(
                r"\[((.*?)\]\((?!http)(\S*?)(\.md)?(#\S+)?)\)", line
            )
            if cls.no_inner_link(combined)
        ]

    @property
    def is_md(self) -> bool:
        return self.md != ""

    @staticmethod
    def no_inner_link(item: str) -> bool:
        return re.match(r"\[.*?\]\(\S*?\)", item) is None

    def abs_url(self, doc_path: "DocPath") -> str:
        """returns absolute URL based on quoted relative URL from obsidian-export"""
        if self.url is None or self.url == "":
            print(f"empty link found: {doc_path.old_rel_path}")
            return "/404"

        try:
            new_rel_path = (
                (doc_path.new_path.parent / unquote(self.url))
                .resolve()
                .relative_to(content_dir)
            )
            new_rel_path = quote(str(slugify_path(new_rel_path, False)))
            return f"/{new_rel_path}"
        except Exception:
            print(f"invalid link found: {doc_path.old_rel_path}")
            return "/404"

    @classmethod
    def parse(cls, line: str, doc_path: "DocPath") -> Tuple[str, List[str]]:
        """parses and fixes all internal links in a line"""
        parsed = line
        linked: List[str] = []

        def decide_internal_link_format(link: "DocLink") -> Tuple[str, str]:
            abs_url = link.abs_url(doc_path)

            if any(link.title.endswith(ext) for ext in (".webm", ".mp4")):
                return abs_url, r"{{ " + f'video(url="{abs_url}", alt="{link.title}")' + r" }}"
            
            if any(link.url.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp")):
                return abs_url, f"![{link.title}]({abs_url})"

            return abs_url, r"{{ " + f'abs_url(abs="{abs_url}{link.header}", text="{link.title}")' + r" }}"

        for link in cls.get_links(line):
            abs_url, replace_with = decide_internal_link_format(link)
            parsed = parsed.replace(link.combined, replace_with)
            linked.append(abs_url)

        return parsed, linked


class DocPath:
    """any path found in exported obsidian directory - section/page/resource"""
    
    def __init__(self, path: Path, target_section: Optional[str] = None):
        """path parsing with optional section override"""
        self.old_path = path.resolve()
        self.old_rel_path = self.old_path.relative_to(raw_dir)
        new_rel_path = self.old_rel_path

        # handle sibling folder collision
        if self.is_md and (self.old_path.parent / self.old_path.stem).is_dir():
            print(f"name collision with sibling folder, renaming: {self.old_rel_path}")
            new_rel_path = self.old_rel_path.parent / (
                self.old_rel_path.stem + "-nested" + self.old_rel_path.suffix
            )

        self.new_rel_path = slugify_path(new_rel_path, not self.is_file)
        
        # apply section override if provided
        if target_section and self.is_file:
            self.new_path = content_dir / target_section / self.new_rel_path.name
            self.new_rel_path = Path(target_section) / self.new_rel_path.name
        else:
            self.new_path = content_dir / str(self.new_rel_path)
        
        print(f"new path: {self.new_path}")

    # --------------------------------- Sections --------------------------------- #

    @property
    def section_title(self) -> str:
        title = str(self.old_rel_path).replace('"', r"\"")
        return (
            title
            if (title != "" and title != ".")
            else Settings.options["ROOT_SECTION_NAME"] or "main"
        )

    @property
    def section_sidebar(self) -> str:
        sidebar = str(self.old_rel_path)
        assert Settings.options["SUBSECTION_SYMBOL"] is not None
        section_symbol = Settings.options["SUBSECTION_SYMBOL"] if sidebar.count("/") > 0 else ""
        sidebar = section_symbol + sidebar.split("/")[-1]
        print("sidebar", sidebar)
        return (
            sidebar
            if (sidebar != "" and sidebar != ".")
            else Settings.options["ROOT_SECTION_NAME"] or "main"
        )

    def write_to(self, child: str, content: Union[str, List[str]]):
        """writes content to a child path under new path"""
        new_path = self.new_path / child
        new_path.parent.mkdir(parents=True, exist_ok=True)
        with open(new_path, "w") as f:
            if isinstance(content, str):
                f.write(content)
            else:
                f.write("\n".join(content))

    # ----------------------------------- Pages ---------------------------------- #

    @property
    def page_title(self) -> str:
        title = " ".join([item for item in self.old_path.stem.split(" ")]).replace('"', r"\"")
        return title

    @property
    def is_md(self) -> bool:
        return self.is_file and self.old_path.suffix == ".md"

    @property
    def modified(self) -> datetime:
        fm = self.frontmatter
        for field in ['modified', 'date modified', 'updated']:
            if field in fm:
                val = fm[field]
                if isinstance(val, datetime):
                    return val
                # handle both 'YYYY-MM-DDTHH:MM' and 'YYYY-MM-DDTHH:MM:SS'
                try:
                    return datetime.fromisoformat(str(val))
                except ValueError:
                    # if seconds missing, append them
                    return datetime.fromisoformat(str(val) + ':00')
        return datetime.fromtimestamp(os.path.getmtime(self.old_path))

    @property
    def content(self) -> List[str]:
        """gets lines of file but ignores frontmatter"""
        with open(self.old_path, "r") as f:
            lines = f.readlines()
            if lines[0].startswith("---"):
                for i, line in enumerate(lines[1:]):
                    if line.startswith("---"):
                        return lines[i + 2:]
            return lines

    @property
    def frontmatter(self) -> Dict[str, str]:
        """gets frontmatter of file"""
        with open(self.old_path, "r") as f:
            lines = f.readlines()
            if lines[0].startswith("---"):
                for i, line in enumerate(lines[1:]):
                    if line.startswith("---"):
                        return yaml.load("".join(lines[1:i + 1]), Loader=yaml.FullLoader)
            return {}

    def write(self, content: Union[str, List[str]]):
        """writes content to new path"""
        if not isinstance(content, str):
            content = "".join(content)
        self.new_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.new_path, "w") as f:
            f.write(content)

    # --------------------------------- Resources -------------------------------- #

    @property
    def is_file(self) -> bool:
        return self.old_path.is_file()

    def copy(self):
        """copies file from old path to new path"""
        self.new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.old_path, self.new_path)

    # ----------------------------------- Graph ---------------------------------- #

    @property
    def abs_url(self) -> str:
        """returns absolute URL to the page"""
        assert self.is_md
        return quote(f"/{str(self.new_rel_path)[:-3]}")

    def edge(self, other: str) -> Tuple[str, str]:
        """gets edge from page's URL to another URL"""
        return tuple(sorted([self.abs_url, other]))


# ---------------------------------------------------------------------------- #
#                                   Settings                                   #
# ---------------------------------------------------------------------------- #

class Settings:
    options: Dict[str, Optional[str]] = {
        "SITE_URL": None,
        "SITE_TITLE": "Someone's Second 🧠",
        "TIMEZONE": "Asia/Hong_Kong",
        "REPO_URL": None,
        "LANDING_PAGE": None,
        "LANDING_TITLE": "I love obsidian-zola! 💖",
        "SITE_TITLE_TAB": "",
        "LANDING_DESCRIPTION": "I have nothing but intelligence.",
        "LANDING_BUTTON": "Click to steal some👆",
        "SORT_BY": "title",
        "SLUGIFY": "y",
        "HOME_GRAPH": "y",
        "PAGE_GRAPH": "y",
        "SUBSECTION_SYMBOL": "<div class='folder'><svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'><path d='M448 96h-172.1L226.7 50.75C214.7 38.74 198.5 32 181.5 32H64C28.65 32 0 60.66 0 96v320c0 35.34 28.65 64 64 64h384c35.35 0 64-28.66 64-64V160C512 124.7 483.3 96 448 96zM64 80h117.5c4.273 0 8.293 1.664 11.31 4.688L256 144h192c8.822 0 16 7.176 16 16v32h-416V96C48 87.18 55.18 80 64 80zM448 432H64c-8.822 0-16-7.176-16-16V240h416V416C464 424.8 456.8 432 448 432z' /></svg></div>",
        "LOCAL_GRAPH": "",
        "GRAPH_LINK_REPLACE": "",
        "STRICT_LINE_BREAKS": "",
        "SIDEBAR_COLLAPSED": "",
        "ROOT_SECTION_NAME": "main",
        "GRAPH_OPTIONS": """
        {
            nodes: {
                shape: "box",
                color: {
                    background: "rgba(19, 26, 26, 0.3)",
                    border: "#40a088"
                },
                font: {
                    face: "Berkeley Mono, monospace",
                    color: "#ffffff",
                    strokeWidth: 0,
                },
                scaling: {
                    label: {
                        enabled: true,
                    },
                },
                shapeProperties: {
                    borderRadius: 2
                }
            },
            edges: {
                color: {
                    color: "#7a8a94",
                    highlight: "#40a088"
                },
                width: 1.5,
                smooth: {
                    type: "continuous",
                },
                hoverWidth: 3,
            },
            interaction: {
                hover: true,
            },
            height: "100%",
            width: "100%",
            physics: {
                solver: "repulsion",
            },
        }
        """,
    }

    @classmethod
    def is_true(cls, key: str) -> bool:
        val = cls.options[key]
        if not val:
            return False
        return val.lower() in ('true', '1', 'yes', 'y', 'on')

    @classmethod
    def parse_env(cls):
        for key in cls.options.keys():
            required = cls.options[key] is None
            if key in environ:
                cls.options[key] = environ[key]
            else:
                if required:
                    raise Exception(f"FATAL ERROR: build.environment.{key} not set!")
        if cls.options["SITE_TITLE_TAB"] == "":
            cls.options["SITE_TITLE_TAB"] = cls.options["SITE_TITLE"]
        print("Options:")
        pp(cls.options)

    @classmethod
    def sub_line(cls, line: str) -> str:
        for key, val in cls.options.items():
            line = line.replace(f"___{key}___", val if val else "")
        return line

    @classmethod
    def sub_file(cls, path: Path):
        content = "".join([cls.sub_line(line) for line in open(path, "r").readlines()])
        open(path, "w").write(content)


# ---------------------------------------------------------------------------- #
#                                Knowledge Graph                               #
# ---------------------------------------------------------------------------- #

LAINCHAN_COLORS = [
    "#00aeff", "#40a088", "#bd00ff", "#c7e6d7",
    "#7a8a94", "#18635d", "#e8f5f0", "#a0a0a0",
]

def parse_graph(nodes: Dict[str, str], edges: List[Tuple[str, str]]):
    node_ids = {k: i for i, k in enumerate(nodes.keys())}
    existing_edges = [
        edge for edge in set(edges) if edge[0] in node_ids and edge[1] in node_ids
    ]
    edge_counts = {k: 0 for k in nodes.keys()}
    for i, j in existing_edges:
        edge_counts[i] += 1
        edge_counts[j] += 1

    base_url = Settings.options['SITE_URL']
    non_root_start = base_url.find('/')
    non_root_part = base_url[non_root_start:] if non_root_start != -1 else ''
    
    graph_info = {
        "nodes": [
            {
                "id": node_ids[url],
                "label": title,
                "url": url,
                "root_url": non_root_part + url,
                "color": {
                    "background": "rgba(19, 26, 26, 0.3)",
                    "border": LAINCHAN_COLORS[idx % len(LAINCHAN_COLORS)],
                    "highlight": {
                        "background": "rgba(24, 99, 93, 0.4)",
                        "color": "#0b0f12"
                    }
                },
                "font": {
                    "color": "#ffffff",
                    "highlight": {"color": "#0b0f12"}
                },
                "value": math.log10(edge_counts[url] + 1) + 1,
            }
            for idx, (url, title) in enumerate(nodes.items())
        ],
        "edges": [
            {"from": node_ids[edge[0]], "to": node_ids[edge[1]]}
            for edge in set(edges)
            if edge[0] in node_ids and edge[1] in node_ids
        ],
    }
    graph_info = json.dumps(graph_info)

    with open(site_dir / "static/js/graph_info.js", "w") as f:
        is_local = "true" if Settings.is_true("LOCAL_GRAPH") else "false"
        link_replace = "true" if Settings.is_true("GRAPH_LINK_REPLACE") else "false"
        f.write("\n".join([
            f"var graph_data={graph_info}",
            f"var graph_is_local={is_local}",
            f"var graph_link_replace={link_replace}",
        ]))

def write_settings():
    with open(site_dir / "static/js/settings.js", "w") as f:
        sidebar_collapsed = "true" if Settings.is_true("SIDEBAR_COLLAPSED") else "false"
        f.write(f"var sidebar_collapsed={sidebar_collapsed}")