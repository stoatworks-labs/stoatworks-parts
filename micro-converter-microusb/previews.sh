#!/bin/sh
# README pictures into this folder, from the STLs (OpenSCAD preview mode keeps colours).
set -e
cd "$(dirname "$0")"
shot() { # name view camera(tx,ty,tz,rx,ry,rz,dist)
    openscad -o "$1.png" --imgsize=1200,900 --camera="$3" --colorscheme=Tomorrow \
        -D "view=\"$2\"" preview.scad 2>/dev/null
}
shot preview_guard       part   0,-5,12,60,0,-35,170
shot preview_guard_back  part   0,-5,12,60,0,145,170
shot preview_fitted      fitted 0,-14,10,62,0,35,200
shot preview_fitted_led  fitted 18.3,0.8,8.5,87,0,20,70
shot preview_fitted_side fitted 0,8,12,78,0,-90,160
