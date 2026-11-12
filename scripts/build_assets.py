#!/usr/bin/env python3
"""Generate the README's SVG assets (light + dark variants).

    python3 scripts/build_assets.py          # writes docs/assets/*.svg

Standard library only. GitHub renders README images through <img>: no scripts or web
fonts, but CSS animation, media queries and prefers-reduced-motion inside the SVG work.
Drawn at 880 px wide (the README column) so text renders close to 1:1. The palette is
shared with the maintainer's other repositories ("datasheet" palette).

Everything drawn here is illustrative: no measured number appears in any asset.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets"

SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    "light": dict(
        paper="#F7F5F0",
        paper2="#EFECE4",
        rule="#D9D4C7",
        rule2="#BDB6A6",
        ink="#15171C",
        ink2="#353A44",
        graphite="#555C6A",
        signal="#1D4ED8",
        copper="#B4470E",
        fault="#C2261D",
    ),
    "dark": dict(
        paper="#10151D",
        paper2="#171E29",
        rule="#2A3341",
        rule2="#3B4656",
        ink="#ECE8E0",
        ink2="#CFCAC0",
        graphite="#A3ABB8",
        signal="#86A8FF",
        copper="#F0935C",
        fault="#FF7D73",
    ),
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def base_css(t: dict[str, str]) -> str:
    return f"""
    .kick {{ font: 700 12.5px {MONO}; letter-spacing: .14em; fill: {t["ink"]}; }}
    .kick2 {{ font: 600 11px {MONO}; letter-spacing: .1em; fill: {t["graphite"]}; }}
    .h {{ font: 650 25px {SANS}; fill: {t["ink"]}; letter-spacing: -.014em; }}
    .sub {{ font: 500 12px {MONO}; fill: {t["ink2"]}; }}
    .cap {{ font: 600 10.5px {MONO}; fill: {t["graphite"]}; letter-spacing: .06em; }}
    .lbl {{ font: 600 11px {MONO}; fill: {t["ink"]}; }}
    .lbl2 {{ font: 500 10.5px {MONO}; fill: {t["graphite"]}; }}
    .title {{ font: 650 13px {SANS}; fill: {t["ink"]}; }}
    .box {{ fill: {t["paper2"]}; stroke: {t["rule2"]}; stroke-width: 1.2; }}
    .card {{ fill: {t["paper"]}; stroke: {t["ink"]}; stroke-width: 1.3; }}
    .wire {{ fill: none; stroke: {t["rule2"]}; stroke-width: 1.4; }}
    .ink {{ fill: none; stroke: {t["ink"]}; stroke-width: 1.4; }}
    .sig {{ fill: none; stroke: {t["signal"]}; stroke-width: 1.6; }}
    .cu {{ fill: none; stroke: {t["copper"]}; stroke-width: 1.8; }}
    .dash {{ stroke-dasharray: 4 4; }}
    .fs {{ fill: {t["signal"]}; }} .fc {{ fill: {t["copper"]}; }} .ff {{ fill: {t["fault"]}; }}
    .fg {{ fill: {t["graphite"]}; }} .fi {{ fill: {t["ink"]}; }} .fp {{ fill: {t["paper"]}; }}
    .chip {{ fill: {t["paper"]}; stroke: {t["rule2"]}; stroke-width: 1; }}
    .chipt {{ font: 600 10.5px {MONO}; fill: {t["ink2"]}; letter-spacing: .04em; }}
    """


def svg(
    w: int, h: int, title: str, desc: str, css: str, body: str, t: dict[str, str], defs: str = ""
) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d">\n'
        f'<title id="t">{esc(title)}</title>\n<desc id="d">{esc(desc)}</desc>\n'
        f"<defs>{defs}</defs>\n<style>{css}\n"
        "    @media (prefers-reduced-motion: reduce) { * { animation: none !important; } }\n"
        f'</style>\n<rect width="{w}" height="{h}" rx="12" fill="{t["paper"]}"/>\n'
        f"{body}\n</svg>\n"
    )


def text(x: float, y: float, s: str, cls: str, anchor: str = "start", extra: str = "") -> str:
    a = "" if anchor == "start" else f' text-anchor="{anchor}"'
    return f'<text x="{x}" y="{y}" class="{cls}"{a}{extra}>{esc(s)}</text>'


def chip(x: float, y: float, s: str, w: float | None = None) -> str:
    w = w or 14 + len(s) * 6.6
    return f'<rect x="{x}" y="{y}" width="{w:.0f}" height="22" rx="11" class="chip"/>' + text(
        x + w / 2, y + 15, s, "chipt", "middle"
    )


def accent_bar(t: dict[str, str], w: int) -> tuple[str, str]:
    defs = (
        '<linearGradient id="acc" x1="0" x2="1">'
        f'<stop offset="0" stop-color="{t["signal"]}"/>'
        f'<stop offset=".6" stop-color="{t["copper"]}"/>'
        f'<stop offset="1" stop-color="{t["fault"]}"/></linearGradient>'
    )
    return defs, f'<rect x="24" y="14" width="{w - 48}" height="3" rx="1.5" fill="url(#acc)"/>'


# ───────────────────────────── banner ─────────────────────────────


def banner(t: dict[str, str], w: int = 880, h: int = 300, scale_note: bool = True) -> str:
    defs, bar = accent_bar(t, w)
    cycle = 6
    css = (
        base_css(t)
        + f"""
    .slot {{ fill: {t["paper"]}; stroke: {t["rule2"]}; stroke-width: 1; }}
    .kv {{ fill: {t["copper"]}; }}
    .layer {{ fill: {t["signal"]}; }}
    .late {{ fill: {t["fault"]}; }}
    .fence {{ stroke: {t["fault"]}; stroke-width: 3; stroke-linecap: round; }}
    .rail {{ stroke: {t["rule2"]}; stroke-width: 2; }}
    """
    )
    b = [bar]
    b.append(text(32, 58, "KVWIRE", "kick"))
    b.append(text(32, 78, "RDMA KV-CACHE TRANSPORT · DISAGGREGATED INFERENCE", "kick2"))
    b.append(text(32, 124, "Move the KV cache at line rate.", "h"))
    b.append(
        '<text x="32" y="156" class="h">Stay <tspan class="fc">correct</tspan> when the '
        "wire fails.</text>"
    )
    b.append(text(32, 190, "paged · per-layer · GPUDirect RDMA", "sub"))
    b.append(text(32, 208, "→ hidden behind prefill compute", "sub"))
    b.append(text(32, 226, "→ epoch-fenced: a late write never lands", "sub"))
    x = 32
    for c in ("pre-alpha · M1", "C++20 verbs + Python", "Apache-2.0"):
        b.append(chip(x, 250, c))
        x += 14 + len(c) * 6.6 + 8

    # Prefill pool: layers computing bottom-up (signal).
    b.append('<rect x="508" y="62" width="104" height="168" rx="8" class="box"/>')
    b.append(text(518, 80, "prefill", "lbl"))
    b.append(text(518, 94, "compute", "lbl2"))
    for k in range(5):
        y = 196 - k * 20
        b.append(f'<rect x="518" y="{y}" width="84" height="13" rx="2" class="slot"/>')
        b.append(f'<rect x="518" y="{y}" width="84" height="13" rx="2" class="layer L{k}"/>')
        css += (
            f".L{k} {{ animation: L{k} {cycle}s step-end infinite; }} "
            f"@keyframes L{k} {{ 0% {{ opacity: .2; }} {8 + k * 14}% {{ opacity: 1; }} }}\n"
        )
    b.append(text(560, 222, "layer by layer", "lbl2", "middle"))

    # Decode pool: paged KV block slots filling (copper).
    b.append('<rect x="752" y="62" width="104" height="168" rx="8" class="box"/>')
    b.append(text(762, 80, "decode", "lbl"))
    b.append(text(762, 94, "paged KV", "lbl2"))
    n = 0
    for r in range(5):
        for c in range(4):
            sx, sy = 763 + c * 21, 106 + r * 23
            b.append(f'<rect x="{sx}" y="{sy}" width="17" height="17" rx="2" class="slot"/>')
            if n < 14:
                b.append(f'<rect x="{sx}" y="{sy}" width="17" height="17" rx="2" class="kv D{n}"/>')
                css += (
                    f".D{n} {{ animation: D{n} {cycle}s step-end infinite; }} "
                    f"@keyframes D{n} {{ 0% {{ opacity: .15; }} "
                    f"{10 + n * 6}% {{ opacity: 1; }} }}\n"
                )
            n += 1

    # Two rails with KV blocks in flight; a late write stopped at the fence on rail 1.
    b.append(text(682, 92, "GPUDirect RDMA", "lbl2", "middle"))
    b.append(text(682, 106, "2 rails", "lbl2", "middle"))
    for ri, y in enumerate((128, 168)):
        b.append(f'<line x1="612" y1="{y}" x2="752" y2="{y}" class="rail"/>')
        for j in range(2 if ri else 3):
            bx = 624 + j * 36
            span = 108
            name = f"m{ri}{j}"
            css += (
                f".{name} {{ animation: {name} {cycle / 2}s linear infinite; "
                f"animation-delay: -{j * cycle / 6:.2f}s; }} "
                f"@keyframes {name} {{ from {{ transform: translateX({624 - bx}px); }} "
                f"to {{ transform: translateX({624 - bx + span}px); }} }}\n"
            )
            b.append(
                f'<rect x="{bx}" y="{y - 6}" width="14" height="12" rx="2" class="kv {name}"/>'
            )
    b.append('<line x1="744" y1="154" x2="744" y2="182" class="fence"/>')
    b.append('<rect x="724" y="162" width="14" height="12" rx="2" class="late"/>')
    b.append(text(682, 200, "late write", "lbl2", "middle"))
    b.append(text(682, 214, "fenced", "lbl", "middle"))

    b.append(f'<rect x="520" y="250" width="324" height="28" rx="14" fill="{t["ink"]}"/>')
    b.append(
        f'<text x="682" y="268" text-anchor="middle" class="lbl" style="fill:{t["paper"]}">'
        "invariant  no old-epoch write lands</text>"
    )
    if scale_note:
        b.append(text(w - 24, 36, "illustrative", "cap", "end"))
    desc = (
        "A prefill pool computes layer by layer while KV-cache blocks stream over two RDMA "
        "rails into a decode pool's paged blocks. A late write from an aborted transfer is "
        "stopped at the fence and the reused block stays intact. Illustrative, not a "
        "measurement."
    )
    return svg(
        w,
        h,
        "kvwire: move the KV cache at line rate, stay correct when the wire fails",
        desc,
        css,
        "\n".join(b),
        t,
        defs,
    )


# ───────────────────────────── architecture ─────────────────────────────


def architecture(t: dict[str, str]) -> str:
    w, h = 880, 450
    defs, bar = accent_bar(t, w)
    for mid, col in (("ar", t["ink2"]), ("arc", t["copper"]), ("arg", t["graphite"])):
        defs += (
            f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" '
            f'markerHeight="10" markerUnits="userSpaceOnUse" orient="auto-start-reverse">'
            f'<path d="M0 0 L10 5 L0 10 z" '
            f'fill="{col}"/></marker>'
        )
    css = (
        base_css(t)
        + f"""
    .arr {{ fill: none; stroke: {t["ink2"]}; stroke-width: 1.3; marker-end: url(#ar); }}
    .ctl {{ fill: none; stroke: {t["graphite"]}; stroke-width: 1.2; stroke-dasharray: 4 3;
            marker-end: url(#arg); marker-start: url(#arg); }}
    .data {{ fill: none; stroke: {t["copper"]}; stroke-width: 4; }}
    .hl {{ fill: {t["paper"]}; stroke: {t["copper"]}; stroke-width: 2; }}
    .gated {{ fill: {t["paper"]}; stroke: {t["rule2"]}; stroke-width: 1.2; stroke-dasharray: 4 3; }}
    """
    )
    b = [
        bar,
        text(32, 46, "SYSTEM CONTEXT", "kick"),
        text(
            32,
            64,
            "control plane ≠ data plane · integrate, don't fork · every byte has an epoch",
            "kick2",
        ),
    ]
    # Clients and coordinator.
    b.append('<rect x="36" y="86" width="120" height="58" rx="8" class="card"/>')
    b.append(text(96, 112, "clients", "lbl", "middle"))
    b.append(text(96, 128, "OpenAI API", "lbl2", "middle"))
    b.append('<path d="M156 115 L214 115" class="arr"/>')
    b.append('<rect x="216" y="80" width="628" height="70" rx="10" class="box"/>')
    b.append(text(232, 102, "router / coordinator", "title"))
    b.append(text(232, 120, "never on the data path", "lbl2"))
    for i, c in enumerate(("transfer registry", "state machine", "SLO admission")):
        x = 410 + i * 142
        b.append(f'<rect x="{x}" y="100" width="134" height="30" rx="6" class="card"/>')
        b.append(text(x + 67, 120, c, "lbl", "middle"))

    # Pools.
    for side, x0, rows in (
        (
            "prefill pool · TP = p",
            36,
            [
                ("vLLM worker", "card"),
                ("kvwire connector · send", "hl"),
                ("pack kernel (gated)", "gated"),
            ],
        ),
        (
            "decode pool · TP = d",
            532,
            [
                ("vLLM worker", "card"),
                ("kvwire connector · recv", "hl"),
                ("unpack kernel (gated)", "gated"),
            ],
        ),
    ):
        b.append(f'<rect x="{x0}" y="196" width="312" height="168" rx="10" class="box"/>')
        b.append(text(x0 + 16, 218, side, "title"))
        for k, (lab, cls) in enumerate(rows):
            y = 230 + k * 42
            b.append(f'<rect x="{x0 + 16}" y="{y}" width="280" height="32" rx="6" class="{cls}"/>')
            b.append(text(x0 + 156, y + 21, lab, "lbl", "middle"))

    # Control plane (metadata) and data plane (KV bytes).
    b.append('<path d="M192 152 L192 194" class="ctl"/>')
    b.append('<path d="M688 152 L688 194" class="ctl"/>')
    b.append(text(200, 178, "reserve · epoch · grant", "lbl2"))
    b.append(text(696, 178, "commit · abort · fence", "lbl2"))
    b.append('<path d="M348 288 L516 288" class="data"/>')
    b.append(f'<path d="M514 280 L530 288 L514 296 z" fill="{t["copper"]}"/>')
    b.append(text(438, 276, "RDMA WRITE", "lbl", "middle"))
    b.append(text(438, 308, "layer-wise · multi-rail", "lbl2", "middle"))
    b.append(text(438, 322, "epoch-fenced", "lbl2", "middle"))

    # faultlab and legend.
    b.append('<rect x="36" y="382" width="808" height="34" rx="8" class="card dash"/>')
    b.append(text(52, 404, "faultlab", "lbl"))
    b.append(
        text(
            124,
            404,
            "kill P or D · link down / flap · forced QP error · late write · coordinator kill",
            "lbl2",
        )
    )
    b.append(
        '<line x1="300" y1="436" x2="330" y2="436" stroke="' + t["copper"] + '" stroke-width="4"/>'
    )
    b.append(text(338, 440, "KV bytes (data plane)", "lbl2"))
    b.append(
        '<line x1="500" y1="436" x2="530" y2="436" stroke="'
        + t["graphite"]
        + '" stroke-width="1.2" stroke-dasharray="4 3"/>'
    )
    b.append(text(538, 440, "metadata over TCP/gRPC (control plane)", "lbl2"))
    desc = (
        "Clients reach a router/coordinator that holds the transfer registry, state machine "
        "and admission control, and exchanges only metadata with the pools. KV bytes move "
        "from the prefill pool's kvwire connector to the decode pool's connector over RDMA "
        "writes, layer by layer, across multiple rails, fenced by epoch. Pack and unpack "
        "kernels are gated on a measured win. faultlab injects faults into both pools."
    )
    return svg(w, h, "kvwire architecture", desc, css, "\n".join(b), t, defs)


REPO = "github.com/nareshns2004/disaggregated-inference-engine"


def social(t: dict[str, str], repo: str) -> str:
    """1280 × 640 card: the banner scaled up, with the repository path underneath."""
    inner = banner(t, scale_note=False).split("\n", 1)[1].rsplit("</svg>", 1)[0]
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640">'
        f'<rect width="1280" height="640" fill="{t["paper"]}"/>'
        '<svg x="0" y="70" width="1280" height="436" viewBox="0 0 880 300">'
        "<style>* { animation: none !important; }</style>" + inner + "</svg>"
        f'<text x="640" y="590" text-anchor="middle" style="font: 600 22px {MONO}; '
        f'fill: {t["graphite"]}; letter-spacing: .04em">{esc(repo)}</text></svg>\n'
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, t in THEMES.items():
        (OUT / f"banner-{name}.svg").write_text(banner(t))
        (OUT / f"architecture-{name}.svg").write_text(architecture(t))
    # Social preview card for repository settings (rendered to PNG by scripts/render_png.sh).
    (OUT / "social-preview.svg").write_text(social(THEMES["light"], REPO))
    print(f"wrote {len(list(OUT.glob('*.svg')))} SVGs to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
