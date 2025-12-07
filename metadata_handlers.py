"""
Metadata handlers: dump everything except tags into frontmatter extra.
tags handled separately bc routing logic, everything else just goes through.
"""

SKIP_FIELDS = {'created', 'modified', 'title'}  # handled elsewhere

def get_frontmatter_extras(metadata: dict) -> dict:
    return {
        key.replace('-', '_'): str(value).strip() if not isinstance(value, list) else value
        for key, value in metadata.items() 
        if key not in SKIP_FIELDS
    }

def get_meta_tags(metadata: dict) -> str:
    """maybe keep some as meta tags for seo? idk you decide"""
    output = []
    
    # only these stay as meta tags
    if 'modified' in metadata:
        output.append(f'<meta property="article:modified_time" content="{metadata["modified"]}"/>')
    
    if 'tags' in metadata:
        for tag in metadata['tags']:
            output.append(f'<meta name="tag" content="{tag}"/>')
    
    return '\n'.join(output)