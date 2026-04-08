#!/usr/bin/env python3
"""
三舵轮运动学辅助（与 urdf 中轮位一致：前 +X，左后、右后 120°/240°）。

机体系速度 v = [vx, vy, wz]（前向为 +x，左侧为 +y，逆时针 wz 为正）。
每轮：舵角 beta_i（相对机体系 X 轴，逆为正），轮心线速度 s_i = r_wheel * omega_i。

平面刚体在轮接地点的速度约束可写为线性关系 A(beta) @ [s0,s1,s2]^T = v_body；
给定 (vx,vy,wz) 与舵角 beta，可用最小二乘或解析式求轮速。

此处仅提供几何常数，便于你在控制器中接入完整雅可比或优化求解。
"""
import math

# 与 three_steer.urdf.xacro 中 steer_wheel 宏一致（米）
R_TRIANGLE = 0.32
R_WHEEL = 0.07

# 三台舵轮在机体系中的方位角（从 +X 逆时针，弧度）
ALPHA = (
    0.0,
    2.0 * math.pi / 3.0,
    4.0 * math.pi / 3.0,
)

# 接地点位置（机体系），前轮到 +X，后两轮 120° / 240°
def wheel_positions():
    r = R_TRIANGLE
    return (
        (r, 0.0),
        (r * math.cos(ALPHA[1]), r * math.sin(ALPHA[1])),
        (r * math.cos(ALPHA[2]), r * math.sin(ALPHA[2])),
    )


def main():
    for i, p in enumerate(wheel_positions()):
        print(f"wheel {i}: xy = ({p[0]:.4f}, {p[1]:.4f})")


if __name__ == "__main__":
    main()
