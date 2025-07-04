#!/bin/sh

die() {
	echo >&2 error: "$@"
	exit 2
}

check_prog() {
	command -v "$1" >/dev/null 2>&1 || die "program '$1' is required, but wasn't found"
}

check_prog zola
check_prog rsync
check_prog python
check_prog obsidian-export

echo "${VAULT:?}"
echo "${SITE_URL:?}"
echo "${REPO_URL:?}"
echo "${LANDING_PAGE:?}"

[ -e "./config.toml" ] || die "Zola configuration file is absent"

rsync -a config.toml build/
rsync -a zola/ build
rsync -a content/ build/content

# Use obsidian-export to export markdown content from obsidian
mkdir -p build/content/docs build/__docs
if [ -z "$STRICT_LINE_BREAKS" ]; then
	obsidian-export --frontmatter=never --hard-linebreaks --no-recursive-embeds "$VAULT" build/__docs
else
	obsidian-export --frontmatter=never --no-recursive-embeds "$VAULT" build/__docs
fi

python convert.py

zola --root build build --output-dir public
