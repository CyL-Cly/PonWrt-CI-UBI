# PonWrt-CI-XG-040G-MD-UBI

为已经使用 all-in-UBI 布局的 Nokia XG-040G-MD 编译 PonWrt。
该仓库只保存 CI、编译配置、第三方包导入脚本和文件覆盖层；编译时拉取
[pbs05/ponwrt](https://github.com/pbs05/ponwrt) 源码。

## 为什么使用独立 CI 仓库

当前需求是迁移自己的软件包选择并试用 PON 功能。独立 CI 仓库可以保持原
[ImmortalWrt CI](https://github.com/Kahen/ImmortalWrt-CI-XG-040G-MD-UBI)
的版本与构建流程，同时单独验证 PonWrt。后续跟进上游只需调整源码版本，
无需合并整个固件源码仓库。需要修改 PON 驱动、DTS 或向上游提交补丁时，
再 fork PonWrt，并把 SOURCE_REPO 改为自己的 fork。

## 固定目标

| 项目 | 设置 |
| --- | --- |
| Source | pbs05/ponwrt |
| 默认源码版本 | c3b518baec8ed0cc5a353327fa154f38bde1e6c0 |
| Target / Subtarget | airoha / an7581 |
| Device | nokia_xg-040g-md-ubi |
| 普通升级镜像 | *-nokia_xg-040g-md-ubi-squashfs-sysupgrade.itb |
| 恢复镜像 | *-nokia_xg-040g-md-ubi-initramfs-recovery.itb |

不使用上游 configs/an7581.config 中的多机型选择，不构建 MD USB-SFP、TF、MF
或非 UBI 机型。使用 MD 内置 PON 光口。

## 迁移内容

- 保留原 config/xg040g-md-ubi.config 中的 NPU 固件、诊断、USB 与文件系统选择。
- 保留原 config/general-packages.config 的软件包基线：OpenClash、Lucky、
  GecoosAC、Samba4、UPnP、WOL Ultra、Footstrap、中文 LuCI 等。
  原 autocore-arm 选项已不存在，使用仍可用的 autocore 包。
- 保留原第三方包来源和 Footstrap 首次启动配置。
- 自动重启插件从官方 LuCI 单独导入，并修正其相对 luci.mk 路径，保持它在
  本源码版本中的编译配置可用。
- 新增 pon-packages.config：PON frontend、EN7572、xPON MAC 驱动，
  airoha-ponctl、airoha-pond、PON 调试工具与 luci-app-pon。
- 显式选择旧 CI 的关键运行依赖（dnsmasq-full、bash、ip-full、Ruby/YAML、
  unzip 等），合并 PonWrt release.config 的桥接卸载、透明代理等网络模块。
- 使用与上游一致的 Ubuntu 24.04 构建环境。
- 使用 config/feeds.conf 固定与源码同期的 feeds；避免最新 packages feed 的
  input-support 等依赖超前于 PonWrt 源码，导致旧配置悄悄失效。
- 对解析后的 .config、实际镜像 metadata、profiles.json 和 rootfs manifest
  执行目标与关键包校验，失败时不上传固件或发布 Release。

config/required-packages.txt 中的包必须保留。其他旧配置中的符号如果被上游删除、
改名或无法满足依赖，会列入 requested-packages-dropped.txt；这不等于所有可选包
都已验证运行正常。

## 创建并运行

1. 在 GitHub 创建仓库，建议命名 PonWrt-CI-XG-040G-MD-UBI，默认分支 main。
2. 将本文件包的内容放在仓库根目录，包含 .github 目录。
3. 提交后 push 到 main 会开始首次构建，也可以进入 Actions →
   Build PonWrt XG-040G-MD UBI → Run workflow 手动触发。
4. 默认 source_ref 为上表中的固定提交；修改源码版本时也需要核对 feeds 版本。
5. 构建完成后下载 PonWrt-XG-040G-MD-UBI Artifact；成功构建默认也发布 prerelease。
   手动运行时可以关闭 publish_release。该配置没有定时构建。

在本地创建并推送（先创建空仓库；以下用户名替换为实际用户）：

```sh
git init -b main
git add .
git commit -m 'Add PonWrt MD UBI CI and migrate existing package configuration'
git remote add origin https://github.com/Kahen/PonWrt-CI-XG-040G-MD-UBI.git
git push -u origin main
```

## 本地使用编译配置

CI 仓库与源码仓库并排放置。在 PonWrt 源码根目录运行：

```sh
cp ../PonWrt-CI-XG-040G-MD-UBI/config/feeds.conf feeds.conf.default
./scripts/feeds update -a
./scripts/feeds install -a
bash ../PonWrt-CI-XG-040G-MD-UBI/scripts/customize.sh
bash ../PonWrt-CI-XG-040G-MD-UBI/scripts/configure.sh
make menuconfig  # 可选：检查或调整选项
make download -j"$(nproc)"
make -j"$(nproc)" V=s
```

configure.sh 会合并三份配置并运行 make defconfig。若需要保存自己在 menuconfig
中的后续改动，可以运行 ./scripts/diffconfig.sh，评估输出后同步回 config/ 下的
配置片段；configure.sh 每次都会重建 .config。

正常构建依赖见工作流中的 Install build dependencies。完整固件编译在 Actions
执行，本文件包不包含可刷写固件。

## 编译产物与版本记录

- sysupgrade.itb：正常升级镜像。
- recovery.itb：RAM 恢复镜像，不作为普通升级包。
- *.manifest：实际固件的软件包清单。
- build.config：make defconfig 后实际生效的完整配置。
- sysupgrade-metadata.json、profiles.json：镜像与机型信息。
- source-commits.tsv：源码、feeds、第三方包提交版本。
- requested-packages-dropped.txt：可选软件包配置未生效记录（如有）。
- SHA256SUMS：两个 .itb 的 SHA256。

主源码和 feeds 默认固定提交；第三方包沿用原项目的分支更新方式。
source-commits.tsv 用于检查每次实际使用的版本；第三方包仍可能随上游变化。
customize.sh 只额外排除未选择的 squeezelite 音频包安装链接，避免该 snapshot
中无关的音频 codec 循环依赖阻碍 Kconfig 解析。

## 切换固件前的设备检查

目标 profile 同名只说明构建目标匹配，不能替代对设备当前布局的检查。
PonWrt 当前 DTS 使用 128 KiB BL2 区域，UBI 从 0x20000 开始，
并使用 bosa、ri、fip、fit、ubootenv、ubootenv2 等 UBI 卷。

旧讨论曾出现 bootloader 512 KiB + env 512 KiB + ubi 的分区表；如果设备目前
仍使用那份布局，不要仅凭 .itb 文件名进行升级。应以设备当前分区和引导链为准。
本项目不会修改 Bootloader 或替设备迁移分区。

切换前保存以下信息和设备自身的原始 bosa/ri 备份：

```sh
ubus call system board
cat /proc/mtd
ubinfo -a
```

确认当前板名、UBI 起始位置、引导链和校准卷匹配后，再对下载的 sysupgrade.itb
运行 sysupgrade -T 检查。检查失败时不要强制升级。
从旧构建切换时通常需要重新配置，预先导出自己的网络/PPPoE/VLAN 参数。
本包迁移的是编译配置，不含 PPPoE 密码、PON 认证凭据或设备校准数据。

PON 驱动和 LuCI 页面存在，不代表一定能通过你的运营商 OLT 注册。
使用设备自身的 bosa/ri，并在设备上核对 PON 注册、OMCI/OAM、VLAN 与 PPPoE 状态。
LuCI PON 配置位于 网络 → PON。保留的 attendedsysupgrade 插件不是该自定义
CI 的发布入口；后续升级从本仓库的构建产物获取。

## 来源

- 原 CI：Kahen/ImmortalWrt-CI-XG-040G-MD-UBI，迁移基准提交
  bce6b04f39fd2b2238c76c9bef6ba789f11ad10a。
- PON 目标与包选择：pbs05/ponwrt、pbs05/openwrt-pon-drivers、
  pbs05/openwrt-pon-userspace。
- 第三方包来源延续原仓库：vernesong/OpenClash、sirpdboy/luci-app-lucky、
  VIKINGYFY/packages、bingoguo93/luci-app-airoha-npu、VizzleTF/luci-theme-footstrap。
