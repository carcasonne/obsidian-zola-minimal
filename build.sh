#!/bin/bash

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

if [ -d "venv" ]; then
    PYTHON="venv/bin/python"
elif [ -d ".venv" ]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python"
fi

echo "${VAULT:?}"
echo "${SITE_URL:?}"
echo "${REPO_URL:?}"
echo "${LANDING_PAGE:?}"
echo "${PYTHON:?}"
echo "${THEME:?}"

ZOLACFG="config.toml"

if ! test -f "$ZOLACFG"; then
	if ! test -f "$VAULT/config.toml"; then
		echo "Zola configuration file not found, using default settings";
		ZOLACFG="./${ZOLACFG}.sample";
	else
		echo "Zola configuration file found in vault";
		ZOLACFG="$VAULT/config.toml";
	fi;
fi

mkdir -p build

rsync -a "$ZOLACFG" build/config.toml
rsync -a "${THEME}/" build/
rsync -a content/ build/content

# obsidian-export dumps to temp dir
mkdir -p build/__vault_export
if [ -z "$STRICT_LINE_BREAKS" ]; then
	obsidian-export --hard-linebreaks --no-recursive-embeds "$VAULT" build/__vault_export
else
	obsidian-export --no-recursive-embeds "$VAULT" build/__vault_export
fi

$PYTHON convert.py

zola --root build build "$@"