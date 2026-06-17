---
name: wx-article-to-md
version: 2.1.0
description: 输入微信公众号文章链接，自动抓取、图片上传自有图床、转换为 Markdown 文件保存到本地
author: agent_created
triggers:
  - 微信文章转md
  - 公众号文章转markdown
  - 下载微信文章
  - 抓取公众号文章
  - wx to md
  - wechat article markdown
---

# 微信公众号文章转 Markdown（含图床上传）

将微信公众号文章链接解析为本地 Markdown 文件，图片自动上传到 Chevereto 图床。

## 前置条件

- Python 3.8+
- 依赖：`beautifulsoup4`, `markdownify`, `requests`

```bash
pip install beautifulsoup4 markdownify requests
```

## 配置

复制 `.env.example` 为 `.env`，填入自有 Chevereto 图床参数：

```bash
cp .env.example .env
```

```
CHEVERETO_URL=https://your-domain.com/api/1/upload
CHEVERETO_KEY=your-api-key
CHEVERETO_ALBUM_ID=your-album-id
```

不配置 `.env` 时，图片保留微信原始 CDN 链接，不影响正常使用。

---

## 快速开始

### 方式一：脚本直接运行

```bash
# URL 一键转换
python scripts/wx_convert.py https://mp.weixin.qq.com/s/xxxxx

# 指定输出目录
python scripts/wx_convert.py https://mp.weixin.qq.com/s/xxxxx -o ./output

# 从预下载的 HTML 转换（跳过抓取）
python scripts/wx_convert.py --html /tmp/wx_article.html
```

### 方式二：AI 自动化（WorkBuddy Skill 模式）

当 AI 加载此 Skill 时，按以下步骤执行：

#### 步骤 1：确认输入

用户提供公众号文章链接：
- `https://mp.weixin.qq.com/s/xxxxx`
- `https://mp.weixin.qq.com/s?__biz=xxx&mid=xxx&idx=xxx&sn=xxx`

默认输出：当前工作目录。

#### 步骤 2：抓取 HTML

```bash
curl -s -L \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml" \
  -H "Accept-Language: zh-CN,zh;q=0.9" \
  "<文章链接>" > /tmp/wx_article.html
```

验证文件大小：正常 > 50KB，过小说明被拦截。

路径说明：
- Git Bash: `/tmp/wx_article.html`
- Windows: `C:/Users/EDY/AppData/Local/Temp/wx_article.html`

#### 步骤 3：转换 & 上传

**优先使用项目内置脚本：**

```bash
python D:/xj/github/xj-skills/writing/wx-article-to-md/scripts/wx_convert.py \
  --html /tmp/wx_article.html \
  -o <输出目录>
```

**若项目脚本不可用，使用内联版本：**

将下方 Python 脚本写入临时文件，替换 `<输出目录>`，然后执行。

<details>
<summary>内联 Python 脚本（点击展开）</summary>

```python
import sys, os, re, json, time
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup
from markdownify import markdownify as md

OUTPUT_DIR = r'<输出目录>'
HTML_PATH = r'<HTML文件路径>'
ENV_PATH = r'C:\Users\EDY\.workbuddy\skills\wx-article-to-md\.env'

def load_env(path):
    config = {}
    if not os.path.exists(path):
        print(f"[INFO] .env 不存在，保留原图链接")
        return config
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                config[k.strip()] = v.strip()
    return config

env = load_env(ENV_PATH)

with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# 元数据
title = author = publish_time = link = ''
for script in soup.find_all('script'):
    text = script.string or ''
    if 'msg_title' in text:
        m = re.search(r"var msg_title = '(.*?)'", text)
        if m: title = m.group(1)
    if 'createTime' in text:
        m = re.search(r"var createTime = '([^']+)'", text)
        if m: publish_time = m.group(1)
    if 'msg_link' in text:
        m = re.search(r'var msg_link = "([^"]+)"', text)
        if m: link = m.group(1)

author_el = soup.find('a', id='js_name')
author = author_el.get_text(strip=True) if author_el else ''

content_div = soup.find('div', id='js_content')
if not content_div:
    print("ERROR: 未找到文章正文")
    sys.exit(1)

for img in content_div.find_all('img'):
    src = img.get('data-src') or img.get('src', '')
    if src: img['src'] = src

markdown_content = md(str(content_div), heading_style='ATX')
markdown_content = re.sub(r'!\[\]\(data:image/[^)]+\)', '', markdown_content)
markdown_content = re.sub(r'\n{4,}', '\n\n\n', markdown_content).strip()

# 图床上传
img_urls = list(set(re.findall(r'!\[.*?\]\((https?://[^\s)]+)\)', markdown_content)))
print(f"\n[INFO] 发现 {len(img_urls)} 张图片")

url_map = {}
if env.get('CHEVERETO_URL') and env.get('CHEVERETO_KEY'):
    import requests
    ok = fail = 0
    for i, img_url in enumerate(img_urls, 1):
        print(f"[{i}/{len(img_urls)}] 上传: {img_url[:80]}...")
        try:
            resp = requests.post(env['CHEVERETO_URL'], data={
                'source': img_url, 'key': env['CHEVERETO_KEY'],
                'album_id': env.get('CHEVERETO_ALBUM_ID', ''), 'format': 'json',
            }, timeout=60)
            result = resp.json()
            if result.get('status_code') == 200:
                url_map[img_url] = result['image']['url']
                ok += 1
                print(f"  -> OK: {result['image']['url']}")
            else:
                fail += 1
                print(f"  -> FAIL: {result.get('status_txt', '')}")
        except Exception as e:
            fail += 1
            print(f"  -> ERROR: {e}")
        if i < len(img_urls): time.sleep(0.5)
    print(f"\n[INFO] 上传统计: 成功 {ok}, 失败 {fail}")

if url_map:
    for old, new in url_map.items():
        markdown_content = markdown_content.replace(old, new)
    print(f"[INFO] 已替换 {len(url_map)} 个图片链接")

final_md = f"""# {title}

> 来源：{author}
> 发布时间：{publish_time}
> 链接：{link}

---

{markdown_content}
"""

safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
output_path = os.path.join(OUTPUT_DIR, f'{safe_title}.md')
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(final_md)

print(f'\n[DONE] 已保存: {output_path}')
print(f'       字符数: {len(final_md)}, 图片: {len(img_urls)}, 已上传: {len(url_map)}')
```

执行：
```bash
python <临时脚本路径>
```
</details>

#### 步骤 4：验证与交付

1. 读取生成的 `.md` 文件确认内容完整
2. 使用 `deliver_attachments` 交付
3. 汇报图片处理情况

---

## 输出格式示例

转换后的 Markdown 头部：

```markdown
# 代码知识图谱爆火：Understand Anything 与 CodeGraph 怎么选？

> 来源：Java后端技术
> 发布时间：2026-06-12 09:19
> 原始链接：https://mp.weixin.qq.com/s/kR5DGyDl47AILbPY-nJS8Q
> 转换时间：2026-06-12 14:45:00

---

正文内容...
```

图片链接替换示例：
- **原始**: `https://mmbiz.qpic.cn/mmbiz_png/xxxxx/640?wx_fmt=png`
- **替换后**: `https://your-domain.com/images/2026/06/12/photo.png`

---

## 配置说明

### 图床参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `CHEVERETO_URL` | 是 | Chevereto API 上传端点 |
| `CHEVERETO_KEY` | 是 | API 密钥 |
| `CHEVERETO_ALBUM_ID` | 否 | 上传到的相册 ID |

### 获取 API 密钥

1. 登录 Chevereto 管理面板
2. 进入 **设置 → API**
3. 创建新的 API Key
4. 将生成的 key 填入 `.env`

---

## 脚本参数参考

```
python scripts/wx_convert.py -h

positional arguments:
  url                  微信公众号文章 URL

optional arguments:
  -o, --output-dir     输出目录（默认当前目录）
  --html               预下载的 HTML 文件（跳过抓取）
  --env                .env 配置文件路径
  --no-upload          跳过图床上传
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| HTML < 50KB | 被微信拦截 | 浏览器手动打开后复制源代码 |
| js_content 不存在 | 文章删除/私密 | 确认文章可访问 |
| 图片上传全部失败 | API 配置问题 | 检查 `.env` 中 KEY/URL 是否正确 |
| `ModuleNotFoundError` | 缺少依赖 | `pip install beautifulsoup4 markdownify requests` |
| 文件名异常 | 标题含特殊字符 | 自动替换 `\/:*?"<>|` 为 `_` |

---

## 注意事项

- `.env` 含敏感信息，**已加入 .gitignore**，不要提交
- curl 路径：Git Bash 用 `/tmp/`，Windows 用 `%TEMP%`
- 微信图片真实地址在 `data-src` 属性，`src` 系占位图
- 图床上传"尝鲜"策略：成功替换，失败保留原链接
- 图片间 0.5s 间隔是正常的防限流措施
