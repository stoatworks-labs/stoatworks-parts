#!/bin/sh
# README pictures into this folder, from the STLs (OpenSCAD preview mode keeps colours).
set -e
cd "$(dirname "$0")"
shot() { # name view camera(tx,ty,tz,rx,ry,rz,dist)
    openscad -o "$1.png" --imgsize=1200,900 --camera="$3" --colorscheme=Tomorrow \
        -D "view=\"$2\"" preview.scad 2>/dev/null
}
shot preview_guard       part   0,0,8,55,0,25,155
shot preview_guard_back  part   0,0,8,55,0,205,155
shot preview_tower       part   -17,0,12,40,0,120,60
shot preview_fitted      fitted 0,0,0,20,0,0,140
shot preview_logo        part   -17,6,13,80,0,180,45
