#!/bin/bash

cd "$(dirname "$(readlink -f "$0")")" || exit 1

SESSION="obsidian-zola"

tmux has-session -t $SESSION 2>/dev/null && tmux kill-session -t $SESSION

tmux new-session -d -s $SESSION -n "zola"
tmux send-keys -t $SESSION:0 ". ./env.sh && excavation --root=build serve" C-m

tmux new-window -t $SESSION:1 -n "ide"
tmux send-keys -t $SESSION:1 "code ." C-m

tmux new-window -t $SESSION:2 -n "watch"
tmux send-keys -t $SESSION:2 ". ./env.sh && find zola -type f | entr -r ./build.sh" C-m

tmux select-window -t $SESSION:2

tmux attach -t $SESSION
