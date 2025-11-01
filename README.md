<p align="center">
  <img height="200" src="icon.png">
</p>

# obsidian-zola-minimal

A tool for converting an Obsidian vault to Zola-compatible markdown with as little tinkering as possible. Also builds the actual Zola files using the provided theme.

Includes my own custom theme (well, it is going to be my theme over time. To start of I am just using the forked theme).

This fork is a fork of `SherAndrei`'s fork. My changes, currently, are:
- Added embedded image support (no longer just a link to the ressource).
- Added python venv support by default, so you don't have to install packages to your system python.

Credits:
* This repo was forked from [obsidian-zola-plus](https://github.com/SherAndrei/obsidian-zola-minimal).
* Wikilink parsing is powered by [obsidian-export](https://github.com/zoni/obsidian-export).

# Setup

- Setup environment variables as explained in `env.sh.sample`
  ```sh
  cp ./env.sh{.sample,}
  . ./env.sh
  ```
- Setup `zola` configuration with `config.toml` as explained in `config.toml.sample`
  ```sh
  cp ./config.toml{.sample,}
  ```
- Create a python virtual environment and install the required packages:
  ```sh
  python -m venv ./venv
  source ./venv/bin/activate
  pip install -r ./requirements.txt
  ```
- Make sure `obsidian-export` is [installed](https://github.com/zoni/obsidian-export?tab=readme-ov-file#installation) and in your `PATH`

- Make sure `zola` is [installed](https://www.getzola.org/documentation/getting-started/installation/) and in your `PATH`

- Run `build.sh` to build static website in `public` directory (make sure `. ./env.sh` has been run in the same context)

# Local Testing

- After setup steps run `zola`:
  ```sh
  zola --root=build serve
  ```

## Tmux

Alternatively run the `./tmux.sh` script to launch:
1. Visual Studio Code in the current directory.
2. A Zola server hosting session
3. A session which rebuilds the project when changes happen to files in the `./zola/` directory.

Obviously needs `tmux` installed, but also `entr` for watching changes to files. I have also made this script callable from anywhere by adding it to my path via calling `oz-dev` via symlink: 

```

ln -s <path-to-file> ~/.local/bin/oz-dev

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
- Image embeds

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
