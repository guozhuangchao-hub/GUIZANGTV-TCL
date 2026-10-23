# 来源与许可

- 初始工程参考与衍生基础：Gathin23/cleanyourtv，MIT License。
  - https://github.com/Gathin23/cleanyourtv
  - 本地定制基线：`69c93b66a75c70a9e386adff327b6a51c12addc5`
  - 原始版权：Copyright (c) 2026 Gathin，保留于根目录 LICENSE。
- 设计与设置交互参考：nthnclrk/CleanFrame，Nathan Clark。
  - https://github.com/nthnclrk/CleanFrame
  - 参考版本：`fa537d1892b71d2de2bf94c24cbff3812e9f70d5`
  - 参考其分组、首页预览、焦点与已应用值分离、确认应用和逐层返回的交互。
  - 本项目没有打包其 Tizen 代码、字体或照片。
  - 图标采用下述开源 SVG，不打包 Android 应用的原始图标。
- 默认渐变、布局示意及本项目绘制代码采用 MIT 许可。
- 品牌 SVG：Simple Icons，CC0-1.0；工具 SVG：Phosphor Icons Fill（勾选与箭头为 Regular），MIT。原 SVG、精确提交来源与许可证位于 `app/src/main/assets/icons/`；Android VectorDrawable 是同一路径数据的格式转换。商标权不因图标的开源许可而转移。
- 使用 Android 系统字体，不打包 Outfit 字体。
- Android Gradle Plugin、Gradle 与 JUnit 是构建或测试依赖，各自适用其许可证；不代表被重新许可为 MIT。
- 各产品与商标归其权利人所有。本项目不隶属于小米、Sony、Apple 或哔哩哔哩。

v0.1.1 起，内置五张经原页面核对的 Unsplash 照片，适用 **Unsplash License**，不适用代码的 MIT 许可。逐张署名、原始链接和处理方式见 [壁纸说明](docs/WALLPAPERS.md)，许可通知也随 APK 打包。

用户自行加入的照片不因放入本工程而自动获得 MIT 许可。其他未授权公开的私人试用素材、实机诊断数据、签名密钥均不在公开源代码或官方 APK 中。

## 本社区TCL分支

- 上游归藏电视：op7418/guizang-tv v0.3.0，2c51b096d5fc34de6cff1add14bb79a60b5bdce0。保留归藏的设计、实现与上游署名。
- Tigris：lesnolie/Tigris cf06fa3bd39968c890f4206e360105155d1842bf，Copyright (c) 2026 lesnolie，MIT。参考窗口守护、通知监听恢复、多屏互动协议、标准TV输入与酷开选择器经验。
- Aerial：pengchujin/aerial-tv，Copyright (c) 2026 pengchujin，MIT。Tigris引用的厂商实机经验和多屏互动协议来源。
- 完整MIT通知随APK保留于 app/src/main/assets/THIRD_PARTY_TCL.txt，适用于本次衍生守护及 tools/tcast_push.py。
- packages/第三方APK、对应源码和内容源各自独立授权，详见packages/README.md和licenses；不因同库分发变为MIT。
