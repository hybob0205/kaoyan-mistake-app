# 拾错｜考研错题复习

按科目记录考研错题、安排复习，并按知识点整理薄弱项。

## 本机版

需要 Python 3：

```bash
python3 launch.py
```

访问 `http://127.0.0.1:8788/`。本机版可使用 `.env` 中的 Agnes AI 配置；凭据不会发送到浏览器或加入 Git。

## GitHub Pages

`main` 分支包含 Pages Actions 工作流。每次推送会从 `index.html`、`app.css`、`app.js` 生成 `site/` 静态站点并部署。GitHub Pages 只能运行静态前端，因此云端版本保留拍照、粘贴、错题详情、手动分类、筛选、复习和浏览器本地存储；AI 整理需使用本机版或另行部署安全的后端。API 密钥绝不放入 Pages 静态文件。

## 数据

错题保存在当前浏览器的 `localStorage`。本机地址和 GitHub Pages 地址是不同站点，数据不会自动互通；请从错题总库导出 JSON 备份，再在另一地址导入。清除浏览器数据前也请先备份。
