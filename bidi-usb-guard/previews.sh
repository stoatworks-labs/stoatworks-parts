#!/bin/sh
# README pictures into this folder, from the STLs (OpenSCAD preview mode keeps colours).
set -e
cd "$(dirname "$0")"
shot() { # name view camera(tx,ty,tz,rx,ry,rz,dist)
    openscad -o "$1.png" --imgsize=1200,900 --camera="$3" --colorscheme=Tomorrow \
        -D "view=\"$2\"" preview.scad 2>/dev/null
}
shot preview_guard       part   0,0,8,55,0,25,150
shot preview_guard_back  part   0,0,8,55,0,205,150
shot preview_logo        part   17,-9,11,85,0,0,45
shot preview_fitted      fitted 0,0,0,20,0,0,135
shot preview_fitted_leds fitted 14,-6,3,25,0,330,70
