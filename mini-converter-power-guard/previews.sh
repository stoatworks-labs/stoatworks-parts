#!/bin/sh
# README pictures into this folder, from the STLs (OpenSCAD preview mode keeps colours).
set -e
cd "$(dirname "$0")"
shot() { # name view model camera(tx,ty,tz,rx,ry,rz,dist) [extra -D options]
    name=$1 view=$2 model=$3 camera=$4; shift 4
    openscad -o "$name.png" --imgsize=1200,900 --camera="$camera" --colorscheme=Tomorrow \
        -D "view=\"$view\"" -D "model=\"$model\"" "$@" preview.scad 2>/dev/null
}
shot preview_guard        part   da   46,-5,10,60,0,25,250
shot preview_guard_back   part   da   46,-5,10,60,0,205,250
shot preview_fitted_da    fitted da   46,0,8,55,0,20,330
shot preview_fitted_sync  fitted sync 46,0,8,55,0,20,330
shot preview_fitted_tie   fitted sync 6,-24,11,55,0,-30,110

# The bnc_holes option, for the Sync Generator at the BNC height in the .scad: its
# STLs are rendered into a scratch folder, since they are only for printing once
# bnc_y has been measured.
tmp=$(mktemp -d)
for p in body logo; do
    openscad -o "$tmp/holes-$p.stl" -D "part=\"$p\"" -D bnc_holes=true -D 'model="sync"' \
        mini_converter_power_guard.scad 2>/dev/null
done
shot preview_holes_sync   fitted sync 46,0,8,55,0,20,330 -D bnc_holes=true -D "stl=\"$tmp/holes\""
rm -r "$tmp"
