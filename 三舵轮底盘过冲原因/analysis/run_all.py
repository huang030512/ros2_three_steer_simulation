"""一键产出毕业论文的所有图（PNG）、表（CSV）与论文文本中要回填的指标 JSON。

用法：
    python -m analysis.run_all

输出：
    analysis/figures/*.png
    analysis/tables/*.csv
    analysis/tables/metrics.json   ← 用于回填论文 markdown 占位符
    thesis/第X章_实验与分析.md     ← 自动把 {{占位符}} 替换为实测数值后的版本
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from .classify import classify, mode_summary, segment, segments_to_df
from .metrics import (
    events_to_df,
    find_overshoot_events,
    overshoot_summary,
    per_wheel_summary,
)
from .parse import align_log_to_cmd, parse_log, split_log_by_wheel
from .plot_figures import (
    fig1_body_cmd,
    fig2_cmd_per_wheel,
    fig3_fb_per_wheel,
    fig4_errors,
    fig5_overshoot_zoom,
    fig6_before_after,
    fig7_rmse_compare,
    fig8_overshoot_compare,
)

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "analysis" / "figures"
TBL_DIR = ROOT / "analysis" / "tables"
THESIS_DIR = ROOT / "thesis"

# 数据集映射：key 是 stem，value 是 (label_cn, file_path)
DATASETS = {
    "baseline": ("基线（早期日志）", ROOT / "底盘数据.txt"),
    "bug": ("改进前 bug 复现", ROOT / "旋转后前进过冲的bug.txt"),
    "improved_v1": ("改进 v1（中间版本）", ROOT / "改善后的数据.txt"),
    "improved_final": ("改进 v2（最终版本）", ROOT / "真正修改后的数据.txt"),
}

# 用于改进前/后图的两份关键数据
BEFORE_KEY = "bug"
AFTER_KEY = "improved_final"


def _fmt(v, digits: int = 3) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        if v != v:  # NaN
            return "—"
        return f"{v:.{digits}f}"
    return str(v)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TBL_DIR.mkdir(parents=True, exist_ok=True)

    # ---------- 1) 解析全部数据 ----------
    parsed: dict[str, dict] = {}
    for key, (label, path) in DATASETS.items():
        if not path.exists():
            print(f"[skip] {path} 不存在")
            continue
        cmd, log, stats = parse_log(path)
        log_by_w = split_log_by_wheel(log)
        aligned = align_log_to_cmd(cmd, log) if not cmd.empty else log.copy()
        parsed[key] = {
            "label": label,
            "path": path,
            "cmd": cmd,
            "log": log,
            "log_by_w": log_by_w,
            "aligned": aligned,
            "stats": stats,
        }
        # 落原始解析 CSV
        cmd.to_csv(TBL_DIR / f"raw_cmd_{key}.csv", index=False, encoding="utf-8-sig")
        log.to_csv(TBL_DIR / f"raw_log_{key}.csv", index=False, encoding="utf-8-sig")
        print(
            f"[parsed] {key:14s} {label:18s}  S3CMD={stats.s3cmd_records:>5}  S3LOG={stats.s3log_records:>5}"
        )

    # ---------- 2) 工况分类与误差统计 ----------
    summaries: dict[str, pd.DataFrame] = {}
    overshoots: dict[str, dict] = {}
    events_by_key: dict[str, list] = {}
    seg_by_key: dict[str, list] = {}
    mode_summary_rows = []

    for key, d in parsed.items():
        cmd = d["cmd"]
        log = d["log"]
        aligned = d["aligned"]
        label = d["label"]

        per_w = per_wheel_summary(log)
        per_w["dataset"] = key
        per_w["label"] = label
        summaries[key] = per_w
        per_w.to_csv(TBL_DIR / f"per_wheel_{key}.csv", index=False, encoding="utf-8-sig")

        if cmd.empty:
            seg_by_key[key] = []
            events_by_key[key] = []
            overshoots[key] = overshoot_summary([])
            continue

        modes = classify(cmd)
        segs = segment(cmd, modes, min_run=3)
        seg_by_key[key] = segs
        segments_to_df(segs).to_csv(
            TBL_DIR / f"segments_{key}.csv", index=False, encoding="utf-8-sig"
        )
        ms = mode_summary(segs).copy()
        ms["dataset"] = key
        ms["label"] = label
        mode_summary_rows.append(ms)

        events = find_overshoot_events(cmd, aligned, modes)
        events_by_key[key] = events
        events_to_df(events).to_csv(
            TBL_DIR / f"overshoot_events_{key}.csv", index=False, encoding="utf-8-sig"
        )
        overshoots[key] = overshoot_summary(events)

    if mode_summary_rows:
        pd.concat(mode_summary_rows).to_csv(
            TBL_DIR / "mode_summary_all.csv", index=False, encoding="utf-8-sig"
        )

    # 跨数据集 per-wheel 汇总
    if summaries:
        pd.concat(summaries.values()).to_csv(
            TBL_DIR / "per_wheel_all.csv", index=False, encoding="utf-8-sig"
        )

    # 过冲改进前后对比表
    overshoot_rows = []
    for key, summ in overshoots.items():
        row = {"dataset": key, "label": parsed[key]["label"], **summ}
        overshoot_rows.append(row)
    overshoot_compare_df = pd.DataFrame(overshoot_rows)
    overshoot_compare_df.to_csv(
        TBL_DIR / "overshoot_compare.csv", index=False, encoding="utf-8-sig"
    )

    # ---------- 3) 绘图 ----------
    # Fig 1/2/3/4 选 bug 数据集（主线案例）
    main_key = BEFORE_KEY if BEFORE_KEY in parsed else next(iter(parsed))
    main_d = parsed[main_key]
    if not main_d["cmd"].empty:
        fig1_body_cmd(main_d["cmd"], seg_by_key.get(main_key, []), main_d["label"], FIG_DIR)
    fig2_cmd_per_wheel(main_d["log_by_w"], main_d["label"], FIG_DIR)
    fig3_fb_per_wheel(main_d["log_by_w"], main_d["label"], FIG_DIR)
    fig4_errors(main_d["log_by_w"], main_d["label"], FIG_DIR)

    # Fig 5：bug 中"窗口最长 + 堆叠峰值最大"的事件（最有代表性）
    if events_by_key.get(BEFORE_KEY):
        evs = events_by_key[BEFORE_KEY]
        # 选 stack_peak_vx 最大的事件（典型）
        ev = max(evs, key=lambda e: (e.window_cmd_len, e.stack_peak_vx))
        fig5_overshoot_zoom(parsed[BEFORE_KEY]["cmd"], parsed[BEFORE_KEY]["aligned"], ev, FIG_DIR)

    # Fig 6：改进前 vs 改进后 同类事件对比
    before_event = None
    after_event = None
    if events_by_key.get(BEFORE_KEY):
        before_event = max(
            events_by_key[BEFORE_KEY],
            key=lambda e: (e.window_cmd_len, e.stack_peak_vx),
        )
    if events_by_key.get(AFTER_KEY):
        after_event = max(
            events_by_key[AFTER_KEY],
            key=lambda e: (e.window_cmd_len, e.stack_peak_vx),
        )
    if before_event is not None or after_event is not None:
        fig6_before_after(
            parsed.get(BEFORE_KEY, {}).get("cmd", pd.DataFrame()),
            before_event,
            parsed.get(AFTER_KEY, {}).get("cmd", pd.DataFrame()),
            after_event,
            FIG_DIR,
        )

    # Fig 7：跟随 RMSE / max|e| 改进前 vs 改进后
    pair = {}
    if BEFORE_KEY in summaries:
        pair[parsed[BEFORE_KEY]["label"]] = summaries[BEFORE_KEY]
    if AFTER_KEY in summaries:
        pair[parsed[AFTER_KEY]["label"]] = summaries[AFTER_KEY]
    if pair:
        fig7_rmse_compare(pair, FIG_DIR)

    # Fig 8：过冲事件指标对比（含 baseline / bug / improved_v1 / improved_final）
    fig8_inputs = {parsed[k]["label"]: overshoots[k] for k in parsed if k in overshoots}
    fig8_overshoot_compare(fig8_inputs, FIG_DIR)

    # ---------- 4) 论文回填指标 JSON ----------
    metrics_for_thesis: dict[str, str] = {}

    # 4.1 数据规模
    for key, d in parsed.items():
        st = d["stats"]
        metrics_for_thesis[f"lines_{key}"] = str(st.total_lines)
        metrics_for_thesis[f"s3cmd_{key}"] = str(st.s3cmd_records)
        metrics_for_thesis[f"s3log_{key}"] = str(st.s3log_records)
        metrics_for_thesis[f"recv_{key}"] = str(st.recv_headers)

    # 4.2 三轮跟随性能（改进前后）
    for key in (BEFORE_KEY, AFTER_KEY):
        df = summaries.get(key)
        if df is None or df.empty:
            continue
        for _, row in df.iterrows():
            w = int(row["w"])
            metrics_for_thesis[f"rmse_V_{key}_w{w}"] = _fmt(row["rmse_V"], 4)
            metrics_for_thesis[f"max_eV_{key}_w{w}"] = _fmt(row["max_eV"], 3)
            metrics_for_thesis[f"rmse_A_{key}_w{w}"] = _fmt(row["rmse_A"], 2)
            metrics_for_thesis[f"max_eA_{key}_w{w}"] = _fmt(row["max_eA"], 2)

    # 4.3 过冲事件指标
    for key, summ in overshoots.items():
        for k, v in summ.items():
            metrics_for_thesis[f"ov_{key}_{k}"] = _fmt(v, 3) if isinstance(v, float) else str(v)

    # 4.4 改善百分比（用于结论句）
    if BEFORE_KEY in overshoots and AFTER_KEY in overshoots:
        b = overshoots[BEFORE_KEY]
        a = overshoots[AFTER_KEY]

        def _pct(before, after):
            if before <= 1e-9:
                return "—"
            return f"{(before - after) / before * 100:.1f}%"

        metrics_for_thesis["pct_stack_peak"] = _pct(
            b["stack_peak_max"], a["stack_peak_max"]
        )
        metrics_for_thesis["pct_release_step_mean"] = _pct(
            b["release_step_mean"], a["release_step_mean"]
        )
        metrics_for_thesis["pct_release_step_max"] = _pct(
            b["release_step_max"], a["release_step_max"]
        )
        metrics_for_thesis["pct_events"] = _pct(
            float(b["n_events"]), float(a["n_events"])
        )

    # 4.5 工况时长占比（仅 bug 数据集，作为代表）
    if BEFORE_KEY in seg_by_key:
        from .classify import MODE_LABELS_CN
        segs = seg_by_key[BEFORE_KEY]
        total = sum(s.duration_samples for s in segs) or 1
        for m in ("forward", "translate", "rotate", "compound", "idle"):
            samp = sum(s.duration_samples for s in segs if s.mode == m)
            metrics_for_thesis[f"mode_pct_{m}"] = f"{samp / total * 100:.1f}%"

    (TBL_DIR / "metrics.json").write_text(
        json.dumps(metrics_for_thesis, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[saved] metrics.json with {len(metrics_for_thesis)} keys")

    # ---------- 5) 把指标回填进 thesis/第X章_实验与分析.md ----------
    template = THESIS_DIR / "第X章_实验与分析.md"
    if template.exists():
        text = template.read_text(encoding="utf-8")

        def _sub(m: re.Match[str]) -> str:
            key = m.group(1).strip()
            return metrics_for_thesis.get(key, m.group(0))

        filled = re.sub(r"\{\{([^{}]+)\}\}", _sub, text)
        out_path = THESIS_DIR / "第X章_实验与分析_已回填.md"
        out_path.write_text(filled, encoding="utf-8")
        print(f"[saved] {out_path}")

    print("Done.")


if __name__ == "__main__":
    main()
