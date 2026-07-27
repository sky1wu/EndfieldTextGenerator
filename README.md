# 简介
终末地白色大字生成器，顾名思义就是用来生成终末地的白色大字的

# 使用方法
下载发行版的exe文件，直接用就行，很简单
介绍视频：https://www.bilibili.com/video/BV1XhVD6wEVR/

# Web 版

在线使用：https://sky1wu.github.io/EndfieldTextGenerator/

Web 版使用原生 Canvas 实现，字体、五笔 98 码表、背景图片处理和 PNG 导出均在浏览器本地完成。

本地预览：

```bash
python -m http.server 8000 --directory web
```

推送到 `main` 分支后，GitHub Actions 会自动部署 `web` 目录到 GitHub Pages。

# 相关技术支持
萨卡兹字母字体：https://github.com/lhclbt/Endfield_Font
Pywubi库（原生的支持的是五笔86，但是终末地用的是五笔98，所以我更新了一下）
五笔98字库：http://98wb.ysepan.com/
