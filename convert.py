import re
from typing import Dict, List, Optional, Tuple

from utils import (
    DocLink,
    DocPath,
    Settings,
    convert_metadata_to_html,
    parse_graph,
    pp,
    raw_dir,
    site_dir,
    content_dir,
    write_settings,
)

# tag -> output directory mapping
TAG_TO_DIR = {
    'book': 'books',
    'article': 'articles',
    'philosophy': 'philosophy',
}

# section -> template mapping
SECTION_TEMPLATES = {
    'books': {
        'section': 'blog/books-section.html',
        'page': 'blog/book-review.html',
    },
    'articles': {
        'section': 'blog/articles-section.html',
        'page': 'blog/article.html',
    },
}

DEFAULT_TEMPLATES = {
    'section': 'blog/section.html',
    'page': 'blog/page.html',
}


def get_target_section(tags: List[str]) -> Optional[str]:
    """find first matching tag -> dir mapping, return None if no match"""
    if not tags:
        return None
    
    for tag in tags:
        if tag in TAG_TO_DIR:
            return TAG_TO_DIR[tag]
    
    return None


def get_templates(section: Optional[str]) -> Dict[str, str]:
    """get templates for section, fallback to defaults"""
    if section and section in SECTION_TEMPLATES:
        return SECTION_TEMPLATES[section]
    return DEFAULT_TEMPLATES


def main():
    Settings.parse_env()
    Settings.sub_file(site_dir / "config.toml")
    Settings.sub_file(site_dir / "content/_index.md")
    Settings.sub_file(site_dir / "static/js/graph.js")

    nodes: Dict[str, str] = {}
    edges: List[Tuple[str, str]] = []
    section_count = 0
    seen_sections = set()

    all_paths = list(sorted(raw_dir.glob("**/*")))

    for path in [raw_dir, *all_paths]:
        doc_path = DocPath(path)
        
        if doc_path.is_file:
            if doc_path.is_md:
                process_page(doc_path, nodes, edges, seen_sections)
            else:
                doc_path.copy()
                print(f"found resource: {doc_path.new_rel_path}")
        else:
            # skip root dir, we want custom index template
            if path == raw_dir:
                continue
            process_section(doc_path, section_count)
            section_count += 1

    pp(nodes)
    pp(edges)
    parse_graph(nodes, edges)
    write_settings()


def process_page(
    doc_path: DocPath, 
    nodes: Dict[str, str], 
    edges: List[Tuple[str, str]],
    seen_sections: set
):
    """process markdown page with tag-based routing"""
    content = doc_path.content
    print(f'content {len(content)} lines for {doc_path.page_title}')
    
    if len(content) < 2:
        print(f"skipping {doc_path} bc empty")
        return

    meta_data = doc_path.frontmatter
    tags = meta_data.get('tags', [])
    
    target_section = get_target_section(tags)
    templates = get_templates(target_section)
    
    if target_section:
        from pathlib import Path
        doc_path.new_path = content_dir / target_section / doc_path.new_path.name
        doc_path.new_rel_path = Path(target_section) / doc_path.new_path.name
        
        if target_section not in seen_sections:
            create_tag_section(target_section, templates['section'])
            seen_sections.add(target_section)
    
    if meta_data.get('graph', True):
        nodes[doc_path.abs_url] = doc_path.page_title
    
    print(f"found metadata for {doc_path.abs_url}: {meta_data}")
    print(f"  -> routing to: {doc_path.new_rel_path}")
    
    parsed_lines: List[str] = []
    links = []
    
    for line in content:
        parsed_line, linked = DocLink.parse(line, doc_path)
        links += linked
        parsed_line = re.sub(r"\\\\\s*$", r"\\\\\\\\", parsed_line)
        parsed_lines.append(parsed_line)
        
        if meta_data.get('graph', True):
            edges.extend([doc_path.edge(rel_path) for rel_path in linked])
    
    frontmatter = [
        "---",
        f'title: "{doc_path.page_title}"',
        f"date: {doc_path.modified}",
        f"updated: {doc_path.modified}",
        f"template: {templates['page']}",
        "extra:",
        f"    prerender: {links}",
        "---",
        "",
    ]
    
    doc_path.write([
        "\n".join(frontmatter),
        convert_metadata_to_html(meta_data),
        *parsed_lines
    ])
    
    print(f"found page: {doc_path.new_rel_path}")


def create_tag_section(section_name: str, template: str):
    """create _index.md for tag-based section"""
    section_path = content_dir / section_name
    section_path.mkdir(parents=True, exist_ok=True)
    
    frontmatter = [
        "---",
        f'title: "{section_name.title()}"',
        f"template: {template}",
        f"sort_by: {Settings.options['SORT_BY']}",
        "extra:",
        f"    sidebar: {section_name}",
        "---",
        "",
    ]
    
    index_path = section_path / "_index.md"
    with open(index_path, "w") as f:
        f.write("\n".join(frontmatter))
    
    print(f"created tag section: {section_name}")


def process_section(doc_path: DocPath, section_count: int):
    """process section directory"""
    frontmatter = [
        "---",
        f'title: "{doc_path.section_title}"',
        "template: blog/section.html",
        f"sort_by: {Settings.options['SORT_BY']}",
        f"weight: {section_count}",
        "extra:",
        f"    sidebar: {doc_path.section_sidebar}",
        "---",
        "",
    ]
    
    doc_path.write_to("_index.md", "\n".join(frontmatter))
    print(f"found section: {doc_path.new_rel_path}")


if __name__ == "__main__":
    main()