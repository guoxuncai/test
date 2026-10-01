# 半导体 · 财经 学习笔记

个人静态知识库：**半导体**知识脉络 + **财经金融每日简报**。
纯静态 HTML + GitHub Pages 自动部署，**每天写完页面丢进目录，双击一个脚本即可上线**。

在线地址：https://guoxuncai.github.io/test/

---

## 一、每天怎么发文章（记住这 3 步）

1. 写好页面文件，放进对应分类目录：

   | 要发的内容 | 放这里 |
   | --- | --- |
   | 财经金融每日简报 | `posts/finance/` |
   | 半导体知识与资讯 | `posts/semiconductor/` |

2. 文件名按 `年-月-日-标题关键词.html` 命名，例如：
   ```
   posts/finance/2026-10-01-节后首日市场观察.html
   ```
   日期必须从文件名开头，脚本靠它排序和归档。

3. 双击项目根目录的 **`publish.bat`**
   → 自动扫描新文章 → 更新主页索引 → 提交并推送到 GitHub → Pages 约 1–2 分钟上线。

> 不需要碰 `index.html`，也不需要手写任何链接。删文章同理：删掉文件后跑一次脚本，主页链接自动消失。

### 其他两个入口

| 文件 | 作用 |
| --- | --- |
| `new-post.bat` | 从标准模板生成一篇草稿（自动套好标题、日期、元数据） |
| `preview.bat` | 更新索引并起本地服务，浏览器打开 http://127.0.0.1:8000 预览再发布 |

---

## 二、目录结构

```
.
├── index.html              博客主页（列表由 JS 动态渲染，不用手改）
├── assets/
│   ├── css/site.css        主页样式（明/暗双主题）
│   ├── css/article.css     文章页通用排版样式
│   └── js/site.js          主页逻辑：分类筛选、搜索、归档、标签
├── data/
│   ├── posts.js            ★ 文章索引（脚本自动生成，勿手改）
│   └── posts.json          同上，JSON 版本便于查看
├── posts/
│   ├── semiconductor/      半导体知识与资讯
│   └── finance/            财经金融每日简报
├── tools/
│   ├── publish.py          自动发布脚本（扫描+生成索引+提交推送）
│   └── template.html       新文章模板（含标准排版组件）
├── feed.xml                RSS 订阅源（自动生成）
├── sitemap.xml             站点地图（自动生成）
├── publish.bat             ① 日常发布入口（扫描+索引+推送）
├── preview.bat             ② 本地预览服务
└── new-post.bat            ③ 新建草稿
```

**想加新分类？** 直接在 `posts/` 下新建目录（如 `posts/macro/`），把 html 放进去即可，
主页会自动出现该分类页签 —— 无需改任何代码。要改显示名，编辑 `tools/publish.py` 顶部的 `CATEGORY_LABELS`。

---

## 三、文章页要写的三个元数据

复制 `tools/template.html` 或双击「new-post.bat」，改这三个地方即可：

```html
<title>文章标题</title>
<meta name="description" content="60-80 字摘要，会显示在主页卡片上">
<meta name="keywords" content="标签1, 标签2, 标签3">
<meta name="date" content="2026-10-01">
```

不写也能扫描到：脚本会退回用 `<title>`、`<h1>`、正文首段作为标题摘要。但写了效果最整齐。

### 排版注意事项

- 文章统一放在 `posts/<分类>/` 二级目录，引用样式的路径是固定写法：
  ```html
  <link rel="stylesheet" href="../../assets/css/article.css">
  <a href="../../index.html">← 返回主页</a>
  ```
- A 股习惯配色已内置：涨用 `<span class="up">`（红），跌用 `<span class="down">`（绿）。
- 其他现成组件：`<div class="box">` 要点框、`<blockquote>` 引用、`表格`、`.tagbar` 标签区，直接看 `tools/template.html`。

---

## 四、脚本进阶用法

```bash
python tools/publish.py              # 扫描 + 生成索引 + 提交推送（等价双击 bat）
python tools/publish.py --no-push    # 只更新索引在本地看，不推送
python tools/publish.py --serve      # 更新索引并启动本地预览服务
python tools/publish.py --draft finance 2026-10-02-早报   # 生成草稿文件
python tools/publish.py -m "自定义提交信息"

python tools/check-series.py          # 校验「系列导航」：篇号、当前项、互链文件是否存在
```

> 系列文章（如半导体学习路径）在每篇底部有 `.series` 导航块。**新增或调整顺序后，
> 建议先跑一次 `tools/check-series.py`**，确认各篇导航项数一致、当前项正确、互链无死链。

---

## 五、部署说明（已配置好，一般不用动）

- `.github/workflows/deploy-pages.yml`：推送到 `main` 分支后自动构建并发布到 GitHub Pages。
- **首次使用请确认**：仓库 `Settings → Pages → Build and deployment → Source` 选 **GitHub Actions**。
- 站点根路径为 `/test/`，脚本中的 `sitemap.xml` / `feed.xml` 链接会按该前缀自动生成。
- 旧文件 `deploy.bat` 已废弃，统一用 `publish.bat`。
- 三个 bat 使用英文文件名是刻意为之：cmd 在 `chcp 65001` 下无法正确解析含中文名的批处理文件，会出现莫名报错。

---

## 六、常见问题

| 现象 | 处理 |
| --- | --- |
| 双击 bat 提示「未检测到 Python」 | 安装 Python 并勾选 Add to PATH；安装后重开一个窗口再双击 |
| 主页列表是空的 | 确认 html 确实在 `posts/` 的某个子目录里，然后跑一次 `publish.bat` |
| 推送失败（权限/认证） | 确认 SSH key 已加到 GitHub，或用 GitHub Desktop / 手动 `git push` |
| 列表一片空白 | ① 确认 html 在 `posts/` 的某个子目录里；② 跑一次 `publish.bat` 生成索引；③ 若直接双击 html 打开无内容，改用「preview.bat」通过 http 访问 |
| 想改站点名/简介 | 编辑 `index.html` 里的品牌区与 hero 文案，保存后重新发布 |
