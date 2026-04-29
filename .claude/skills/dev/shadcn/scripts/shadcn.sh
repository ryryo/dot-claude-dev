#!/bin/bash
# shadcn CLI wrapper - resolves PATH for nodenv/anyenv environments
export PATH="$HOME/.anyenv/envs/nodenv/shims:$HOME/.anyenv/envs/nodenv/bin:$HOME/.nodenv/shims:$HOME/.nodenv/bin:$PATH"
exec npx shadcn@latest "$@"
