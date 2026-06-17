#!/usr/bin/env python3
"""
微信公众号文章 → Markdown 转换器（含图床上传）
============================================
用法:
  # 从 URL 一键下载转换（推荐）
  python wx_convert.py https://mp.weixin.qq.com/s/xxxxx

  # 从预下载的 HTML 文件转换
  python wx_convert.py --html /tmp/wx_article.html

  # 指定输出目录
  python wx_convert.py https://mp.weixin.qq.com/s/xxxxx -o ./output

  # 指定 .env 文件路径
  python wx_convert.py https://mp.weixin.qq.com/s/xxxxx --env ./my.env

依赖: beautifulsoup4, markdownify, requests
"""

import argparse
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
DEFAULT_OUTPUT_DIR = os.getcwd()
DEFAULT_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
TEMP_HTML_PATH = os.path.join(os.environ.get('TEMP', '/tmp'), 'wx_article.html')

# 浏览器 UA，避免被微信拦截
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def log(level: str, msg: str):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] [{level}] {msg}")


def safe_filename(name: str) -> str:
    """去除文件名中的非法字符"""
    return re.sub(r'[\\/:*?"<>|]', '_', name).strip()


def load_env(path: str) -> dict:
    """解析 .env 文件（key=value 格式，支持 # 注释）"""
    config = {}
    if not os.path.exists(path):
        log('WARN', f'.env 文件不存在: {path}')
        return config
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                config[key.strip()] = value.strip()
    log('INFO', f'已加载配置: {list(config.keys())}')
    return config


def fetch_html(url: str, output_path: str) -> bool:
    """用 curl 抓取文章 HTML，返回是否成功"""
    import subprocess
    log('INFO', f'正在抓取: {url}')
    cmd = [
        'curl', '-s', '-L',
        '-H', f'User-Agent: {UA}',
        '-H', 'Accept: text/html,application/xhtml+xml',
        '-H', 'Accept-Language: zh-CN,zh;q=0.9',
        '-o', output_path,
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log('ERROR', f'curl 失败: {result.stderr}')
        return False

    size = os.path.getsize(output_path)
    if size < 50 * 1024:
        log('ERROR', f'HTML 文件过小 ({size} 字节)，可能被微信拦截')
        return False

    log('INFO', f'HTML 下载完成: {size / 1024:.0f} KB')
    return True


# ---------------------------------------------------------------------------
# 解析 & 转换
# ---------------------------------------------------------------------------
def parse_article(html_path: str) -> dict:
    """解析微信文章 HTML，返回 {title, author, publish_time, link, markdown, img_urls}"""
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md

    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # --- 元数据 ---
    meta_patterns = {
        'title':        r"var msg_title = '(.*?)'",
        'publish_time': r"var createTime = '([^']+)'",
        'link':         r'var msg_link = "([^"]+)"',
    }
    meta = {}
    for script in soup.find_all('script'):
        text = script.string or ''
        for key, pattern in meta_patterns.items():
            if key not in meta:
                m = re.search(pattern, text)
                if m:
                    meta[key] = m.group(1)
        if len(meta) == len(meta_patterns):
            break

    # 公众号名
    author_el = soup.find('a', id='js_name')
    meta['author'] = author_el.get_text(strip=True) if author_el else '未知'

    # 补充缺失字段
    meta.setdefault('title', '未命名文章')
    meta.setdefault('publish_time', '')
    meta.setdefault('link', '')

    log('INFO', f'标题: {meta["title"]}')
    log('INFO', f'来源: {meta["author"]}  |  时间: {meta["publish_time"]}')

    # --- 正文 ---
    content_div = soup.find('div', id='js_content')
    if not content_div:
        raise RuntimeError('未找到文章正文（js_content 不存在），文章可能已删除或设为私密')

    # 修复图片：微信真实地址在 data-src
    for img in content_div.find_all('img'):
        real_src = img.get('data-src') or img.get('src', '')
        if real_src and not real_src.startswith('data:'):
            img['src'] = real_src

    # 转 Markdown
    markdown_content = md(str(content_div), heading_style='ATX')

    # 清理
    markdown_content = re.sub(r'!\[\]\(data:image/[^)]+\)', '', markdown_content)
    markdown_content = re.sub(r'\n{4,}', '\n\n\n', markdown_content)
    markdown_content = markdown_content.strip()

    # 提取图片 URL
    img_urls = list(set(
        re.findall(r'!\[.*?\]\((https?://[^\s)]+)\)', markdown_content)
    ))

    log('INFO', f'正文 {len(markdown_content)} 字符, 图片 {len(img_urls)} 张')
    return {**meta, 'markdown': markdown_content, 'img_urls': img_urls}


# ---------------------------------------------------------------------------
# 图床上传
# ---------------------------------------------------------------------------
def upload_images(img_urls: list, env: dict) -> dict:
    """上传图片到 Chevereto 图床，返回 {old_url: new_url}"""
    import requests

    api_url = env.get('CHEVERETO_URL', '')
    api_key = env.get('CHEVERETO_KEY', '')
    album_id = env.get('CHEVERETO_ALBUM_ID', '')

    if not api_url or not api_key:
        log('INFO', '未配置图床，保留微信原始图片链接')
        return {}

    log('INFO', f'开始上传 {len(img_urls)} 张图片到 {urlparse(api_url).hostname}')
    url_map = {}
    ok = fail = 0

    for i, img_url in enumerate(img_urls, 1):
        short = img_url[:100] + ('...' if len(img_url) > 100 else '')
        log('INFO', f'[{i}/{len(img_urls)}] {short}')

        try:
            resp = requests.post(
                api_url,
                data={
                    'source': img_url,
                    'key': api_key,
                    'album_id': album_id,
                    'format': 'json',
                },
                timeout=60,
            )
            result = resp.json()

            if result.get('status_code') == 200:
                new_url = result['image']['url']
                url_map[img_url] = new_url
                ok += 1
                log('OK', f'→ {new_url}')
            else:
                fail += 1
                log('FAIL', f'status={result.get("status_code")}: {result.get("status_txt", resp.text[:100])}')

        except requests.exceptions.Timeout:
            fail += 1
            log('FAIL', '请求超时')
        except Exception as e:
            fail += 1
            log('FAIL', str(e)[:120])

        if i < len(img_urls):
            time.sleep(0.5)

    log('INFO', f'上传完成: 成功 {ok}, 失败 {fail}, 合计 {len(img_urls)}')
    return url_map


# ---------------------------------------------------------------------------
# 组装 & 保存
# ---------------------------------------------------------------------------
def build_and_save(meta: dict, markdown: str, img_urls: list, url_map: dict, output_dir: str) -> str:
    """替换图片链接，组装最终 Markdown，保存文件"""
    # 替换图片 URL
    replaced = 0
    for old_url, new_url in url_map.items():
        if old_url in markdown:
            markdown = markdown.replace(old_url, new_url)
            replaced += 1

    if replaced:
        log('INFO', f'已替换 {replaced} 个图片链接')

    # 组装
    frontmatter = f"""# {meta['title']}

> 来源：{meta['author']}
> 发布时间：{meta['publish_time']}
> 原始链接：{meta['link']}
> 转换时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

"""
    final_md = frontmatter + markdown

    # 保存
    filename = safe_filename(meta['title']) + '.md'
    output_path = os.path.join(output_dir, filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_md)

    log('DONE', f'已保存: {output_path}')
    log('DONE', f'大小: {len(final_md):,} 字符  |  图片: {len(img_urls)} 张  |  已上传: {len(url_map)} 张')
    return output_path


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description='微信公众号文章转 Markdown（含图床上传）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python wx_convert.py https://mp.weixin.qq.com/s/xxxxx
  python wx_convert.py https://mp.weixin.qq.com/s/xxxxx -o ./output
  python wx_convert.py --html wx_article.html
  python wx_convert.py --html wx_article.html --env ~/.chevereto.env

配置:
  在 SKILL.md 同级目录创建 .env 文件:
    CHEVERETO_URL=http://your-domain.com/api/1/upload
    CHEVERETO_KEY=your-api-key
    CHEVERETO_ALBUM_ID=your-album-id
        """,
    )
    parser.add_argument('url', nargs='?', help='微信公众号文章 URL')
    parser.add_argument('-o', '--output-dir', default=DEFAULT_OUTPUT_DIR, help='输出目录（默认当前目录）')
    parser.add_argument('--html', help='预下载的 HTML 文件路径（跳过 curl 抓取）')
    parser.add_argument('--env', dest='env_file', default=DEFAULT_ENV_PATH, help='.env 配置文件路径')
    parser.add_argument('--no-upload', action='store_true', help='跳过图床上传，保留原始链接')
    args = parser.parse_args()

    if not args.url and not args.html:
        parser.error('需要提供文章 URL 或 --html 参数')

    # 确保输出目录存在
    os.makedirs(args.output_dir, exist_ok=True)

    # 加载 .env
    env = load_env(args.env_file) if not args.no_upload else {}

    # 获取 HTML
    if args.html:
        html_path = args.html
        if not os.path.exists(html_path):
            log('ERROR', f'HTML 文件不存在: {html_path}')
            sys.exit(1)
        log('INFO', f'使用已有 HTML: {html_path}')
    elif args.url:
        if not fetch_html(args.url, TEMP_HTML_PATH):
            sys.exit(1)
        html_path = TEMP_HTML_PATH

    # 解析文章
    try:
        result = parse_article(html_path)
    except Exception as e:
        log('ERROR', str(e))
        sys.exit(1)

    # 上传图片
    url_map = {}
    if result['img_urls'] and env:
        url_map = upload_images(result['img_urls'], env)

    # 组装保存
    output_path = build_and_save(
        result, result['markdown'], result['img_urls'], url_map, args.output_dir,
    )

    # 输出结果路径供调用方解析
    print(f'\nOUTPUT_FILE={output_path}')

    # 清理临时文件（非 --html 模式）
    if not args.html and os.path.exists(TEMP_HTML_PATH):
        os.remove(TEMP_HTML_PATH)


if __name__ == '__main__':
    main()
