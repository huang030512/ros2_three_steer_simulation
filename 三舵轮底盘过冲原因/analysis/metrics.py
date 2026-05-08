"""跟随性能与"旋转→直行过冲事件"指标。

跟随误差：
  e_V = fbV - cmdV
  e_A = fbA - cmdA   （未做 unwrap，本工程舵角范围未跨 ±180°，可忽略）

过冲事件（旋转→直行场景，论文 Fig 5/6 用）：
  当车体指令模式由 rotate / compound 切换到 forward 时，关注接下来的窗口里
  - cmdVx 在 cmdV(轮速) 仍为 0 期间的最大堆叠值        → stack_peak
  - cmdV 第一次脱离 0 时的台阶高度                      → release_step
  - 释放瞬间的最大舵角偏差 |fbA - cmdA|                 → fbA_residual
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


# -------------------------- 跟随误差 --------------------------

def per_wheel_errors(log_df: pd.DataFrame) -> pd.DataFrame:
    """计算每条 S3LOG 的跟随误差（单条记录粒度）。"""
    out = log_df.copy()
    out["eV"] = out["fbV"] - out["cmdV"]
    out["eA"] = out["fbA"] - out["cmdA"]
    return out


def per_wheel_summary(log_df: pd.DataFrame) -> pd.DataFrame:
    """按舵轮汇总 RMSE / max|e| / mean|e|。

    返回列：w, n, rmse_V, max_eV, mean_abs_eV, rmse_A, max_eA, mean_abs_eA
    """
    if log_df.empty:
        return pd.DataFrame()
    err = per_wheel_errors(log_df)
    rows = []
    for w, sub in err.groupby("w"):
        rows.append(
            {
                "w": int(w),
                "n": int(len(sub)),
                "rmse_V": float(np.sqrt(np.mean(sub["eV"] ** 2))),
                "max_eV": float(sub["eV"].abs().max()),
                "mean_abs_eV": float(sub["eV"].abs().mean()),
                "rmse_A": float(np.sqrt(np.mean(sub["eA"] ** 2))),
                "max_eA": float(sub["eA"].abs().max()),
                "mean_abs_eA": float(sub["eA"].abs().mean()),
            }
        )
    return pd.DataFrame(rows)


# -------------------------- 过冲事件检测 --------------------------

@dataclass
class OvershootEvent:
    """旋转/复合 → 前进 切换点附近的一次过冲。"""

    cmd_idx_switch: int  # S3CMD 中切换到 forward 的索引
    log_idx_release: int  # 关联 S3LOG（任一轮）首次轮速脱离 0 的索引
    stack_peak_vx: float  # 堵舵期 cmdVx 的最大值（或 vy / vw 中主分量）
    release_step: float  # 任一轮 cmdV 首次离 0 的步幅
    fbA_residual_deg: float  # 释放瞬间最大 |fbA-cmdA|
    window_cmd_len: int  # 切换→释放经历的 cmd 样本数


def find_overshoot_events(
    cmd_df: pd.DataFrame,
    aligned_log: pd.DataFrame,
    modes: pd.Series,
    cmd_zero_th: float = 0.01,  # m/s，cmdV 视为 0 的阈值
    max_window_cmd: int = 200,  # 最多向后看多少条 S3CMD
) -> list[OvershootEvent]:
    """寻找"旋转/复合 → 前进"切换处的过冲事件。

    aligned_log 必须含列：cmdV, cmdA, fbA, char_pos, w（来自 align_log_to_cmd）。
    """
    if cmd_df.empty or aligned_log.empty or modes.empty:
        return []

    events: list[OvershootEvent] = []
    arr = modes.to_numpy()
    cmd_pos = cmd_df["char_pos"].to_numpy()
    log_pos = aligned_log["char_pos"].to_numpy()

    for i in range(1, len(arr)):
        if arr[i] == "forward" and arr[i - 1] in ("rotate", "compound"):
            j_end = min(i + max_window_cmd, len(arr))
            switch_pos = cmd_pos[i]
            window_pos_end = cmd_pos[j_end - 1]

            # 这段 S3CMD 切片
            cmd_slice = cmd_df.iloc[i:j_end]
            # 这段对应的 S3LOG（按字符位置）
            log_mask = (log_pos >= switch_pos) & (log_pos <= window_pos_end)
            log_slice = aligned_log[log_mask]
            if log_slice.empty:
                continue

            # 找到任意一轮 cmdV 首次脱离 0 的索引
            nonzero = log_slice[log_slice["cmdV"].abs() > cmd_zero_th]
            if nonzero.empty:
                continue
            release_row = nonzero.iloc[0]
            release_pos = release_row["char_pos"]

            # 堵舵期 = 切换点到释放点之间的 cmd
            stack_mask = (cmd_pos >= switch_pos) & (cmd_pos < release_pos)
            stack_slice = cmd_df[stack_mask]
            if stack_slice.empty:
                continue
            stack_peak = float(stack_slice["cmdVx"].abs().max())

            # 释放台阶：取释放瞬间该轮 cmdV 与之前最近的 0 之差（这里直接用其值）
            release_step = float(abs(release_row["cmdV"]))

            # 释放瞬间所有轮舵角残余
            same_pos_logs = aligned_log[
                aligned_log["char_pos"].between(
                    release_row["char_pos"] - 200, release_row["char_pos"] + 200
                )
            ]
            if same_pos_logs.empty:
                fbA_res = float(abs(release_row["fbA"] - release_row["cmdA"]))
            else:
                fbA_res = float(
                    (same_pos_logs["fbA"] - same_pos_logs["cmdA"]).abs().max()
                )

            events.append(
                OvershootEvent(
                    cmd_idx_switch=i,
                    log_idx_release=int(release_row.name),
                    stack_peak_vx=stack_peak,
                    release_step=release_step,
                    fbA_residual_deg=fbA_res,
                    window_cmd_len=len(stack_slice),
                )
            )
    return events


def overshoot_summary(events: list[OvershootEvent]) -> dict:
    """事件统计（用于改进前后对比）。"""
    if not events:
        return {
            "n_events": 0,
            "stack_peak_max": 0.0,
            "stack_peak_mean": 0.0,
            "release_step_max": 0.0,
            "release_step_mean": 0.0,
            "fbA_residual_max": 0.0,
            "fbA_residual_mean": 0.0,
            "window_mean": 0.0,
        }
    sp = np.array([e.stack_peak_vx for e in events])
    rs = np.array([e.release_step for e in events])
    fr = np.array([e.fbA_residual_deg for e in events])
    wn = np.array([e.window_cmd_len for e in events])
    return {
        "n_events": len(events),
        "stack_peak_max": float(sp.max()),
        "stack_peak_mean": float(sp.mean()),
        "release_step_max": float(rs.max()),
        "release_step_mean": float(rs.mean()),
        "fbA_residual_max": float(fr.max()),
        "fbA_residual_mean": float(fr.mean()),
        "window_mean": float(wn.mean()),
    }


def events_to_df(events: list[OvershootEvent]) -> pd.DataFrame:
    if not events:
        return pd.DataFrame(
            columns=[
                "cmd_idx_switch",
                "log_idx_release",
                "stack_peak_vx",
                "release_step",
                "fbA_residual_deg",
                "window_cmd_len",
            ]
        )
    return pd.DataFrame([e.__dict__ for e in events])


__all__ = [
    "OvershootEvent",
    "per_wheel_errors",
    "per_wheel_summary",
    "find_overshoot_events",
    "overshoot_summary",
    "events_to_df",
]
