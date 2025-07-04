<p align="center">
  <img height="200" src="icon.png">
</p>

# obsidian-zola-minimal

A free (means better) alternative to Obsidian Publish. This repo contains an easy-to-use (read: simplistic) solution for converting an Obsidian Personal Knowledge Management System (read: bunch of random Markdowns) into a Zola site.

What's in this fork?
- Removed any mention of netlify.
- Configuration is done with enviromental variables.
- Uploaded to repo binaries are deleted, system ones are used.
- Removed any possibility to interact with website other than reading and traversing.

Credits:
* This repo was forked from [obsidian-zola-plus](https://github.com/Yarden-zamir/obsidian-zola-plus).
* Wikilink parsing is powered by [obsidian-export](https://github.com/zoni/obsidian-export).

# Setup

- Turn your Obsidian vault folder into a Git repository
- Setup environment variables as explained in `env.sh.sample`
  ```sh
  cp ./env.sh{.sample,}
  . ./env.sh
  ```

- Make sure `python` is [installed](https://www.python.org/downloads/) and in your `PATH`
  ```
  $ python --version
  Python 3.12.2
  ```

- Install required `python` packages
  ```sh
  python -m pip install -r ./requirements.txt
  ```

- Make sure `obsidian-export` is [installed](https://github.com/zoni/obsidian-export?tab=readme-ov-file#installation) and in your `PATH`

- Make sure `zola` is [installed](https://www.getzola.org/documentation/getting-started/installation/) and in your `PATH`
- Setup `zola` configuration with `config.toml` as explained in `config.toml.sample`
  ```sh
  cp ./config.toml{.sample,}
  ```

- Run `build.sh` to build static website in `public` directory

# Local Testing (Ubuntu)

- After setup steps run `zola`:
  ```sh
  zola --root=build serve
  ```

# Features

**Supported**
- Knowledge graph (you can also treat it as backlinks)
- LaTEX (powered by `KaTEX`, bye MathJAX fans 👋)
- Partial string search (powered by `elasticlunr`)
- Syntax highlighting + Fira Code!
- Customizable animations
- Navigation
- Table of content
- Typical Markdown syntax
- Strikethroughs
- Tables
- Single-line footnotes (i.e. `[^1]` in the paragraph and `[^1]: xxx` later)
- Checkboxes
- Link escaping pattern: `[Slides Demo](<Slides Demo>)`

**Unsupported**

- Non-image / note embeds (e.g. videos, audio, PDF). They will be turned into links.
- Image resizing
- Highlighting text
- Inline / Multi-line footnotes
- Mermaid Diagrams

# Gotchas
1. Do not have files with name `index.md` or `_index.md`
2. ~~Do not have files that have the same name as its subfolder (e.g. having both `.../category1.md` and `.../category1/xxx.md` is not allowed)~~ (Fixed)
3. `LANDING_PAGE` needs to be set to the slugified file name if `SLUGIFY` is turned on (e.g. to use `I am Home.md`, `LANDING_PAGE` needs to be `i-am-home`)
