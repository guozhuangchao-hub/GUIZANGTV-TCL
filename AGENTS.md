# GuiZang TV TCL：给安装与开发 Agent

用户当前指令优先。先读 README.md 和 skills/guizang-tv-install/SKILL.md；按品牌再读 docs/COMPATIBILITY.md。

- 本仓库基于 op7418/guizang-tv 的 v0.3.0；保留设计、作者与许可。没有 main 上较新 Codex 对话功能，不要引导用户寻找该菜单。
- 安装操作只针对用户指定的 ADB serial，每条命令必须 `-s`。Python 工具默认只读计划，`--apply` 才写入。没有用户要求安装时不访问设备。
- 不把一台设备的成功说成全品牌实测。写明桌面安装、遥控器、信号源、开机、待机唤醒、影视源播放分别的结果。
- TCL 用不声明 HOME 的 tcl 包。ADB 安装验证失败转多屏互动或电视本地安装，不改验证器，不root，不禁用原桌面或系统组件。
- 标准版用于支持标准 HOME 的 Android TV。品牌名不等于固件能力；其他国产电视按探针结果回退，不能套用小米HDMI数字或TCL appops。
- 启用守护会处理Home键并增加悬浮窗、WRITE_SECURE_SETTINGS、无障碍和通知监听授权；说明目的，沿用当前明确授权，不把普通安装默认为所有权限授权。
- 备份留在仓库外，权限0600；保留其他无障碍服务，不清空用户的系统配置。签名不匹配时停下，不自动卸载丢数据。
- APK来源/校验/许可见 packages/catalog.json 与 packages/README.md；第三方包及内容源不自动适用根MIT许可证。新喵不是本项目开发，来源为用户提供的安装包，公开授权状态未核实。
- 安装TVBox不等于每条源可播放；源的JSON、解析插件、目录、实际视频分别验证。已有源不覆盖，除非用户明确要替换。
- 保留源码、凭证、ADB密钥、用户日志、IP/序列号及私人壁纸在仓库外。不要提交本机签名私钥或其密码。
- 改动跑对应Java/Python测试；构建两个manifest变体，检查HOME差异。无设备时只报告离线验证。
