watch-docs:
    sphinx-autobuild docs/source docs/build/html --open-browser --watch src --watch docs/source --delay 2

docs:
    cd docs && make clean html

examples:
    make clean examples

# updates version number, commits EVERY FILE and tags
commit-as-release FIRST-BUMP *ARGS:
    #!/usr/bin/env bash
    set -e pipefail
    uv version --bump {{FIRST-BUMP}} {{ARGS}}
    git add --all
    git commit
    git tag v$(uv version --short)

# updates version number, commits and tags
release FIRST-BUMP *ARGS:
    #!/usr/bin/env bash
    set -e pipefail
    echo "checking for unstaged changes..."
    (test -z "$(git status --porcelain)" && echo "ok: no unstaged changes") || (echo "error: found unstaged changes" && false)
    uv version --bump {{FIRST-BUMP}} {{ARGS}}
    git add uv.lock pyproject.toml
    git commit
    git tag v$(uv version --short)
