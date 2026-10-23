---
name: guizang-tv-install
description: Install GuiZang TV on an owner-authorized Android TV or box, select TCL T-Cast versus standard Android installation, configure opt-in startup and HDMI fallbacks, and optionally install the bundled Xinmiao and TVBox apps. Use for TV setup and brand-specific installation failures; does not root, debloat, or promise all firmware/content sources work.
---

# 归藏电视：TCL 与多品牌安装

目标：保留归藏设计，给用户自己的电视装好桌面，按需添加两款影视应用，交付可核对的状态与恢复记录。只安装桌面不需要电脑常驻、模型账号或 REA。

先定位仓库。该技能和 `tools/`、`packages/` 属于同一个分发包；如果只单独安装了技能，克隆 `https://github.com/guozhuangchao-hub/GUIZANGTV-TCL.git` 到用户工作目录，再从克隆根目录执行下述命令，不从 `~/.codex/skills` 推测 APK 路径。读取仓库 `AGENTS.md` 和 [品牌分支](references/brands.md)。只加载当前品牌需要的内容。

## 检测与最少交互

1. 优先用已有官方 Android Platform Tools 和 Python 3.9+；没有时提供对应系统的官方安装方式。确认电视 IP/配对端口和用户同意安装。ADB 开关、首次授权、电视上的安装“同意”由用户完成；能从探针读取的信息不反复询问。
2. `adb devices -l` 后由用户提供/确认目标 serial，后续每个命令都带 `-s SERIAL`，不选第一台、不自动扫描全网。先运行：
   ```sh
   python3 tools/check_packages.py
   python3 tools/tv_setup.py doctor --serial SERIAL
   python3 tools/tv_setup.py install --serial SERIAL --with-media
   ```
   最后一条只是读取设备、校验包并打印计划。电视低于 API26 停止；32位v7a影视包不能安装到只有arm64-v8a能力的设备，按实际架构找对应上游构建。
3. 已有归藏时核对包名、版本与签名。新仓库的签名不同于上游以及昨天的本地试用包；不能自动卸载来绕过签名冲突，保留数据，使用原签名构建或和用户明确迁移方案。

## 安装与桌面守护

TCL/雷鸟选择 `packages/guizang-tv-tcl-0.4.0.apk`，不声明HOME，优先多屏互动；标准 Android TV（包括部分Sony/Google TV/盒子）选择 `standard` 包。探针结果与品牌表优先于营销型号。

普通安装（不会启用高权限或接管Home）：
```sh
python3 tools/tv_setup.py install --serial SERIAL --tv-ip TV_PRIVATE_IPV4 \
  --with-media --backup /PRIVATE/PATH/guizang-before.json --apply
```
`--tv-ip` 只在TCL多屏互动需要，填写电视自己的IPv4。备份必须在仓库外、路径可写且文件不存在。T-Cast只临时提供选定APK，电视上让用户选同意；安装后本机HTTP服务自动关闭。

若用户要求开机进入/主页键回归藏，解释守护需要悬浮窗、WRITE_SECURE_SETTINGS、无障碍和通知监听授权；代码只监听窗口状态和Home键，不读屏幕正文或处理通知。用户已同意该功能时，沿用授权，加 `--guard` 执行安装命令即可。脚本同时尝试TCL的APP_AUTO_START、APP_ASSOC_START，保留其他无障碍服务；其他品牌可能没有这两项appops。

标准版先走系统默认桌面选择。在用户要求归藏作为默认桌面时，可执行：
```sh
adb -s SERIAL shell cmd package set-home-activity io.github.op7418.guizangtv/.FrameHomeActivity
```
再按Home并读取前台验证；命令显示Success不代表固件真的遵守。Home仍回原桌面时，再根据用户需求启用守护。其他品牌若也拒绝HOME声明，确认是同类限制后可用 `--variant tcl` 选择无HOME构建，并按需守护；传输方式仍按实际品牌选择，不假装存在TCL多屏服务。**不禁用原桌面**。Xiaomi不能停用PatchWall；TCL不能安装声明HOME的包时换TCL包，不改APK验证器。

多屏互动连接失败，先查同网/AP隔离和电视多屏互动服务。该固件没有6553服务则走U盘/电视文件管理器/用户已登录网盘；将APK实际路径在Finder/资源管理器打开让用户配合。不要求用户无谓安装网盘OAuth技能。没有可行安装入口则停止依赖步骤，报告明确限制，不绕到root/刷机。

## 两款影视应用

`--with-media` 安装两个原始包、按已发现应用追加首页入口，保留原有排序/壁纸，满9项时告知用户自行选择隐藏哪一项。不会复制账号和观看记录。每包来源/哈希/架构见 `packages/catalog.json`，第三方许可见 `packages/README.md`。

TVBox第一次安装后配置本地源，不需要电脑常开：
```sh
python3 tools/configure_tvbox.py --serial SERIAL
python3 tools/configure_tvbox.py --serial SERIAL --backup /PRIVATE/PATH/tvbox-before.json --apply
```
该脚本校验配置和解析插件，利用**当前可见的**TVBox“设置 → 配置地址”及它自己的局域网输入接口；不直接写私有app数据。已有源时保留；用户明确要替换才加 `--replace-source`。UI不匹配时通过 `uiautomator dump`/截图看实际界面再操作，不盲发确认键。截图无内容时让用户看电视，不能把黑屏解释为未安装。

本仓库已修复jinenge仓库JSON尾部多拼内容和旧域名插件403造成的**配置加载**问题。部分直播地址带旧参数，曾返回605；这不是电视不兼容，不承诺所有站点可播。先验证目录，再挑一个实际视频，播放成功才能写“可播放”。新喵为用户提供原APK，不是本仓库开发或审核过的影视服务，账号及内容按其实际要求处理。

## 验证与交付

依次验证：包注册/版本 → 遥控器焦点 → 原有设置保留 → 信号源面板和返回 → 用户选定的实际影视播放。只有用户要求自启时才继续完整重启/待机两条路径；重启与电源键会打断播放，先取得对应授权。

冷启动观察前先只读，不手动打开归藏后说它“自启成功”。启动请求、service已绑定、HOME命令成功都不是最终前台证据。分别报告桌面、HDMI、冷启动、唤醒、应用安装和源播放的PASS/FAIL/未测。

卸载前关闭守护：
```sh
python3 tools/tv_setup.py restore --serial SERIAL --backup /PRIVATE/PATH/guizang-before.json --apply
```
该恢复只移除本次自己的服务/监听、恢复appops，保留其他服务和应用数据；原来已有守护时停止自动恢复，按记录核对。若另设过默认Home，恢复备份里的原组件并验证后才卸载。恢复不自动重启。

遇到新的固件接口问题，按 [工具与逆向经验](references/toolbox.md) 获取证据；普通安装不需要安装全套技能或逆向工具。未知设备不套用TCL/小米专用数字。
