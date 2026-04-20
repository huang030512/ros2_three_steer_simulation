from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "generated_assets"


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

BLUE = "#1f4e79"
MID_BLUE = "#4f81bd"
LIGHT_BLUE = "#dbe8f6"
LIGHT_GREEN = "#e2f0d9"
LIGHT_YELLOW = "#fff2cc"
LIGHT_ORANGE = "#fce4d6"
LIGHT_PURPLE = "#e4dfec"
RED = "#c00000"
GREEN = "#70ad47"
TEXT = "#303030"
GRAY = "#6f6f6f"


def draw_box(ax, xy, w, h, text, fc="#eef4fb", ec="#4f81bd", fontsize=13, bold=False):
    shadow = FancyBboxPatch(
        (xy[0] + 0.06, xy[1] - 0.06),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=0,
        facecolor="#d9e2f0",
        alpha=0.35,
        zorder=1,
    )
    ax.add_patch(shadow)
    rect = FancyBboxPatch(
        xy,
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=2,
        edgecolor=ec,
        facecolor=fc,
        zorder=2,
    )
    ax.add_patch(rect)
    ax.text(
        xy[0] + w / 2,
        xy[1] + h / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        fontweight="bold" if bold else "normal",
        color=TEXT,
        wrap=True,
        zorder=3,
    )


def draw_arrow(ax, p1, p2, color="#c00000", lw=2.2, rad=0.0):
    style = f"arc3,rad={rad}"
    ax.add_patch(
        FancyArrowPatch(
            p1,
            p2,
            connectionstyle=style,
            arrowstyle="-|>",
            mutation_scale=15,
            lw=lw,
            color=color,
        )
    )


def draw_panel(ax):
    panel = FancyBboxPatch(
        (-2.05, -2.35),
        4.1,
        4.45,
        boxstyle="round,pad=0.02,rounding_size=0.18",
        linewidth=1.4,
        edgecolor="#d8e3f0",
        facecolor="#fbfdff",
        zorder=0,
    )
    ax.add_patch(panel)


def draw_chassis(ax, center=(0, 0), scale=1.0, show_labels=False):
    cx, cy = center
    body_w, body_h = 1.9 * scale, 1.3 * scale
    body = FancyBboxPatch(
        (cx - body_w / 2, cy - body_h / 2),
        body_w,
        body_h,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        linewidth=2.0,
        edgecolor=BLUE,
        facecolor=LIGHT_BLUE,
    )
    ax.add_patch(body)

    wheels = [
        ("前舵轮", cx + 0.0 * scale, cy + 1.05 * scale),
        ("左后舵轮", cx - 0.95 * scale, cy - 1.0 * scale),
        ("右后舵轮", cx + 0.95 * scale, cy - 1.0 * scale),
    ]
    for name, x, y in wheels:
        ax.add_patch(Circle((x, y), 0.22 * scale, linewidth=1.7, edgecolor=GRAY, facecolor="#f7f7f7", zorder=3))
        ax.add_patch(Circle((x, y), 0.08 * scale, linewidth=0.9, edgecolor=GRAY, facecolor="#d0d0d0", zorder=4))
        if show_labels:
            ax.plot([cx, x], [cy, y], linestyle="--", color="#c9d3de", linewidth=1.0, zorder=1)
            ax.text(x, y + 0.30 * scale, name, ha="center", va="bottom", fontsize=11, color=TEXT)
            ax.text(x, y - 0.34 * scale, f"({x-cx:.2f}, {y-cy:.2f})", ha="center", va="top", fontsize=8.5, color="#666666")

    # coordinate frame
    ax.add_patch(Circle((cx, cy), 0.03 * scale, facecolor=TEXT, edgecolor="none", zorder=5))
    draw_arrow(ax, (cx, cy), (cx + 0.8 * scale, cy), color="#2f5597", lw=1.8)
    draw_arrow(ax, (cx, cy), (cx, cy + 0.8 * scale), color=GREEN, lw=1.8)
    ax.text(cx + 0.9 * scale, cy + 0.02 * scale, "X", fontsize=11, color="#2f5597", va="center")
    ax.text(cx - 0.02 * scale, cy + 0.95 * scale, "Y", fontsize=11, color=GREEN, ha="center")


def fig_motion_modes():
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.8), dpi=220)
    fig.patch.set_facecolor("white")
    specs = [
        ("纯前进", "Vx > 0, Vy = 0, ω = 0", "forward"),
        ("纯横移", "Vx = 0, Vy > 0, ω = 0", "lateral"),
        ("原地旋转", "Vx = 0, Vy = 0, ω > 0", "rotate"),
    ]
    for ax, (title, note, mode) in zip(axes, specs):
        ax.set_aspect("equal")
        ax.set_xlim(-2.2, 2.2)
        ax.set_ylim(-2.6, 2.55)
        ax.axis("off")
        draw_panel(ax)
        draw_chassis(ax)
        if mode == "forward":
            draw_arrow(ax, (0, 1.42), (0, 2.0), lw=2.8)
        elif mode == "lateral":
            draw_arrow(ax, (1.55, 0), (-1.55, 0), lw=2.8)
        else:
            draw_arrow(ax, (0.68, 1.42), (-0.68, 1.42), lw=2.3, rad=1.0)
            draw_arrow(ax, (-0.62, -0.18), (-0.28, 0.55), lw=2.3, rad=0.95)
        ax.text(0, 2.18, title, fontsize=15, fontweight="bold", ha="center", color=TEXT)
        ax.text(0, -2.02, note, fontsize=11.5, ha="center", color="#4d4d4d")
    fig.suptitle("全向运动模式示意图", fontsize=20, fontweight="bold", color=BLUE, y=0.98)
    plt.tight_layout(rect=(0, 0, 1, 0.93))
    out = OUT_DIR / "全向运动模式示意图.png"
    plt.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def fig_structure():
    fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=220)
    ax.set_aspect("equal")
    ax.set_xlim(-3.1, 3.1)
    ax.set_ylim(-2.8, 3.0)
    ax.axis("off")
    draw_chassis(ax, center=(0, 0), scale=1.2, show_labels=True)

    # velocity definitions
    draw_arrow(ax, (0, 0), (1.95, 0), color=RED, lw=2.3)
    draw_arrow(ax, (0, 0), (0, 1.95), color=RED, lw=2.3)
    ax.text(2.1, 0, "Vx", fontsize=13, color=RED, va="center", fontweight="bold")
    ax.text(0.0, 2.08, "Vy", fontsize=13, color=RED, ha="center", fontweight="bold")
    draw_arrow(ax, (0.62, 1.82), (-0.62, 1.82), color=RED, lw=2.1, rad=0.95)
    ax.text(0, 2.20, "ω", fontsize=14, color=RED, ha="center", fontweight="bold")

    ax.text(0, 2.82, "三舵轮底盘结构与坐标系示意图", fontsize=20, fontweight="bold", color=BLUE, ha="center")
    ax.text(0, -2.45, "以车体中心建立车体坐标系，三个舵轮位置参数用于后续逆运动学解算", fontsize=12, color="#505050", ha="center")
    out = OUT_DIR / "三舵轮结构与坐标系示意图.png"
    plt.tight_layout()
    plt.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def fig_system_overview():
    fig, ax = plt.subplots(figsize=(13.5, 5.8), dpi=220)
    ax.set_xlim(0, 13.5)
    ax.set_ylim(0, 5.8)
    ax.axis("off")

    ax.text(6.75, 5.32, "系统总体方案框图", fontsize=20, fontweight="bold", color=BLUE, ha="center")

    xs = [0.55, 3.1, 5.65, 8.2, 10.75]
    titles = [
        "输入层\n手柄输入\n上层速度指令",
        "目标生成\nX / Y / ω\n速度目标",
        "控制层\n速度平滑处理\n逆运动学解算",
        "执行层\n舵角命令\n轮速命令下发",
        "反馈层\n角度/速度反馈\n状态与故障检测",
    ]
    colors = [LIGHT_GREEN, LIGHT_YELLOW, LIGHT_BLUE, LIGHT_ORANGE, LIGHT_PURPLE]
    for x, text, fc in zip(xs, titles, colors):
        draw_box(ax, (x, 2.25), 1.95, 1.3, text, fc=fc, fontsize=11.8, bold=True)

    for i in range(len(xs) - 1):
        draw_arrow(ax, (xs[i] + 1.98, 2.9), (xs[i + 1], 2.9), color=RED, lw=2.0)

    draw_arrow(ax, (11.75, 2.2), (1.0, 1.25), color=GREEN, lw=1.8, rad=-0.08)
    ax.text(6.4, 1.0, "闭环反馈更新", fontsize=11.5, color=GREEN, ha="center")

    ax.text(6.75, 4.42, "实物主线：STM32 控制程序完成底盘层控制逻辑", fontsize=12.8, color="#4a4a4a", ha="center")
    ax.text(6.75, 0.34, "仿真主线：ROS 2 / Gazebo 用于验证控制关系与典型工况输出", fontsize=12.8, color="#4a4a4a", ha="center")
    out = OUT_DIR / "系统总体方案框图.png"
    plt.tight_layout()
    plt.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def fig_control_flow():
    fig, ax = plt.subplots(figsize=(8.2, 10.0), dpi=220)
    ax.set_xlim(0, 8.2)
    ax.set_ylim(0, 10.0)
    ax.axis("off")
    ax.text(4.1, 9.5, "控制程序流程图", fontsize=20, fontweight="bold", color=BLUE, ha="center")

    y = [8.2, 6.95, 5.7, 4.45, 3.2, 1.95, 0.7]
    texts = [
        "系统初始化\n读取配置参数",
        "接收输入\n手柄按键 / 上层速度指令",
        "生成底盘目标速度\nVx、Vy、ω",
        "速度平滑处理\n三角形加减速轨迹",
        "三舵轮逆运动学解算\n求舵角与轮速命令",
        "执行器命令下发\n发送舵角与轮速控制量",
        "状态反馈与循环执行\n更新角度、速度和运行状态",
    ]
    fills = [LIGHT_BLUE, LIGHT_GREEN, LIGHT_YELLOW, LIGHT_ORANGE, LIGHT_PURPLE, LIGHT_BLUE, LIGHT_GREEN]

    for yi, text, fc in zip(y, texts, fills):
        draw_box(ax, (1.55, yi), 5.1, 0.85, text, fc=fc, fontsize=11.8, bold=True)

    for i in range(len(y) - 1):
        draw_arrow(ax, (4.1, y[i]), (4.1, y[i + 1] + 0.85), color=RED, lw=2.0)

    ax.text(4.1, 0.16, "循环周期执行，实现输入—解算—输出—反馈完整控制链路", fontsize=11.8, color="#4a4a4a", ha="center")
    out = OUT_DIR / "控制程序流程图.png"
    plt.tight_layout()
    plt.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outs = [
        fig_motion_modes(),
        fig_structure(),
        fig_system_overview(),
        fig_control_flow(),
    ]
    for p in outs:
        print(p)


if __name__ == "__main__":
    main()
