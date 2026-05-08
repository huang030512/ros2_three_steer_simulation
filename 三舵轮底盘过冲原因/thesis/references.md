# 论文术语 / 引用对照

> 用于答辩前快速核对"哪段文字 / 哪个数字 / 哪张图"对应到工程里的哪一份原始资料。

## 术语对照

| 论文表述 | 代码 / 文件中的表述 | 备注 |
|---|---|---|
| 车体级指令 | S3CMD（cmdVx / cmdVy / cmdVw） | 由上层运动规划/遥控下发 |
| 轮级指令 | S3LOG 中的 cmdA / cmdV | 控制器逆运动学解算后下发 |
| 轮级反馈 | S3LOG 中的 fbA / fbV | 来自舵向编码器与行走电机编码器 |
| 工况 | mode ∈ {idle, forward, translate, rotate, compound} | 见 X.3.1 节阈值判据 |
| 过冲事件 | OvershootEvent | 见 X.5.1 节定义 |
| 堵舵期 | stack period | cmdV=0 但 cmdVx≠0 的窗口 |
| 释放阶跃 | release step | cmdV 首次脱离 0 的台阶高度 |
| 舵角残余 | fbA residual | 释放瞬间任一轮 max|fbA-cmdA| |
| 速度整形函数 | KiSteer3_WalkCtrl | 在 X.6 节提出 |

## 文字段落引用对照

| 论文章节 | 引用源 |
|---|---|
| X.5.1 现象描述 | [过冲原因分析.txt](../过冲原因分析.txt) |
| X.5.2 机理分析 | [过冲原因分析.txt](../过冲原因分析.txt) 第 27 行结论句 |
| X.6 改进方案 | [改正思路.txt](../改正思路.txt) |
| X.7.1 同类事件对比 | [改善后的数据分析.txt](../改善后的数据分析.txt) 第 18~26 行 |
| X.7.2 量化指标对比 | [改善后的数据分析.txt](../改善后的数据分析.txt) 第 32~36 行 |

## 图表数据来源对照

| 图/表 | 数据来源 | 生成代码 |
|---|---|---|
| 图 1 | bug 数据集 S3CMD + 工况分类 | [analysis/plot_figures.py](../analysis/plot_figures.py) `fig1_body_cmd` |
| 图 2/3/4 | bug 数据集 S3LOG（按轮 w 分组） | `fig2_cmd_per_wheel` / `fig3_fb_per_wheel` / `fig4_errors` |
| 图 5 | bug 数据集中堆叠峰值最大、窗口最长的事件 | `fig5_overshoot_zoom` |
| 图 6 | bug 数据集 + 改进 v2 数据集 各取代表性事件 | `fig6_before_after` |
| 图 7 | bug / 改进 v2 的 per_wheel 统计 | `fig7_rmse_compare` |
| 图 8 | baseline / bug / v1 / v2 的过冲事件汇总 | `fig8_overshoot_compare` |
| 表 X-2 | parse stats | `analysis/run_all.py` 4.1 节 |
| 表 X-3 | per_wheel_summary（bug） | `analysis/run_all.py` 4.2 节 |
| 表 X-4 | overshoot_summary 对比 | `analysis/run_all.py` 4.3 节 |
| 表 X-5 | per_wheel_summary 对比 | `analysis/run_all.py` 4.2 节 |
