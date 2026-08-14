# HBuilderX Core 占位目录

这里不包含、也不分发 HBuilderX 私有编译插件。

在合法安装 HBuilderX，并分别完成一次 Vue 2、Vue 3 真机运行以安装相关插件后，执行：

```bash
chmod +x ./prepare-core.sh
./prepare-core.sh /path/to/HBuilderX/plugins
docker build -t uni-builder-core:4.15.0-r1 .
```

请根据实际 HBuilderX 版本调整镜像标签，并自行确认许可和再分发限制。

