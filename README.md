# 拾错｜考研错题复习

按科目记录考研错题、安排复习，并按知识点整理薄弱项。网页部署在 GitHub Pages，AI 接口由独立 Python 服务安全调用 Agnes。

## 使用 AI

浏览器只保存后端地址和访问码；Agnes API 密钥只配置在后端环境变量中，不会进入网页或 GitHub 仓库。

### 部署后端到 Render

1. 先在 Agnes 控制台撤销聊天中暴露过的旧密钥，并创建新密钥。
2. 登录 [Render](https://render.com/)，选择 **New + → Blueprint**，连接 `hybob0205/kaoyan-mistake-app` 仓库并部署。仓库中的 `render.yaml` 会创建 Python API 服务。
3. 在 Render 服务环境变量中填入 `AGNES_API_KEY`（新密钥）和 `APP_ACCESS_TOKEN`（自己生成的长随机访问码）。`AGNES_API_BASE_URL` 与 `AGNES_MODEL` 已预设。保存后等待服务部署完成。
4. 复制 Render 提供的 `https://…onrender.com` 服务地址。
5. 打开 [拾错](https://hybob0205.github.io/kaoyan-mistake-app/)，进入“AI 服务状态”，填写 Render 地址和同一个 `APP_ACCESS_TOKEN`，点击“保存并连接”。看到“已连接”后即可在新增或错题详情中使用 AI 分析。
6. 把网页地址和访问码交给学习者，在她的设备上也填入服务地址与访问码。访问码只需分享给使用者，不要放入代码仓库。

生成长随机访问码（在终端运行）：

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

Render 免费实例可能在一段时间无访问后休眠，首次 AI 请求需要等待服务唤醒。错题数据仍保存在各自浏览器中；这不会自动同步到协助者设备。

## 本机版

需要 Python 3：

```bash
python3 launch.py
```

访问 `http://127.0.0.1:8788/`。本机版读取 `.env`；凭据不会发送到浏览器或加入 Git。可参考 `.env.example`。

## GitHub Pages

`main` 分支包含 Pages Actions 工作流。每次推送会从 `index.html`、`app.css`、`app.js` 生成 `site/` 静态站点并部署。Pages 负责网页；独立后端服务提供 AI API。后端只接受已配置的访问码，并限制浏览器跨域来源为本 Pages 站点。

## 数据

错题保存在当前浏览器的 `localStorage`。本机地址和 GitHub Pages 地址、以及不同设备之间的数据不会自动互通；请从错题总库导出 JSON 备份，再在另一地址导入。清除浏览器数据前也请先备份。
