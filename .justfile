watch-docs:
    sphinx-autobuild docs/source docs/build/html --open-browser --watch src --watch docs/source --delay 2

docs:
    cd docs && make clean html

examples:
    make clean examples

# updates version number, commits and tags
release FIRST-BUMP *ARGS:
    #!/usr/bin/env bash
    set -e pipefail
    echo "checking for unstaged changes..."
    (test -z "$(git status --porcelain)" && echo "ok: no unstaged changes") || (echo "error: found unstaged changes" && false)
    uv version --bump {{FIRST-BUMP}} {{ARGS}}
    git add uv.lock pyproject.toml
    git commit
    git tag $(uv version --short)
