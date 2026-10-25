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
shot preview_logo        part   18,-9,8,85,0,0,45
shot preview_fitted      fitted 0,0,0,20,0,0,135
# straight at the panel, orthographic, so the cable doesn't hide the power LED's slot
openscad -o preview_fitted_leds.png --imgsize=1200,900 --camera=6,-3,5,0,0,0,110 --projection=o \
    --colorscheme=Tomorrow -D 'view="fitted"' preview.scad 2>/dev/null
