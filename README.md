# xj-skills

WorkBuddy Skills 开发项目，按领域分类管理所有自定义 skill。

## 分类结构

| 目录 | 说明 |
|------|------|
| `coding/` | 编程开发类：代码生成、重构、调试、代码审查等 |
| `writing/` | 写作类：文章、报告、文档、内容创作等 |
| `data-analysis/` | 数据分析类：数据处理、可视化、报表等 |
| `project-management/` | 项目管理类：任务规划、需求分析、复盘等 |

## Skills 列表

### writing/

| Skill | 说明 | 版本 |
|-------|------|------|
| [gzh-design-skill](writing/gzh-design-skill/) | 公众号排版引擎：Markdown 一键转为粘贴到公众号不掉格式的精美 HTML，内置 6 套主题 + 主题生成器 | v1.0 |
| [ai-article-detector](writing/ai-article-detector/) | AI 含量检测：5维度分析（结构/语言/信息密度/情感立场/格式细节） | v1.0 |
| [blog-text-polish](writing/blog-text-polish/) | 博客文字纠错·润色·去AI味：错别字检测、句式优化、AI痕迹改写 | v1.0 |
| [wx-article-to-md](writing/wx-article-to-md/) | 微信公众号文章转 Markdown，图片自动上传自有 Chevereto 图床 | v2.1 |

## Skill 开发规范

每个 skill 放在对应分类目录下，以独立子目录存放，包含 `SKILL.md` 入口文件。

```
writing/
  └── wx-article-to-md/
        ├── SKILL.md          # Skill 入口（AI 指令）
        ├── scripts/          # 可执行脚本
        │     └── wx_convert.py
        ├── .env.example      # 配置模板
        └── .gitignore
```
