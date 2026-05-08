"""毕业论文绘图：Fig 1～8。

约定：
- 横轴用 S3CMD/S3LOG 在文件中的样本序号（idx）。
  原因：串口接收时间存在毫秒级抖动，且并非所有日志都有完整时间戳；
  样本序号能保证三轮 / 命令侧 / 反馈侧严格对齐，便于读图。
- 中文字体：Microsoft YaHei → SimHei → DejaVu Sans 兜底，避免乱码。
- 全部输出 300 dpi PNG。
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .classify import MODE_COLORS, MODE_LABELS_CN, MODE_ORDER, Segment

# --------------------------- 字体与样式 ---------------------------

matplotlib.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "DejaVu Sans",
]
matplotlib.rcParams["axes.unicode_minus"] = False
matplotlib.rcParams["figure.dpi"] = 110
matplotlib.rcParams["savefig.dpi"] = 300
matplotlib.rcParams["axes.grid"] = True
matplotlib.rcParams["grid.alpha"] = 0.3
matplotlib.rcParams["lines.linewidth"] = 1.0

WHEEL_COLORS = {1: "#1f77b4", 2: "#ff7f0e", 3: "#2ca02c"}


# --------------------------- 工具 ---------------------------

def _shade_modes(ax, segs: list[Segment], xs: np.ndarray) -> None:
    """在 ax 上画工况色带。xs 是 S3CMD 的横坐标数组。"""
    if not segs:
        return
    for s in segs:
        if s.mode == "idle":
            continue
        x0 = xs[s.start] if s.start < len(xs) else xs[-1]
        x1 = xs[s.end] if s.end < len(xs) else xs[-1]
        ax.axvspan(x0, x1, color=MODE_COLORS[s.mode], alpha=0.12, lw=0)


def _legend_modes(ax) -> None:
    handles = [
        plt.Rectangle((0, 0), 1, 1, fc=MODE_COLORS[m], alpha=0.35)
        for m in MODE_ORDER
        if m != "idle"
    ]
    labels = [MODE_LABELS_CN[m] for m in MODE_ORDER if m != "idle"]
    ax.legend(handles, labels, loc="upper right", fontsize=8, ncol=4, framealpha=0.9)


def _save(fig, out: Path, name: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    p = out / name
    fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return p


# --------------------------- Fig 1: 车体指令全景 ---------------------------

def fig1_body_cmd(
    cmd_df: pd.DataFrame,
    segs: list[Segment],
    title: str,
    out: Path,
    name: str = "fig1_body_cmd.png",
) -> Path:
    fig, axes = plt.subplots(3, 1, figsize=(11, 7), sharex=True)
    xs = cmd_df["idx"].to_numpy()

    axes[0].plot(xs, cmd_df["cmdVx"], color="#1f77b4")
    axes[0].set_ylabel("cmdVx (m/s)")
    _shade_modes(axes[0], segs, xs)

    axes[1].plot(xs, cmd_df["cmdVy"], color="#2ca02c")
    axes[1].set_ylabel("cmdVy (m/s)")
    _shade_modes(axes[1], segs, xs)

    axes[2].plot(xs, cmd_df["cmdVw"], color="#ff7f0e")
    axes[2].set_ylabel("cmdVw (rad/s)")
    axes[2].set_xlabel("S3CMD 样本序号")
    _shade_modes(axes[2], segs, xs)
    _legend_modes(axes[0])

    fig.suptitle(f"图1 车体指令全景与工况识别 —— {title}", fontsize=12)
    return _save(fig, out, name)


# --------------------------- Fig 2: 命令侧分开 ---------------------------

def fig2_cmd_per_wheel(
    log_by_w: dict[int, pd.DataFrame],
    title: str,
    out: Path,
    name: str = "fig2_cmd_per_wheel.png",
) -> Path:
    fig, (ax_v, ax_a) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    for w in (1, 2, 3):
        if w not in log_by_w:
            continue
        sub = log_by_w[w]
        ax_v.plot(sub["sample"], sub["cmdV"], color=WHEEL_COLORS[w], label=f"轮{w}")
        ax_a.plot(sub["sample"], sub["cmdA"], color=WHEEL_COLORS[w], label=f"轮{w}")
    ax_v.set_ylabel("指令轮速 cmdV (m/s)")
    ax_v.legend(loc="best", fontsize=9)
    ax_a.set_ylabel("指令舵角 cmdA (deg)")
    ax_a.set_xlabel("各轮 S3LOG 样本序号")
    ax_a.legend(loc="best", fontsize=9)
    fig.suptitle(f"图2 三舵轮命令侧（cmdV / cmdA） —— {title}", fontsize=12)
    return _save(fig, out, name)


# --------------------------- Fig 3: 反馈侧分开 ---------------------------

def fig3_fb_per_wheel(
    log_by_w: dict[int, pd.DataFrame],
    title: str,
    out: Path,
    name: str = "fig3_fb_per_wheel.png",
) -> Path:
    fig, (ax_v, ax_a) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    for w in (1, 2, 3):
        if w not in log_by_w:
            continue
        sub = log_by_w[w]
        ax_v.plot(sub["sample"], sub["fbV"], color=WHEEL_COLORS[w], label=f"轮{w}")
        ax_a.plot(sub["sample"], sub["fbA"], color=WHEEL_COLORS[w], label=f"轮{w}")
    ax_v.set_ylabel("反馈轮速 fbV (m/s)")
    ax_v.legend(loc="best", fontsize=9)
    ax_a.set_ylabel("反馈舵角 fbA (deg)")
    ax_a.set_xlabel("各轮 S3LOG 样本序号")
    ax_a.legend(loc="best", fontsize=9)
    fig.suptitle(f"图3 三舵轮反馈侧（fbV / fbA） —— {title}", fontsize=12)
    return _save(fig, out, name)


# --------------------------- Fig 4: 跟随误差 ---------------------------

def fig4_errors(
    log_by_w: dict[int, pd.DataFrame],
    title: str,
    out: Path,
    name: str = "fig4_errors.png",
) -> Path:
    fig, (ax_v, ax_a) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    for w in (1, 2, 3):
        if w not in log_by_w:
            continue
        sub = log_by_w[w]
        eV = sub["fbV"] - sub["cmdV"]
        eA = sub["fbA"] - sub["cmdA"]
        ax_v.plot(sub["sample"], eV, color=WHEEL_COLORS[w], label=f"轮{w}")
        ax_a.plot(sub["sample"], eA, color=WHEEL_COLORS[w], label=f"轮{w}")
    ax_v.axhline(0, color="k", lw=0.5)
    ax_a.axhline(0, color="k", lw=0.5)
    ax_v.set_ylabel("轮速误差 eV = fbV − cmdV (m/s)")
    ax_v.legend(loc="best", fontsize=9)
    ax_a.set_ylabel("舵角误差 eA = fbA − cmdA (deg)")
    ax_a.set_xlabel("各轮 S3LOG 样本序号")
    ax_a.legend(loc="best", fontsize=9)
    fig.suptitle(f"图4 三舵轮跟随误差时序 —— {title}", fontsize=12)
    return _save(fig, out, name)


# ---------------------- Fig 5: 过冲事件局部放大 ----------------------

def fig5_overshoot_zoom(
    cmd_df: pd.DataFrame,
    aligned_log: pd.DataFrame,
    event,  # OvershootEvent
    out: Path,
    name: str = "fig5_overshoot_zoom.png",
    pad_cmd: int = 30,
) -> Path:
    """对单个过冲事件做局部放大，并标注三阶段：
    1) 旋转/堵舵期    2) 释放瞬间    3) 释放后跟随
    """
    i = event.cmd_idx_switch
    a = max(0, i - pad_cmd)
    b = min(len(cmd_df), i + event.window_cmd_len + pad_cmd + 30)
    cmd_slice = cmd_df.iloc[a:b]
    if cmd_slice.empty:
        return Path("")

    # 与 cmd_slice 对应的 log 切片
    p_lo = cmd_slice["char_pos"].iloc[0]
    p_hi = cmd_slice["char_pos"].iloc[-1]
    log_slice = aligned_log[(aligned_log["char_pos"] >= p_lo) & (aligned_log["char_pos"] <= p_hi)]

    fig, axes = plt.subplots(3, 1, figsize=(11, 8.5), sharex=False)

    # 上：车体 cmdVx + 三阶段
    axes[0].plot(cmd_slice["idx"], cmd_slice["cmdVx"], color="#1f77b4", label="cmdVx")
    axes[0].plot(cmd_slice["idx"], cmd_slice["cmdVw"], color="#ff7f0e", label="cmdVw")
    axes[0].axvline(cmd_df["idx"].iloc[i], color="r", ls="--", lw=1, label="rotate→forward 切换")
    if event.window_cmd_len > 0 and i + event.window_cmd_len < len(cmd_df):
        axes[0].axvline(
            cmd_df["idx"].iloc[i + event.window_cmd_len],
            color="g",
            ls="--",
            lw=1,
            label="cmdV 释放点",
        )
        axes[0].axvspan(
            cmd_df["idx"].iloc[i],
            cmd_df["idx"].iloc[i + event.window_cmd_len],
            color="r",
            alpha=0.10,
            label="堵舵堆叠期",
        )
    axes[0].set_ylabel("车体指令 (m/s, rad/s)")
    axes[0].legend(loc="best", fontsize=8)
    axes[0].set_title(
        f"过冲事件：堆叠峰值 cmdVx={event.stack_peak_vx:.3f} m/s, "
        f"释放阶跃={event.release_step:.3f} m/s, "
        f"舵角残余={event.fbA_residual_deg:.2f}°"
    )

    # 中：三轮 cmdV 与 fbV
    for w in (1, 2, 3):
        sub = log_slice[log_slice["w"] == w]
        if sub.empty:
            continue
        axes[1].plot(sub.index, sub["cmdV"], color=WHEEL_COLORS[w], lw=1.4, label=f"轮{w} cmdV")
        axes[1].plot(sub.index, sub["fbV"], color=WHEEL_COLORS[w], lw=1.0, ls="--", label=f"轮{w} fbV")
    axes[1].set_ylabel("轮速 (m/s)")
    axes[1].legend(loc="best", fontsize=7, ncol=3)

    # 下：三轮 cmdA 与 fbA
    for w in (1, 2, 3):
        sub = log_slice[log_slice["w"] == w]
        if sub.empty:
            continue
        axes[2].plot(sub.index, sub["cmdA"], color=WHEEL_COLORS[w], lw=1.4, label=f"轮{w} cmdA")
        axes[2].plot(sub.index, sub["fbA"], color=WHEEL_COLORS[w], lw=1.0, ls="--", label=f"轮{w} fbA")
    axes[2].set_ylabel("舵角 (deg)")
    axes[2].set_xlabel("样本序号 (S3LOG 全局索引；上图为 S3CMD 索引，因此横轴含义不同)")
    axes[2].legend(loc="best", fontsize=7, ncol=3)

    fig.suptitle("图5 旋转→直行过冲事件局部放大", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    return _save(fig, out, name)


# ------------------- Fig 6: 改进前 vs 改进后对比 -------------------

def fig6_before_after(
    before_cmd: pd.DataFrame,
    before_event,
    after_cmd: pd.DataFrame,
    after_event,
    out: Path,
    name: str = "fig6_before_after.png",
    pad_cmd: int = 30,
) -> Path:
    """两行同结构：上 改进前 cmdVx / cmdVw，下 改进后 cmdVx / cmdVw。"""
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=False)

    def _plot(ax, cmd_df, event, label):
        if event is None:
            ax.text(0.5, 0.5, f"{label}: 未检测到事件", transform=ax.transAxes,
                    ha="center", va="center")
            return
        i = event.cmd_idx_switch
        a = max(0, i - pad_cmd)
        b = min(len(cmd_df), i + event.window_cmd_len + pad_cmd + 30)
        sl = cmd_df.iloc[a:b]
        ax.plot(sl["idx"], sl["cmdVx"], color="#1f77b4", label="cmdVx")
        ax.plot(sl["idx"], sl["cmdVw"], color="#ff7f0e", label="cmdVw")
        ax.axvline(cmd_df["idx"].iloc[i], color="r", ls="--", lw=1, label="切换点")
        if i + event.window_cmd_len < len(cmd_df):
            ax.axvspan(
                cmd_df["idx"].iloc[i],
                cmd_df["idx"].iloc[i + event.window_cmd_len],
                color="r",
                alpha=0.10,
            )
        ax.set_title(
            f"{label} 堆叠峰值={event.stack_peak_vx:.3f} m/s, "
            f"释放阶跃={event.release_step:.3f} m/s, "
            f"窗口={event.window_cmd_len} 个 S3CMD"
        )
        ax.set_ylabel("(m/s, rad/s)")
        ax.legend(loc="best", fontsize=8)

    _plot(axes[0], before_cmd, before_event, "改进前 (bug 复现)")
    _plot(axes[1], after_cmd, after_event, "改进后")
    axes[1].set_xlabel("S3CMD 样本序号")
    fig.suptitle("图6 改进前后同类「旋转→直行」事件对比", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return _save(fig, out, name)


# ------------------- Fig 7: 三轮 RMSE/max|e| 改进前后柱状 -------------------

def fig7_rmse_compare(
    summaries: dict[str, pd.DataFrame],
    out: Path,
    name: str = "fig7_rmse_compare.png",
) -> Path:
    """summaries: {label: per_wheel_summary_df}, 至少两组（改进前/改进后）。"""
    labels = list(summaries.keys())
    wheels = [1, 2, 3]
    width = 0.8 / max(len(labels), 1)

    fig, axes = plt.subplots(2, 2, figsize=(11, 7))

    metrics = [
        ("rmse_V", "轮速 RMSE (m/s)", axes[0, 0]),
        ("max_eV", "轮速 max|e| (m/s)", axes[0, 1]),
        ("rmse_A", "舵角 RMSE (deg)", axes[1, 0]),
        ("max_eA", "舵角 max|e| (deg)", axes[1, 1]),
    ]
    palette = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd"]
    for col, ylabel, ax in metrics:
        x = np.arange(len(wheels))
        for k, lbl in enumerate(labels):
            df = summaries[lbl]
            vals = []
            for w in wheels:
                row = df[df["w"] == w]
                vals.append(float(row[col].iloc[0]) if not row.empty else 0.0)
            ax.bar(x + (k - (len(labels) - 1) / 2) * width, vals, width=width,
                   color=palette[k % len(palette)], label=lbl)
        ax.set_xticks(x)
        ax.set_xticklabels([f"轮{w}" for w in wheels])
        ax.set_ylabel(ylabel)
        ax.legend(loc="best", fontsize=8)

    fig.suptitle("图7 三舵轮跟随性能改进前后对比", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return _save(fig, out, name)


# ------------------- Fig 8: 过冲事件指标对比柱状 -------------------

def fig8_overshoot_compare(
    overshoot_summaries: dict[str, dict],
    out: Path,
    name: str = "fig8_overshoot_compare.png",
) -> Path:
    labels = list(overshoot_summaries.keys())
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    palette = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd"]

    keys = [
        ("stack_peak_max", "stack_peak_mean", "堵舵期 cmdVx 堆叠 (m/s)"),
        ("release_step_max", "release_step_mean", "释放阶跃 (m/s)"),
        ("fbA_residual_max", "fbA_residual_mean", "释放瞬间舵角残余 (deg)"),
    ]
    for ax, (k_max, k_mean, ylabel) in zip(axes, keys):
        x = np.arange(len(labels))
        max_vals = [overshoot_summaries[l].get(k_max, 0.0) for l in labels]
        mean_vals = [overshoot_summaries[l].get(k_mean, 0.0) for l in labels]
        ax.bar(x - 0.2, max_vals, width=0.38, color=palette[0], label="最大值")
        ax.bar(x + 0.2, mean_vals, width=0.38, color=palette[1], label="平均值")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, rotation=15, ha="right")
        ax.set_ylabel(ylabel)
        ax.legend(loc="best", fontsize=8)

    fig.suptitle("图8 过冲事件关键指标改进前后对比", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return _save(fig, out, name)


__all__ = [
    "fig1_body_cmd",
    "fig2_cmd_per_wheel",
    "fig3_fb_per_wheel",
    "fig4_errors",
    "fig5_overshoot_zoom",
    "fig6_before_after",
    "fig7_rmse_compare",
    "fig8_overshoot_compare",
]
