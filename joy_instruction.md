# 底层原理
## 手柄处
手柄里面有两类输入：

摇杆：模拟量，本质上是电位器或霍尔传感器，输出连续值。
按键：数字量，按下是 1，松开是 0。
比如左摇杆上下，硬件会产生一个连续值。推到最前可能是最大值，回中是 0，拉到最后是最小值。

手柄通过 USB 或蓝牙把这些状态打包成 HID 报告发给电脑。HID 是 Human Interface Device，人机输入设备协议，键盘、鼠标、手柄都属于这一类。
## 主机处
Linux 收到 HID 数据后，不是让应用程序直接读 USB 数据，而是交给内核 input 子系统统一处理。

内核会创建设备文件，例如：

/dev/input/js0
/dev/input/event5
其中：

/dev/input/js0 是 joystick 接口，比较简单，专门给手柄用。
/dev/input/eventX 是 evdev 接口，更通用，键盘鼠标手柄都可以走这个。
## ros2处

### 接受消息
joy_node 是 ROS 2 的手柄驱动节点。它的工作很单纯：

打开 /dev/input/js0。
循环读取手柄事件。
把 Linux 的轴/按键事件转换成 ROS 消息。
发布到 /joy 话题。
/joy 的消息类型是：

sensor_msgs/msg/Joy
它里面主要有两个数组：

axes:    float32[]  # 摇杆、扳机等模拟量
buttons: int32[]    # 按键
例如常见 Xbox 风格手柄可能是：

axes[0] = 左摇杆左右
axes[1] = 左摇杆上下
axes[3] = 右摇杆左右
buttons[4] = LB
buttons[5] = RB
注意：这个编号不是绝对固定的，不同手柄可能不一样。所以调试时要看：

ros2 topic echo /joy
你推哪个摇杆，观察哪个 axes[i] 在变；按哪个按钮，观察哪个 buttons[i] 变成 1。

### 手柄映射
joy_node 发布的是原始手柄数据 /joy，机器人通常不直接使用。中间的 teleop_twist_joy 会把它转换成标准机器人速度 /cmd_vel。

你的配置是：

teleop_twist_joy.yaml
Lines 1-22
teleop_twist_joy_node:
  ros__parameters:
    require_enable_button: true
    enable_button: 4
    enable_turbo_button: 5
    axis_linear:
      x: 1
      y: 0
    scale_linear:
      x: 0.65
      y: 0.65
    scale_linear_turbo:
      x: 1.0
      y: 1.0
    axis_angular:
      yaw: 3
    scale_angular:
      yaw: 1.2
    scale_angular_turbo:
      yaw: 1.8
底层换算逻辑可以理解成：

cmd_vel.linear.x  = joy.axes[1] * 0.65
cmd_vel.linear.y  = joy.axes[0] * 0.65
cmd_vel.angular.z = joy.axes[3] * 1.2
按住高速键 RB 时：

cmd_vel.linear.x  = joy.axes[1] * 1.0
cmd_vel.linear.y  = joy.axes[0] * 1.0
cmd_vel.angular.z = joy.axes[3] * 1.8
require_enable_button: true 的意思是必须按住使能键，否则即使摇杆有输入，也不会发布有效运动速度。这是为了安全。


## 总结
手柄接收的底层原理是：Linux 把手柄抽象成输入设备，ROS 的 joy_node 把设备事件转成 /joy，teleop_twist_joy 再把 /joy 映射成机器人通用速度 /cmd_vel，最后你的四舵轮节点把 /cmd_vel 解算成每个轮子的舵角和转速。
