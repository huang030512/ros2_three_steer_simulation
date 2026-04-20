from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "generated_assets" / "全向运动模式示意图.png"


def pick_cjk_font():
    candidates = [
        "Noto Sans CJK SC",
        "Noto Sans CJK JP",
        "Source Han Sans CN",
        "WenQuanYi Zen Hei",
        "Microsoft YaHei",
        "SimHei",
        "Arial Unicode MS",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return "DejaVu Sans"


FONT_NAME = pick_cjk_font()
plt.rcParams["font.family"] = FONT_NAME
plt.rcParams["axes.unicode_minus"] = False


def draw_chassis(ax, mode_title, annotation, mode):
    ax.set_aspect("equal")
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-2.6, 2.4)
    ax.axis("off")

    # chassis body
    body = Rectangle(
        (-0.95, -0.65),
        1.9,
        1.3,
        linewidth=2.2,
        edgecolor="#1f4e79",
        facecolor="#dbe8f6",
        joinstyle="round",
    )
    ax.add_patch(body)

    # three steer wheels
    wheels = [(0.0, 1.05), (-0.95, -1.0), (0.95, -1.0)]
    for x, y in wheels:
        outer = Circle((x, y), 0.22, linewidth=1.8, edgecolor="#6b6b6b", facecolor="#f2f2f2")
        inner = Circle((x, y), 0.08, linewidth=1.1, edgecolor="#6b6b6b", facecolor="#c9c9c9")
        ax.add_patch(outer)
        ax.add_patch(inner)

    # body coordinate frame
    ax.add_patch(FancyArrowPatch((0.0, 0.0), (0.75, 0.0), arrowstyle="-|>", mutation_scale=16, lw=1.8, color="#2f5597"))
    ax.add_patch(FancyArrowPatch((0.0, 0.0), (0.0, 0.75), arrowstyle="-|>", mutation_scale=16, lw=1.8, color="#70ad47"))
    ax.text(0.83, 0.0, "X", fontsize=12, color="#2f5597", va="center")
    ax.text(0.0, 0.86, "Y", fontsize=12, color="#70ad47", ha="center")

    # motion arrows
    if mode == "forward":
        ax.add_patch(
            FancyArrowPatch(
                (0.0, 1.55),
                (0.0, 2.15),
                arrowstyle="simple",
                mutation_scale=28,
                lw=0,
                color="#c00000",
                alpha=0.95,
            )
        )
    elif mode == "lateral":
        ax.add_patch(
            FancyArrowPatch(
                (1.6, 0.0),
                (-1.6, 0.0),
                arrowstyle="simple",
                mutation_scale=28,
                lw=0,
                color="#c00000",
                alpha=0.95,
            )
        )
    elif mode == "rotate":
        ax.add_patch(
            FancyArrowPatch(
                (-0.65, -0.15),
                (-0.35, 0.6),
                connectionstyle="arc3,rad=1.1",
                arrowstyle="-|>",
                mutation_scale=20,
                lw=2.8,
                color="#c00000",
            )
        )
        ax.add_patch(
            FancyArrowPatch(
                (0.45, 1.6),
                (-0.45, 1.6),
                connectionstyle="arc3,rad=1.25",
                arrowstyle="-|>",
                mutation_scale=18,
                lw=2.4,
                color="#c00000",
            )
        )

    ax.text(0, 2.25, mode_title, fontsize=16, fontweight="bold", color="#1f1f1f", ha="center")
    ax.text(0, -2.0, annotation, fontsize=12, color="#404040", ha="center")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.8), dpi=220)
    fig.patch.set_facecolor("white")

    draw_chassis(axes[0], "纯前进", "Vx > 0, Vy = 0, ω = 0", "forward")
    draw_chassis(axes[1], "纯横移", "Vx = 0, Vy > 0, ω = 0", "lateral")
    draw_chassis(axes[2], "原地旋转", "Vx = 0, Vy = 0, ω > 0", "rotate")

    fig.suptitle("全向运动模式示意图", fontsize=20, fontweight="bold", color="#1f4e79", y=0.98)
    plt.tight_layout(rect=(0, 0, 1, 0.93))
    plt.savefig(OUT, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(OUT)


if __name__ == "__main__":
    main()
