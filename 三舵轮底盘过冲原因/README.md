# 三舵轮底盘过冲：实验数据分析与论文素材

本仓库基于现场抓取的串口日志，按"现象 → 机理 → 改进方案 → 改进前后对比"
四步出毕业论文素材，包含一套自动化分析与绘图脚本，以及一份配套的论文章节
Markdown 文稿。

## 目录结构

```
.
├── 底盘数据.txt                   # 早期基线日志（仅 S3LOG）
├── 旋转后前进过冲的bug.txt        # bug 完整复现（S3CMD + S3LOG）
├── 改善后的数据.txt               # 改进 v1（中间版本）
├── 真正修改后的数据.txt           # 改进 v2（最终版本）
├── 过冲原因分析.txt               # 已写好的机理分析（X.5.2 节素材）
├── 改正思路.txt                   # 已写好的改进方案（X.6 节素材）
├── 改善后的数据分析.txt           # 已写好的改善效果分析（X.7 节素材）
├── requirements.txt               # Python 依赖
├── analysis/                      # 分析与绘图代码
│   ├── parse.py                   # 解析 S3CMD / S3LOG
│   ├── classify.py                # 工况分类（前进/平移/旋转/复合/静止）
│   ├── metrics.py                 # 跟随误差与过冲事件检测
│   ├── plot_figures.py            # 图 1 ~ 图 8 绘图
│   ├── run_all.py                 # 一键产出全部图表
│   ├── figures/                   # 输出 PNG（300 dpi）
│   └── tables/                    # 输出 CSV 与 metrics.json
└── thesis/                        # 论文章节文稿
    ├── 第X章_实验与分析.md         # 主章节模板（带 {{占位符}}）
    ├── 第X章_实验与分析_已回填.md  # 自动生成（占位符已替换为实测数值）
    ├── figures_captions.md         # 图题/表题清单（贴到 Word）
    └── references.md               # 术语 / 引用 / 数据来源对照
```

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 一键产出全部论文素材

```bash
python -m analysis.run_all
```

完成后将得到：

- `analysis/figures/fig1_body_cmd.png` ~ `fig8_overshoot_compare.png` —— 8 张论文图；
- `analysis/tables/per_wheel_*.csv`、`overshoot_*.csv`、`segments_*.csv` —— 全部统计 CSV；
- `analysis/tables/metrics.json` —— 论文文本要回填的所有数值；
- `thesis/第X章_实验与分析_已回填.md` —— 已把 `{{占位符}}` 替换为实测数值的章节正文。

### 3. 拼论文

打开 `thesis/第X章_实验与分析_已回填.md` 复制到学校 Word 模板；按
`thesis/figures_captions.md` 插入图片与题注。

## 论文核心结论（来自实测数据）

| 指标 | 改进前 (bug) | 改进 v2（最终） | 下降 |
|---|---|---|---|
| 过冲事件数 | 13 | 4 | 69.2% |
| 堵舵期 cmdVx 堆叠最大值 | 0.350 m/s | 0.237 m/s | 32.3% |
| 释放阶跃最大值 | 0.350 m/s | 0.102 m/s | 70.9% |
| 释放阶跃平均值 | 0.213 m/s | 0.040 m/s | 81.2% |

机理：底盘过冲并非源于"旋转 / 平移工况本身"，而是
**舵未归位时上层 $v_x$ 指令持续累加、舵就绪瞬间一次性释放**——本工程
通过 `KiSteer3_WalkCtrl` 速度整形 + 起步加速度限幅根治该问题。

## 数据局限（论文已诚实写明）

- 三轮 S3LOG 在日志中是**交错**到达的，本文以接收顺序展示，不做严格
  时刻重采样；
- 时间戳来自串口接收端，存在毫秒级抖动，不影响过冲识别但不适合做严格
  频域分析；
- `底盘数据.txt` 不含 S3CMD，只用作辅助说明，主线分析以 bug 与改进 v2
  两份为主。
