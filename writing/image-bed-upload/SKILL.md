---
name: image-bed-upload
version: 1.0.0
description: 将 Markdown 文档中引用的本地图片批量上传到自有图床（Chevereto），并把文档中的本地路径替换为图床返回的远程链接
author: agent_created
triggers:
  - 上传文档图片
  - 上传文档里的图片
  - 把文档中的图片上传
  - 把那个文档中的图片上传到图床
  - 图片上传到图床
  - 把本地图片换成图床链接
  - 替换文档图片链接
  - 图床上传
  - upload local images to image bed
  - replace local images with cdn urls
---

# 文档图片图床上传

将 Markdown 文档中引用的**本地图片**批量上传到图床，并把文档里的本地路径替换为图床返回的远程链接。

适用于：用户想把一篇已写好的 Markdown 文档（里面嵌了本地图片，如 `![](./images/foo.png)`）发布到需要外链图床的场景。

## 触发条件

当用户表达以下意图时调用本 skill：

- 「把**那个文档**里的图片上传到图床」
- 「把文档中的本地图片换成图床链接 / CDN 链接」
- 「上传文档图片」「图床上传」等

用户提供目标文档路径（`.md`）。若用户未明确指出文档，先确认是哪一份文档。

## 图床接口

| 项 | 值 |
|----|----|
| 上传地址 | `http://youserver/upload`（从 `.env` 读取，见下方配置） |
| 请求方式 | `POST` `multipart/form-data` |
| 文件字段 | `files`（可同时传多个文件，字段名重复） |
| 响应 | `{"success": true, "result": ["https://.../xxx.png", ...]}` |

- `result` 数组顺序与上传的 `files` 顺序一致，按索引一一对应。
- `success` 为 `false` 时表示整体失败，需检查网络 / 服务可达性。

## 配置

上传地址写在 skill 目录下的 `.env` 中，脚本运行时会自动读取。**复制模板即可使用：**

```bash
cp writing/image-bed-upload/.env.example writing/image-bed-upload/.env
```

`.env` / `.env.example` 内容（已含真实上传地址）：

```
IMAGE_BED_URL=http://youserver/upload
```

地址解析优先级：命令行 `-u` > `.env` 的 `IMAGE_BED_URL` > 脚本内置默认值。
`.env` 已加入 `.gitignore`，不会被提交。

## 执行步骤（AI 自动化模式）

### 步骤 1：确认目标文档

拿到用户要处理的 Markdown 文档路径，例如：

```
d:/git/github/xj-skills/writing/some-article/文章.md
```

### 步骤 2：运行上传脚本

优先使用项目内置脚本，它会自动：

1. 扫描文档中所有 `![alt](path)` 图片引用
2. 过滤掉远程链接（`http(s)://`、`//`、`data:`）和不存在的文件
3. 把所有本地图片一次性 POST 到图床（多文件）
4. 按返回顺序把文档中的本地路径替换为远程 URL
5. 默认**原地覆盖**文档（加 `--backup` 可先备份；`-o` 可指定输出路径）

```bash
# 原地替换（推荐先 git 提交或用 --backup 备份）
python D:/git/github/xj-skills/writing/image-bed-upload/scripts/upload_images.py ^
  "d:/git/github/xj-skills/writing/some-article/文章.md" --backup

# 仅预览将要上传哪些图片，不实际上传
python D:/git/github/xj-skills/writing/image-bed-upload/scripts/upload_images.py ^
  "d:/git/github/xj-skills/writing/some-article/文章.md" --dry-run

# 输出到新文件，保留原文档
python D:/git/github/xj-skills/writing/image-bed-upload/scripts/upload_images.py ^
  "d:/git/github/xj-skills/writing/some-article/文章.md" -o "d:/git/github/xj-skills/.out/文章_图床版.md"
```

### 步骤 3：校验与交付

1. 读取处理后的文档，确认本地图片路径已全部替换为 `http(s)://chevereto...` 开头的图床链接。
2. 汇报统计：共发现 N 张本地图片、成功上传替换 M 张、跳过 K 张（不存在/已为远程链接）。
3. 若使用了 `--backup`，提醒用户已生成 `.bak` 备份文件。

---

## 脚本参数

```
python scripts/upload_images.py -h

positional arguments:
  doc                   要处理的 Markdown 文档路径

options:
  -u, --url URL         图床上传地址（默认 http://youserver/upload）
  -o, --output PATH     输出路径（默认原地覆盖 doc）
  --backup              处理前先生成 doc.bak 备份
  --dry-run             仅列出待上传图片，不实际上传/不修改文档
```

## 注意事项

- Windows 路径含反斜杠，传入脚本时建议用双引号包裹。
- 图床地址为内网 / natapp 隧道路由，**需用户本地或目标环境能访问该地址**。
- 同一张图片在文档中被引用多次，只会上传一次，但所有引用都会被替换。
- 失败的图片不会被替换，原本地路径保留，便于后续排查。
- 脚本依赖 `requests`：`pip install requests`。
