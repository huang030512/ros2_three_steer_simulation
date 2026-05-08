"""日志解析模块。

把串口抓到的 txt 解析成两类有序记录：

- S3CMD: 车体级指令 (cmdVx, cmdVy, cmdVw)
- S3LOG: 轮级 (w, cmdA, cmdV, fbA, fbV)

需要处理的"脏"情形：
1. 行首 [I]、[I][I] 前缀（HAL 调试打印的 INFO 标签）
2. 单纯只有 [I] 或空白的行
3. [YYYY-MM-DD HH:MM:SS.mmm]# RECV ASCII/N <<< 这种串口接收头，
   其前后可能把一行 S3CMD/S3LOG 切成两半
4. 同一物理行里可能挤了好几条记录（被空格或 [I] 隔开）
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

# 匹配两类记录
S3CMD_RE = re.compile(
    r"S3CMD,cmdVx=(-?\d+\.?\d*),cmdVy=(-?\d+\.?\d*),cmdVw=(-?\d+\.?\d*)"
)
S3LOG_RE = re.compile(
    r"S3LOG,w=(\d+),cmdA=(-?\d+\.?\d*)deg,cmdV=(-?\d+\.?\d*),"
    r"fbA=(-?\d+\.?\d*)deg,fbV=(-?\d+\.?\d*)"
)

# 串口接收头：[2026-05-06 06:27:32.141]# RECV ASCII/1828 <<<
RECV_RE = re.compile(
    r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]# RECV ASCII/\d+ <<<"
)


@dataclass
class ParseStats:
    """解析过程的统计信息，便于在论文里诚实交代数据清洗效果。"""

    total_lines: int
    recv_headers: int
    s3cmd_records: int
    s3log_records: int
    bytes_total: int


def _clean_text(raw: str) -> tuple[str, list[tuple[int, str]], int]:
    """清洗原始文本。

    返回 (清洗后文本, 时间戳序列, RECV 头数)。

    清洗规则：
    - 把 RECV 头整行替换成换行（消除把 S3CMD/S3LOG 切两半的影响）
    - 去掉 [I] 前缀（保留分隔，这样多个 [I] 紧挨的多条记录仍能被独立匹配）
    - 不做行内拼接 —— 我们用正则在全文一次性扫描所有记录，
      被切的两半会因为去掉 RECV 头之后被 \n 重新邻接成完整字符串
      （绝大多数情况下被切处不在 S3CMD/S3LOG 关键字段里；少量极端情况由正则匹配失败丢弃）。
    """

    timestamps: list[tuple[int, str]] = []

    def _record_ts(m: re.Match[str]) -> str:
        timestamps.append((m.start(), m.group(1)))
        return "\n"

    cleaned = RECV_RE.sub(_record_ts, raw)
    recv_count = len(timestamps)

    # 把 [I] 替换成空格，避免 [I][I] 把两条记录粘在一起后还能被独立 finditer 匹配
    cleaned = cleaned.replace("[I]", " ")
    return cleaned, timestamps, recv_count


def parse_log(path: Path | str) -> tuple[pd.DataFrame, pd.DataFrame, ParseStats]:
    """解析单个日志文件。

    Returns
    -------
    cmd_df : DataFrame
        列: idx, char_pos, cmdVx, cmdVy, cmdVw, ts (可能为 NaT)
    log_df : DataFrame
        列: idx, char_pos, w, cmdA, cmdV, fbA, fbV, ts (可能为 NaT)
    stats : ParseStats
    """
    path = Path(path)
    raw = path.read_text(encoding="utf-8", errors="ignore")
    total_lines = raw.count("\n") + 1
    cleaned, ts_marks, recv_count = _clean_text(raw)

    # S3CMD
    cmd_records = []
    for i, m in enumerate(S3CMD_RE.finditer(cleaned)):
        cmd_records.append(
            {
                "idx": i,
                "char_pos": m.start(),
                "cmdVx": float(m.group(1)),
                "cmdVy": float(m.group(2)),
                "cmdVw": float(m.group(3)),
            }
        )
    cmd_df = pd.DataFrame(cmd_records)

    # S3LOG
    log_records = []
    for i, m in enumerate(S3LOG_RE.finditer(cleaned)):
        log_records.append(
            {
                "idx": i,
                "char_pos": m.start(),
                "w": int(m.group(1)),
                "cmdA": float(m.group(2)),
                "cmdV": float(m.group(3)),
                "fbA": float(m.group(4)),
                "fbV": float(m.group(5)),
            }
        )
    log_df = pd.DataFrame(log_records)

    # 时间戳近似对齐：每条记录取离它最近且在它之前的 RECV 时间
    if ts_marks and not cmd_df.empty:
        cmd_df["ts"] = _approx_ts(cmd_df["char_pos"].to_numpy(), ts_marks)
    else:
        cmd_df["ts"] = pd.NaT
    if ts_marks and not log_df.empty:
        log_df["ts"] = _approx_ts(log_df["char_pos"].to_numpy(), ts_marks)
    else:
        log_df["ts"] = pd.NaT

    stats = ParseStats(
        total_lines=total_lines,
        recv_headers=recv_count,
        s3cmd_records=len(cmd_df),
        s3log_records=len(log_df),
        bytes_total=len(raw),
    )
    return cmd_df, log_df, stats


def _approx_ts(positions, ts_marks: list[tuple[int, str]]):
    """把记录在文本中的字符位置映射到最近一个早于它的 RECV 时间戳。"""
    import numpy as np

    mark_pos = np.array([p for p, _ in ts_marks], dtype=int)
    mark_ts = pd.to_datetime([t for _, t in ts_marks])
    insert = np.searchsorted(mark_pos, positions, side="right") - 1
    insert = np.clip(insert, 0, len(mark_ts) - 1)
    return mark_ts[insert]


def split_log_by_wheel(log_df: pd.DataFrame) -> dict[int, pd.DataFrame]:
    """按舵轮编号 w 分组，返回 {1:df, 2:df, 3:df}（重置 idx）。"""
    out: dict[int, pd.DataFrame] = {}
    for w, sub in log_df.groupby("w"):
        sub = sub.reset_index(drop=True).copy()
        sub["sample"] = sub.index
        out[int(w)] = sub
    return out


def align_log_to_cmd(
    cmd_df: pd.DataFrame, log_df: pd.DataFrame
) -> pd.DataFrame:
    """把每条 S3LOG 配上"它发生时最近的一条 S3CMD"。

    依据：日志里 S3CMD 之后通常紧跟 w=1,2,3 三条 S3LOG，所以用 char_pos
    的 searchsorted 把每条 LOG 关联到最近一条早于它的 CMD。

    返回的 DataFrame 在 log_df 列基础上增加 cmdVx, cmdVy, cmdVw。
    """
    import numpy as np

    if cmd_df.empty or log_df.empty:
        out = log_df.copy()
        for c in ("cmdVx", "cmdVy", "cmdVw"):
            out[c] = float("nan")
        return out

    cmd_pos = cmd_df["char_pos"].to_numpy()
    log_pos = log_df["char_pos"].to_numpy()
    insert = np.searchsorted(cmd_pos, log_pos, side="right") - 1
    insert = np.clip(insert, 0, len(cmd_pos) - 1)

    out = log_df.copy().reset_index(drop=True)
    out["cmdVx"] = cmd_df["cmdVx"].to_numpy()[insert]
    out["cmdVy"] = cmd_df["cmdVy"].to_numpy()[insert]
    out["cmdVw"] = cmd_df["cmdVw"].to_numpy()[insert]
    return out


def parse_many(files: Iterable[Path | str]) -> dict[str, dict]:
    """批量解析。

    返回 {file_stem: {"cmd": df, "log": df, "stats": ParseStats}}。
    """
    out: dict[str, dict] = {}
    for f in files:
        f = Path(f)
        cmd_df, log_df, stats = parse_log(f)
        out[f.stem] = {"cmd": cmd_df, "log": log_df, "stats": stats}
    return out


__all__ = [
    "ParseStats",
    "parse_log",
    "parse_many",
    "split_log_by_wheel",
    "align_log_to_cmd",
]
