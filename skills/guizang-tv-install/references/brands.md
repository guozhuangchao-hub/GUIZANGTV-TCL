# 品牌路由与已知坑

| 设备/能力 | 安装与Home | 信号源/设置 | 本项目证据 |
|---|---|---|---|
| TCL85J8L / tcl_mt5879_cn / Android11 | TCL包；多屏互动6553推送；APP_AUTO_START和APP_ASSOC_START；可选窗口守护 | ShowWindowService + Type=Source；检查服务导出/权限 | 同源TCL5冷启动稳定记录、TCL6用户继续使用；公开0.4包本次只离线验证 |
| 其他TCL/雷鸟 | 先探测品牌、API、现有包和多屏互动；没有服务则本地安装 | 同组件必须存在/导出/权限允许；否则标准TV输入回退 | Tigris/Aerial参考，不能视为同型号实测 |
| 已适配小米MiTV-MTSU0 Android14 | 普通应用试用；旧的start_3rd_app一次性入口保留；默认桌面选择可能被固件忽略 | input23/24只对这一固件验证；不复制到其他机型 | 上游私人同源实测记录 |
| 其他小米/红米/盒子 | ADB或电视本地安装；不能禁用com.mitv.tvhome，避免开机黑屏；待机可能force-stop第三方并清无障碍 | 优先系统TvInputManager，系统不提供时说明限制 | Tigris/Aerial经验；本分支未完成其他小米实测 |
| Sony BRAVIA / Google TV / 标准Android TV | standard包声明HOME，先验证系统默认桌面；不需要时不授予守护权限 | 系统TV输入框架与Settings；Sony IP-control属于额外可选适配，未移植也不强行改亮度 | 当前为标准API与上游参考，未在Sony实测 |
| Skyworth/Coocaa | 依实际ADB/本地安装入口；Home不遵守时可选守护 | 标准输入列表为空时尝试可导出的SourceDialogActivity | Tigris本身亦标注未实机验证；本分支未实测 |
| Hisense及其他Android品牌 | 能安装不代表支持换Home；先普通应用、再系统默认，最后按需守护 | 标准API，组件不存在就停在普通桌面能力 | 未实测；不宣称支持非Android的VIDAA/webOS/Tizen |

- Android低于8/API26不是本APK支持范围；设备“智能电视”不代表它运行Android。
- TCL/小米开ADB入口随固件变化。TCL“本机信息→上下左右”只作为候选；用户说无变化时看实际菜单/版本，不反复让用户盲按。小米通常关于页面连续按产品型号，随后账号与安全/开发者选项；也要看具体固件。
- Android11以后部分设备使用无线调试配对与动态端口，不能一律写5555。
- 现代Android的后台启动、动态receiver、精确闹钟规则与旧Android不同。本分支含API33动态receiver标志和无精确闹钟授权的回退；仍需设备验证。
- 32位系统不能运行只有arm64的APK；64位芯片也可能运行32位Android。看abilist，不看CPU宣传。
- HDMI截图可能黑屏，需用户现场观察；信号源菜单打开、取消回桌面、实际HDMI画面是不同检查。
- TCL启动可先进入系统主页再由守护回归藏，不能承诺抹掉厂商开机动画。应用/HDMI正在前台时不应该循环抢回。

主要参考：Tigris cf06fa3bd39968c890f4206e360105155d1842bf README、AGENTS与tv/*Adapter；Aerial的同类守护经验。引用不等于本项目完成实测。
