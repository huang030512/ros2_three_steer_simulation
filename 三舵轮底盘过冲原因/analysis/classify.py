"""车体工况分类。

输入：S3CMD 时间序列 (cmdVx, cmdVy, cmdVw)
输出：每条 S3CMD 的运动模式标签 ∈ {idle, forward, translate, rotate, compound}

判据（论文中给出的）：

- 静止 idle      : |vx|<v_th 且 |vy|<v_th 且 |w|<w_th
- 前进 forward   : |vx|≥v_th，其它两个低于阈值
- 平移 translate : |vy|≥v_th，其它两个低于阈值
- 旋转 rotate    : |w| ≥w_th，其它两个低于阈值
- 复合 compound  : 上述任意两个或以上同时显著
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# 默认阈值（m/s 与 rad/s）；按经验给得偏小，以便把"加减速过程"也算成动态而非误判为 idle
DEFAULT_V_TH = 0.005
DEFAULT_W_TH = 0.005

MODE_ORDER = ["idle", "forward", "translate", "rotate", "compound"]
MODE_LABELS_CN = {
    "idle": "静止",
    "forward": "前进/后退",
    "translate": "平移",
    "rotate": "旋转",
    "compound": "复合",
}
MODE_COLORS = {
    "idle": "#CCCCCC",
    "forward": "#1f77b4",
    "translate": "#2ca02c",
    "rotate": "#ff7f0e",
    "compound": "#d62728",
}


@dataclass
class Segment:
    """连续同模式段。"""

    mode: str
    start: int  # S3CMD idx
    end: int  # 闭区间末端 idx
    duration_samples: int
    peak_vx: float
    peak_vy: float
    peak_vw: float


def classify(
    cmd_df: pd.DataFrame,
    v_th: float = DEFAULT_V_TH,
    w_th: float = DEFAULT_W_TH,
) -> pd.Series:
    """为 cmd_df 的每行打模式标签。"""
    if cmd_df.empty:
        return pd.Series(dtype=object)
    vx = cmd_df["cmdVx"].abs().to_numpy()
    vy = cmd_df["cmdVy"].abs().to_numpy()
    vw = cmd_df["cmdVw"].abs().to_numpy()

    a_x = vx >= v_th
    a_y = vy >= v_th
    a_w = vw >= w_th
    active = a_x.astype(int) + a_y.astype(int) + a_w.astype(int)

    mode = np.full(len(cmd_df), "idle", dtype=object)
    mode[(active == 1) & a_x] = "forward"
    mode[(active == 1) & a_y] = "translate"
    mode[(active == 1) & a_w] = "rotate"
    mode[active >= 2] = "compound"
    return pd.Series(mode, index=cmd_df.index, name="mode")


def segment(
    cmd_df: pd.DataFrame,
    modes: pd.Series,
    min_run: int = 2,
) -> list[Segment]:
    """把模式序列压缩成连续段。

    min_run: 小于该长度的连续段会被合并到前一段（去抖动）。
    """
    if cmd_df.empty or modes.empty:
        return []
    arr = modes.to_numpy()
    starts = [0]
    for i in range(1, len(arr)):
        if arr[i] != arr[i - 1]:
            starts.append(i)
    starts.append(len(arr))

    segs: list[Segment] = []
    for a, b in zip(starts[:-1], starts[1:]):
        m = arr[a]
        sub = cmd_df.iloc[a:b]
        seg = Segment(
            mode=m,
            start=a,
            end=b - 1,
            duration_samples=b - a,
            peak_vx=float(sub["cmdVx"].abs().max()),
            peak_vy=float(sub["cmdVy"].abs().max()),
            peak_vw=float(sub["cmdVw"].abs().max()),
        )
        segs.append(seg)

    # 去掉非常短的抖动段，并入前一个
    if min_run > 1 and segs:
        merged: list[Segment] = [segs[0]]
        for seg in segs[1:]:
            if seg.duration_samples < min_run and merged:
                prev = merged[-1]
                prev.end = seg.end
                prev.duration_samples = prev.end - prev.start + 1
                prev.peak_vx = max(prev.peak_vx, seg.peak_vx)
                prev.peak_vy = max(prev.peak_vy, seg.peak_vy)
                prev.peak_vw = max(prev.peak_vw, seg.peak_vw)
            else:
                merged.append(seg)
        segs = merged
    return segs


def segments_to_df(segs: list[Segment]) -> pd.DataFrame:
    """段列表 → DataFrame（便于落 CSV）。"""
    if not segs:
        return pd.DataFrame(
            columns=[
                "mode",
                "start",
                "end",
                "duration_samples",
                "peak_vx",
                "peak_vy",
                "peak_vw",
            ]
        )
    return pd.DataFrame([s.__dict__ for s in segs])


def mode_summary(segs: list[Segment]) -> pd.DataFrame:
    """各模式累计样本数与平均段长。"""
    if not segs:
        return pd.DataFrame(columns=["mode", "label", "samples", "segments", "mean_len"])
    rows = []
    for m in MODE_ORDER:
        sub = [s for s in segs if s.mode == m]
        if not sub:
            continue
        rows.append(
            {
                "mode": m,
                "label": MODE_LABELS_CN[m],
                "samples": int(sum(s.duration_samples for s in sub)),
                "segments": len(sub),
                "mean_len": float(np.mean([s.duration_samples for s in sub])),
            }
        )
    return pd.DataFrame(rows)


__all__ = [
    "DEFAULT_V_TH",
    "DEFAULT_W_TH",
    "MODE_ORDER",
    "MODE_LABELS_CN",
    "MODE_COLORS",
    "Segment",
    "classify",
    "segment",
    "segments_to_df",
    "mode_summary",
]
