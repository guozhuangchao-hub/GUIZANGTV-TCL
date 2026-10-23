# 随附安装包与配置

这是独立分发的第三方应用和归藏构建产物，**不是把第三方应用重新许可成MIT**。所有原始APK未重签、未注入账号或观看记录；安装前运行 `python3 tools/check_packages.py`。版本、包名、ABI、完整SHA256与来源以 [catalog.json](catalog.json) 为准。

| 文件 | 来源与说明 |
|---|---|
| guizang-tv-tcl-0.4.0.apk | 本仓库构建；API26+，不声明HOME；需注意社区签名与原上游/个人试用不同 |
| guizang-tv-standard-0.4.0.apk | 同源码同社区签名，声明标准HOME；适合支持标准桌面选择的Android TV |
| xinmiao-1.1.2.apk | 用户提供，来自其小米盒子正在使用的新喵影视1.1.2，包名com.mygithub0.tvbox0.apei583，原证书未变；公开分发许可未找到可核实声明，作者/服务方权益不因本仓库而改变 |
| TVBox_q215613905_20260914-1520-java32.apk | j4Uq/TVBoxOSC正式release原文件；v7a32位；上游AGPL-3.0 |
| sourceCode-ab11d28.tar.xz | 与上述TVBox APK同一release提供的对应源码，原样携带；SHA256也纳入校验 |

TVBox源码许可证全文：[AGPL-3.0](licenses/TVBox-AGPL-3.0.txt)。上游源码链：q215613905/TVBoxOS ab11d289e09963a9daf65ca7f6b7a9a8cbe184e1；发布页 https://github.com/j4Uq/TVBoxOSC/releases/tag/20260914-1520 。维护者更新APK时必须同时更新其对应源码与校验记录，不套用本仓库代码许可。

新喵来源仅为用户提供的原安装包，不是已验证的官方发布或本仓库维护的客户端，未获得“开源”或“内容全部可用”的结论。若权利人需要调整分发，请在仓库Issue联系。账号、授权、内容可用性以应用实际要求为准。

## TVBox本地配置

`tvbox-config/` 来自 jinenge/tvbox fd551fc9cdedb4b130e4692972bf116bb08ffa57 的有效配置对象与其lib，独立适用 [MPL-2.0](licenses/jinenge-MPL-2.0.txt)。仓库原始tvbox.json在完整对象后多拼接了一段；此处采用与作者在线配置相同的完整对象，42站，不含尾部多余内容。未更换站点/解析逻辑；插件MD5为1d7a5147033044a81f91d5f4a510f9ed。

配置脚本把文件存到电视 `Download/GuiZangTV/tvbox`，源地址为 `clan://localhost/Download/GuiZangTV/tvbox/tvbox.json`。解析插件从本机加载，避免旧域名403和电视直连GitHub超时；不是电脑HTTP常驻服务。

修复配置语法/插件路径不代表每个来源可播。特别是原直播列表里的临时签名可能已过期，曾实测605。已有用户配置默认保留，只有显式要求替换时才使用 `--replace-source`。不要把下载或播放失败当成需要root电视的理由。
