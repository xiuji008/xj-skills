#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upload_images.py — 将 Markdown 文档中引用的本地图片批量上传到图床，
并把文档里的本地路径替换为图床返回的远程链接。

图床接口:
    POST http://youserver/upload
    multipart/form-data, 字段名 files (可重复传多个文件)
    响应: {"success": true, "result": ["https://.../xxx.png", ...]}
"""

import sys
import os
import re
import json
import argparse

sys.stdout.reconfigure(encoding='utf-8')

try:
    import requests
except ImportError:
    print("[ERROR] 缺少依赖 requests，请先运行: pip install requests")
    sys.exit(1)

DEFAULT_UPLOAD_URL = "http://youserver/upload"

# 匹配 Markdown 图片语法:  ![alt](path "optional title")
IMG_RE = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)')

REMOTE_PREFIXES = ('http://', 'https://', '//', 'data:')

# 默认 .env 位置：脚本所在目录的上一级（skill 根目录），与 .env.example 同处
DEFAULT_ENV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
ENV_KEY = 'IMAGE_BED_URL'


def load_env(path):
    """读取 .env 中的键值对，返回 dict。文件不存在返回空 dict。"""
    config = {}
    if not os.path.exists(path):
        return config
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            config[k.strip()] = v.strip()
    return config


def guess_mime(path):
    ext = os.path.splitext(path)[1].lower()
    return {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp',
        '.svg': 'image/svg+xml',
    }.get(ext, 'application/octet-stream')


def collect_local_images(doc_path, content):
    """收集文档中所有本地图片的绝对路径（去重、跳过远程/不存在）。"""
    doc_dir = os.path.dirname(os.path.abspath(doc_path))
    ordered = []
    seen = set()
    for m in IMG_RE.finditer(content):
        ref = m.group(2).strip()
        if ref.startswith(REMOTE_PREFIXES):
            continue
        abs_path = os.path.normpath(os.path.join(doc_dir, ref))
        if not os.path.isfile(abs_path):
            print(f"[WARN] 图片不存在，跳过: {ref}  ->  {abs_path}")
            continue
        if abs_path not in seen:
            seen.add(abs_path)
            ordered.append(abs_path)
    return ordered


def upload_images(images, url):
    """一次性上传所有图片，返回与 images 顺序对应的 URL 列表。"""
    opened = []
    files = []
    try:
        for p in images:
            f = open(p, 'rb')
            opened.append(f)
            files.append(('files', (os.path.basename(p), f, guess_mime(p))))
        print(f"[INFO] 正在上传 {len(files)} 张图片到 {url} ...")
        resp = requests.post(url, files=files, timeout=180)
    finally:
        for f in opened:
            f.close()

    try:
        data = resp.json()
    except ValueError:
        print(f"[ERROR] 响应不是合法 JSON，HTTP {resp.status_code}: {resp.text[:300]}")
        return None

    if not data.get('success'):
        print(f"[ERROR] 图床返回失败: {json.dumps(data, ensure_ascii=False)}")
        return None

    return data.get('result', [])


def replace_refs(content, doc_path, url_map):
    doc_dir = os.path.dirname(os.path.abspath(doc_path))

    def repl(m):
        alt = m.group(1)
        ref = m.group(2).strip()
        title = m.group(3)
        if ref.startswith(REMOTE_PREFIXES):
            return m.group(0)
        abs_path = os.path.normpath(os.path.join(doc_dir, ref))
        if abs_path in url_map:
            new_url = url_map[abs_path]
            if title:
                return f'![{alt}]({new_url} "{title}")'
            return f'![{alt}]({new_url})'
        return m.group(0)

    return IMG_RE.sub(repl, content)


def main():
    parser = argparse.ArgumentParser(
        description='将 Markdown 文档中的本地图片上传到图床并替换链接')
    parser.add_argument('doc', help='Markdown 文档路径')
    parser.add_argument('-u', '--url', default=None,
                        help='图床上传地址（优先级最高，覆盖 .env 与默认值）')
    parser.add_argument('--env', default=DEFAULT_ENV_PATH,
                        help='.env 配置文件路径（默认脚本同目录的 .env）')
    parser.add_argument('-o', '--output', default=None,
                        help='输出路径（默认原地覆盖 doc）')
    parser.add_argument('--backup', action='store_true',
                        help='处理前先生成 doc.bak 备份')
    parser.add_argument('--dry-run', action='store_true',
                        help='仅列出待上传图片，不实际上传、不修改文档')
    args = parser.parse_args()

    # URL 优先级: -u 命令行 > .env 的 IMAGE_BED_URL > 内置默认值
    env = load_env(args.env)
    upload_url = args.url or env.get(ENV_KEY) or DEFAULT_UPLOAD_URL
    if args.url:
        print(f"[INFO] 使用命令行指定地址: {upload_url}")
    elif env.get(ENV_KEY):
        print(f"[INFO] 已从 .env 读取上传地址: {upload_url}")
    else:
        print(f"[INFO] 未配置 .env，使用默认上传地址: {upload_url}")

    if not os.path.isfile(args.doc):
        print(f"[ERROR] 文档不存在: {args.doc}")
        sys.exit(1)

    with open(args.doc, 'r', encoding='utf-8') as f:
        content = f.read()

    images = collect_local_images(args.doc, content)
    print(f"[INFO] 文档中可上传的本地图片: {len(images)} 张")
    for p in images:
        print(f"  - {p}")

    if args.dry_run:
        return

    if not images:
        print("[INFO] 无可上传的本地图片，结束")
        return

    if '*' in upload_url:
        print("[ERROR] 未提供真实上传地址（.env 为脱敏占位符，且未用 -u 或系统环境变量 IMAGE_BED_URL 提供真实地址），中止")
        sys.exit(1)

    urls = upload_images(images, upload_url)
    if urls is None:
        sys.exit(1)
    if len(urls) != len(images):
        print(f"[WARN] 返回链接数 {len(urls)} 与图片数 {len(images)} 不一致，按索引匹配")

    url_map = {}
    for i, abs_path in enumerate(images):
        if i < len(urls) and urls[i]:
            url_map[abs_path] = urls[i]

    new_content = replace_refs(content, args.doc, url_map)

    out_path = args.output or args.doc
    if out_path == args.doc and args.backup:
        backup_path = args.doc + '.bak'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[INFO] 已备份原文档: {backup_path}")

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"[DONE] 成功替换 {len(url_map)} / {len(images)} 个图片链接")
    print(f"       输出: {out_path}")


if __name__ == '__main__':
    main()
