import os
import re

# Global tracker for llms.txt files (if needed)
ALL_PAGES = []

def promote_headings_outside_fences(content):
    in_fence = False
    out = []
    for line in content.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if not in_fence:
            # Promote headings for better readability in LLMs
            line = re.sub(r'^(#{1,6})(\s+)', r'#\1\2', line)
        out.append(line)
    return "\n".join(out)

def on_pre_build(config):
    global ALL_PAGES
    ALL_PAGES = []

def on_post_page(output, page, config):
    docs_dir = config['docs_dir']
    abs_dest = page.file.abs_dest_path
    
    # Handle Directory URLs vs Direct File URLs to fix 404s
    if page.file.src_path == "index.md":
        # Root index page: index.md -> index.md
        dest_path = os.path.join(config['site_dir'], "index.md")
    elif abs_dest.endswith("index.html"):
        # Subdirectory index page: guides/index.html -> guides.md
        parent_dir = os.path.dirname(os.path.dirname(abs_dest))
        folder_name = os.path.basename(os.path.dirname(abs_dest))
        dest_path = os.path.join(parent_dir, f"{folder_name}.md")
    else:
        # Direct file: foo.html -> foo.md
        dest_path = os.path.splitext(abs_dest)[0] + ".md"

    print(f"DEBUG: Saving flattened markdown for {page.file.src_path} TO {dest_path}")

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    # For Streaming Integrator, we just use the page markdown directly 
    # as there are currently no includes or complex redoc tags.
    content = page.markdown
    content = promote_headings_outside_fences(content)
    
    with open(dest_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    rel_url = os.path.relpath(dest_path, config['site_dir'])
    if not any(p["url"] == rel_url for p in ALL_PAGES):
        ALL_PAGES.append({"title": page.title, "url": rel_url})

def on_post_build(config):
    # Optional: Generate llms.txt if required, similar to docs-is
    llms_path = os.path.join(config['site_dir'], "llms.txt")
    lines = [
        "# WSO2 Streaming Integrator Documentation",
        "> Optimized for AI agents, LLMs, and developers",
        "",
        "## Site Map",
        "- [Comprehensive file index](./llms-full.txt)"
    ]
    with open(llms_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    full_path = os.path.join(config['site_dir'], "llms-full.txt")
    full_lines = ["# WSO2 Streaming Integrator - Full Document Index", ""]
    for p in sorted(ALL_PAGES, key=lambda x: x['url']):
        full_lines.append(f"- [{p['title']}](./{p['url']})")
    with open(full_path, "w", encoding="utf-8") as f:
        f.write("\n".join(full_lines))
    print(f"SUCCESS - llms.txt and llms-full.txt generated.")
