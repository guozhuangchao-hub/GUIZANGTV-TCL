# 昨天用过什么工具、何时需要它

| 工具/技能 | 解决的问题 | 本仓库如何复用 |
|---|---|---|
| 官方ADB | 读取型号/API/ABI、签名和前台；提取用户盒子里的正确APK；验证权限与安装 | tools/tv_setup.py显式目标、前置计划、私有备份；不用全网扫描 |
| Tigris/Aerial源码 | TCL拒绝adb install/HOME声明、开机后台拦截、系统主页覆盖第三方 | TCL无HOME包、多屏互动推送、两项appops、可选窗口守护；保留MIT署名 |
| REA / reverse-engineer-anything | 逆向TCL已安装系统APK，找到真正导出入口和Source服务调用，排除不能启动的内部Activity | 仅在固件接口未知且用户允许分析时使用；不是每次安装都逆向 |
| cleanyourtv设备笔记 | 了解厂商系统限制及不能随意删的组件 | 参考而不执行一键debloat；原桌面、投屏、语音助手、直播组件保留 |
| baidu-drive技能/百度网盘客户端 | 多屏互动尚未找到时，用用户自己已登录网盘把APK带到电视 | 先选可用的本地/多屏方式；网盘是回退，不为一份APK要求完整OAuth配置。此次由用户手工上传，并非skill自动上传 |
| skill-installer | 正确定位并安装所需第三方技能的实际子目录 | 不是看到仓库URL就把根目录当SKILL；只在确实需要时安装 |
| ponytail | 避免为一次安装另起永久后台或庞大框架 | Python标准库、原生Android、复用现成APK/系统入口 |
| Chrome/browser/页面工具 | 阅读项目说明、查发布版本及校验值 | 可用CLI时优先gh/git；不需要把网页自动化挂在电视运行路径里 |
| aapt2、javac、d8、zipalign、apksigner | 没有Gradle时使用已安装SDK构建并验证APK/ABI/签名 | scripts/build_local.py；安装用户不需要安装这些开发工具 |

## 新固件需要REA时

先只读提取本机组件与版本：`pm path com.tcl.settings`、`dumpsys package`、`dumpsys tv_input`。用户授权后把需要的系统APK pull到仓库外的私有目录；不要公开整套厂商APK、账号数据和原始日志。

按已安装REA实际工具选择Android包清单→精确类/方法，不为普通源码阅读启动逆向全家桶。曾用的CLI形式：

```sh
rea inspect-android-package /PRIVATE/TCL-Settings.apk --format json
rea inspect-android-method /PRIVATE/TCL-Settings.apk FULL.CLASS METHOD --format json
```

方法名/参数从实际清单获得，不猜。REA/JADX引擎未就绪时按其技能说明修复；`rea-agents@6.4.0`是本次环境对齐版本记录，不是永久最新版本要求。

本次确认 `com.tcl.settings/.ShowWindowService` 的 `com.tcl.settings.SHOW_WINDOW` + `flag=1` + `Type=Source` 能打开原生信号源面板；直接调内部自定义源Activity会被exported限制。源码/静态分析只说明候选接口，仍要在目标固件观察实际行为。

普通APK改名、签名冲突、网络不可达、源605和JSON语法损坏都不需要root。用户授权root不意味着为了普通安装就应该root；优先已验证的系统安装入口。
