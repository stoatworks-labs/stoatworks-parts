#!/bin/sh
# README pictures into this folder, from the STLs (OpenSCAD preview mode keeps colours).
set -e
cd "$(dirname "$0")"
shot() { # name view camera(tx,ty,tz,rx,ry,rz,dist)
    openscad -o "$1.png" --imgsize=1200,900 --camera="$3" --colorscheme=Tomorrow \
        -D "view=\"$2\"" preview.scad 2>/dev/null
}
shot preview_clamp       part   8,-10,10,60,0,-40,230
shot preview_clamp_back  part   8,-10,10,60,0,140,230
shot preview_fitted      fitted 25,0,8,52,0,32,330
shot preview_fitted_tie  fitted 10,-44,11,50,0,40,90
shot preview_fitted_side fitted 10,14,11,82,0,-90,330
