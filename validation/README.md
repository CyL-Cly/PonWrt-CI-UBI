本目录是迁移验证记录。resolved.config 是实际 make defconfig 后的配置。全部保留选项及新增 PON 包通过检查；未执行完整固件编译或真机 PON 测试。make-defconfig.log 中的 bmx7 等告警来自未选择的上游 feed 包。完整编译依赖检查保留在 CI 中。
