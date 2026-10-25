# Stoatworks parts

> **AI-assisted project.** This codebase was created with Claude (Anthropic), directed and reviewed by a human author.

Printed guards and clamps for the little video converters that live at the end of a
cable run, held on by nothing but their own connectors. Each one stops a lead from
levering the socket it's plugged into, which is how these converters usually die: not
from anything clever, just from being swung about by their power lead.

Every part has a page on the website with fitting steps, renders and a 3D view:
<https://stoatworks-labs.com/parts/>. The labels on my converters carry a QR code to
the same pages.

| Part | Fits | Status | |
|---|---|---|---|
| [BiDi USB guard](bidi-usb-guard/) | Blackmagic Design Micro Converter BiDirectional SDI/HDMI 3G, SDI end | v0.1, test-fitted | [page](https://stoatworks-labs.com/parts/bidi-usb-guard/) |
| [BiDi micro-USB guard](bidi-microusb-guard/) | Blackmagic Design Micro Converter BiDirectional SDI/HDMI, the micro-USB model, SDI end | v0.1, not yet fitted | [page](https://stoatworks-labs.com/parts/bidi-microusb-guard/) |
| [Micro Converter USB guard](micro-converter-usb-guard/) | Blackmagic Design Micro Converter SDI to HDMI and HDMI to SDI, 3G and 12G, HDMI end | v0.1, not yet fitted | [page](https://stoatworks-labs.com/parts/micro-converter-usb-guard/) |
| [Micro Converter micro-USB guard](micro-converter-microusb/) | Blackmagic Design Micro Converter SDI to HDMI and HDMI to SDI, the micro-USB models, HDMI end | v0.1, not yet fitted | [page](https://stoatworks-labs.com/parts/micro-converter-microusb/) |
| [IP Mini HDMI clamp](ip-mini-hdmi-clamp/) | Blackmagic Design 2110 IP Mini IP to HDMI, and its SFP model, HDMI end | v0.1, not yet fitted | [page](https://stoatworks-labs.com/parts/ip-mini-hdmi-clamp/) |
| [Mini Converter power guard](mini-converter-power-guard/) | Blackmagic Design Mini Converter SDI Distribution, SDI Distribution 4K and Sync Generator, Power end | v0.1, not yet fitted | [page](https://stoatworks-labs.com/parts/mini-converter-power-guard/) |
| [Mini Converter power clamp](mini-converter-power-clamp/) | Blackmagic Design Mini Converter SDI Distribution, SDI Distribution 4K and Sync Generator, Power end | v0.1, not yet fitted | [page](https://stoatworks-labs.com/parts/mini-converter-power-clamp/) |
| [Decimator USB guard](decimator-usb-guard/) | Decimator Design Decimator MD-LX, SDI end | v0.1, test-fitted | [page](https://stoatworks-labs.com/parts/decimator-usb-guard/) |
| [Decimator micro-USB guard](decimator-microusb-guard/) | Decimator Design Decimator MD-LX, the micro-USB model, SDI end | v0.1, not yet fitted | [page](https://stoatworks-labs.com/parts/decimator-microusb-guard/) |

"Not yet fitted" means just that: modelled and checked in software, never on a real
converter. Each part's README says what has and hasn't been checked. If you print one
and it doesn't fit, tell me and I'll fix it.

## What's in each folder

- `<name>.scad`: the model, in OpenSCAD. Every dimension is a named variable at the top.
- `<name>_vX.stl`: the whole part, for a one-colour print.
- `<name>_vX-body.stl` and `-logo.stl`: the same part split for a two-colour print. Load
  both as one object and give the logo its own filament.
- `stoatworks_mark.scad`: the mark, generated. Leave it as it is.
- `check.py`, `preview.scad`, `previews.sh`: the checks and the renders. `check.py` needs
  the packages in [`requirements.txt`](requirements.txt). A couple of them can also
  compare against the downloaded part the fit was first measured from, which isn't mine
  to redistribute, so it isn't here and they skip that comparison without it.
- `README.md`: fitting, printing, what's been checked, and where the numbers came from.

## Licence

Everything in this repo is licensed under
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0](LICENSE) (CC BY-NC-SA 4.0).
In short: print them, change them and share them, as long as you credit Stoatworks Labs,
don't sell them or prints of them, and share anything you make from them under the same
licence. The [legal code](LICENSE) is what counts, not this paragraph.

That's different from the rest of my repos, which are MIT. I'm going to sell printed ones,
and this keeps that to me while leaving them free for anyone to print their own. If you
want to sell them, ask.
