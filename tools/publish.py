#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
==========================================================
 静态博客 · 自动发布脚本
==========================================================
作用：
  1. 扫描 posts/ 目录下所有 HTML 文章，自动提取 标题 / 日期 / 摘要 / 标签 / 分类
  2. 生成 data/posts.js（主页数据源）、feed.xml（RSS）、sitemap.xml
  3. 自动 git add / commit / push 到 GitHub，触发 Pages 自动部署

常用命令：
  python tools/publish.py              # 扫描 + 更新索引 + 提交推送
  python tools/publish.py --no-push    # 只更新索引，不推送（先本地看看）
  python tools/publish.py --serve      # 更新索引并启动本地预览服务
  python tools/publish.py --draft finance 2026-10-01-标题关键词
                                       # 从模板新建一篇草稿文件
==========================================================
"""
import os
import re
import io
import sys
import json
import html
import shutil
import argparse
import datetime
import subprocess

# ----------------------------- 配置 -----------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "posts")
DATA_DIR = os.path.join(ROOT, "data")
TOOLS_DIR = os.path.join(ROOT, "tools")

# 分类显示名（未列出的目录会直接用目录名作为显示名）
CATEGORY_LABELS = {
    "semiconductor": "半导体",
    "finance": "财经简报",
    "macro": "宏观经济",
    "notes": "随笔笔记",
}

DEFAULT_SITE_URL = "https://guoxuncai.github.io/test/"
RE_DATE = re.compile(r"(20\d{2})[-_.]?[^\d]?(\d{1,2})[-_.]?[^\d]?(\d{1,2})")
# 中文日期：2026年9月25日 / 2026年10月1日
RE_CN_DATE = re.compile(r"(20\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日")

# 摘要清洗：去掉版面装饰性文字（品牌英文名被空格拆开、栏目标题、署名行等）
_NOISE_PATTERNS = [
    r"J\s*I\s*N\s*N\s*I\s*A\s*N",
    r"JINNIAN\s*FINANCE",
    r"JINNIAN\s*FINANCIAL\s*MORNING\s*BRIEF",
    r"JINNIAN\s*FINANCE\s*DAILY",
    r"FINANCIAL\s*DAILY\s*BRIEF",
    r"瑾年财经早报",
    r"瑾年财经工作室",
    r"每日财经早报",
    r"财经早报",
    r"财经周报",
    r"财经周日刊",
    r"瑾年财经",
    r"瑾年出品",
    r"出品人?[：:]\s*\S+",
    r"作者[：:]\s*\S+",
    r"主理人[：:]\s*\S+",
    r"视频号[：:]\s*\S+",
    r"数据来源[：:]\s*\S+",
    r"出品[：:]\s*\S+",
    r"数据驱动\s*·\s*专业解读\s*·\s*银行人自己的早报",
    r"一手数据\s*·\s*深度解读\s*·\s*银行人专属",
    r"每日精选\s*·\s*银行人自己的财经早餐",
    r"银行人自己\w*",
    r"每日金融市场全景[速纵]览",
    r"金融资讯\s*·\s*市场数据\s*·\s*深度解读",
    r"股市\s*·\s*债市\s*·\s*期货\s*·\s*资金市场\s*·\s*银行\s*·\s*理财",
    r"—\s*每日金融市场全景[速纵]览\s*—",
    r"·\s*总第\s*\d+\s*期",
    r"总第\s*\d+\s*期",
]


# ----------------------------- 工具 -----------------------------
def read_text(path):
    """兼容 utf-8 / gbk / utf-8-sig，读不了就返回空串"""
    for enc in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            with io.open(path, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    return ""


def strip_tags(s):
    s = re.sub(r"(?is)<(script|style|svg|canvas)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?s)<!--.*?-->", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def meta_content(src, *names):
    """读取 <meta name="xx" content="yy"> 或 property="yy" """
    for n in names:
        m = re.search(
            r'<meta[^>]+(?:name|property)\s*=\s*["\']' + re.escape(n) + r'["\'][^>]*content\s*=\s*["\']([^"\']*)["\']',
            src, re.I)
        if not m:
            m = re.search(
                r'<meta[^>]+content\s*=\s*["\']([^"\']*)["\'][^>]*(?:name|property)\s*=\s*["\']' + re.escape(n) + r'["\']',
                src, re.I)
        if m:
            return html.unescape(m.group(1)).strip()
    return ""


def clean_summary(s):
    """去掉摘要开头的版面装饰文字、署名行、重复标题等噪声"""
    if not s:
        return s
    s = s.strip()

    # 1) 只合并"逐字拆开"的短标题（连续单字间空格，如 财 经 早 报），不碰正常词间空格
    s = re.sub(r"(?:(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])){2,}", "", s)
    # 拆开的英文品牌名：J I N N I A N -> JINNIAN
    s = re.sub(r"(?:(?<=[A-Z])\s+(?=[A-Z]))+", "", s)

    # 2) 逐条清除版面装饰词
    for pat in _NOISE_PATTERNS:
        s = re.sub(pat, " ", s, flags=re.I)

    # 3) 清除符号、表情、分隔符
    s = re.sub(r"[📊📈📉📅📌🔹🔸💰🛢🏦💼🌍📚🎙✨✦📋⬆⬇🔺🔻▼▲]+", " ", s)
    s = re.sub(r"[|｜·•✦]{1,}\s*", " ", s)
    s = re.sub(r"[ \t]{2,}", " ", s)

    # 4) 只裁掉开头的"纯时间/纯标签"片段，且要求后面还有实质内容
    #    逐次剥离，避免把正文第一个字一起吃进去
    head_pats = [
        r"^\s*20\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*[（(]?\s*周?[一二三四五六日天]?\s*[)）]?\s*",
        r"^\s*\d{4}[-/.]\d{1,2}[-/.]\d{1,2}\s*",
        r"^\s*[（(]?\s*周[一二三四五六日天]\s*[)）]?\s*",
        r"^\s*(星期|礼拜)[一二三四五六日天]\s*",
        r"^\s*农历[^\s，,。；;]{0,8}\s*",
        r"^\s*(上|上一)交易日[：:]\s*[^\s，,。；;]{0,14}\s*",
        r"^\s*数据[截止来源][：:]\s*[^\s，,。；;]{0,16}\s*",
        r"^\s*20\d{2}\s*年\s*第?\s*\d*\s*[季度周]\s*",
        r"^\s*[每]?[周日期]*晚[间上]?推送\s*",
        r"^\s*[一二三四五六七八九十]+[、.．]\s*",
        r"^\s*(概览|市场概览|今日市场概览|今日要点|今日核心摘要|今日速览|本期导读|结论摘要|大盘综述|股市概览|股市早参|股市纵览|全球市场概览|A股市场概况|A股市场|市场纵览)\s*[:：、]?\s*",
        r"^\s*(OVERVIEW|MARKET\s*OVERVIEW)\s*[:：]?\s*",
        r"^\s*[-—–]{1,}\s*",          # 残留的分隔线
        r"^\s*[、，,。：:；;]\s*",
    ]
    for _ in range(6):
        before = s
        for pat in head_pats:
            s = re.sub(pat, "", s, count=1, flags=re.I)
        if s == before:
            break

    s = re.sub(r"[ \t]{2,}", " ", s).strip(" 。，,、|·-—– 　:：")
    return s


def is_poor_summary(s, title=""):
    """判断摘要质量是否合格：太短、含装饰残留、或与标题/时间标签重复"""
    if not s or len(s) < 24:
        return True
    flat = re.sub(r"\s", "", s)
    # 英文品牌名残留（含被空格拆开后合并的形态）
    if re.search(r"(?i)(JINNIAN|FINANCE|FINANCIAL|MORNINGBRIEF|DAILYBRIEF|OVERVIEW)", flat):
        return True
    # 栏目标题 / 版面标签残留
    if re.search(r"(财经早报|财经周报|财经周日刊|今日核心摘要|今日市场概览|今日速览|今日要点|本期导读|市场概览|大盘综述|股市概览|股市早参|股市纵览|全球市场概览|A股复盘|资金市场|债券市场|期货行情|银行监管|理财市场|经济要闻|每日一学)", flat):
        return True
    # 与标题核心词高度重合
    core = re.sub(r"[\s|｜·—–\-_]+", "", title)[:12]
    if core and len(core) >= 6 and core in flat[:40]:
        return True
    # 开头仍是时间/编号/分隔符
    if re.match(r"^[\s（(]*(\d{4}\s*年|星期|周[一二三四五六日]|礼拜|农历|[一二三四五六七八九十]+、|[-—–]|[、，,。：:；;])", s):
        return True
    # 以片段符号开头
    if re.match(r"^\s*[️🛢📰🏭⚖️]+", s):
        return True
    return False


def file_date(fname, src, path):
    """优先文件名日期 -> 标题/正文中的中文日期 -> meta -> 文件修改时间"""
    for text in (fname, meta_content(src, "date", "article:published_time", "publishdate")):
        if not text:
            continue
        m = RE_CN_DATE.search(text) or RE_DATE.search(text)
        if m:
            return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))
    # 从 <title> 与正文开头（前 3000 字）里找中文日期
    head = src[:3000]
    m = RE_CN_DATE.search(head)
    if m:
        return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))
    return datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()


def tidy_title(src, fname):
    t = ""
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", src)
    if m:
        t = strip_tags(m.group(1))
        # 去掉常见站点后缀
        t = re.split(r"\s*[|｜\-–—]\s*(半导体\s*·\s*财经|学习笔记).*$", t)[0].strip()
    if not t:
        for tag in ("h1", "h2"):
            m = re.search(r"(?is)<" + tag + r"[^>]*>(.*?)</" + tag + ">", src)
            if m:
                t = strip_tags(m.group(1))
                break
    if not t:
        t = re.sub(r"^\d{4}[-_.]?\d{2}[-_.]?\d{2}[-_\s]*", "", fname)
        t = os.path.splitext(t)[0].replace("-", " ").replace("_", " ").strip()
    return t[:80]


def build_summary(src, maxlen=120, title=""):
    d = meta_content(src, "description", "og:description")
    if d:
        c = clean_summary(d)
        if not is_poor_summary(c, title):
            return c[:maxlen]
    # 没有 description，或清洗后质量不合格 -> 从正文挑一段干净的句子
    m = re.search(r"(?is)<body[^>]*>(.*)</body>", src)
    body = strip_tags(m.group(1) if m else src)
    body = clean_summary(body)
    # 按句切分，取第一句"看起来像摘要"的话（含数字或较长）
    parts = [x.strip() for x in re.split(r"(?<=[。！？!?])", body) if x.strip()]
    for i, raw in enumerate(parts[:8]):
        seg = raw.strip(" 。，,、|·-—–:：")
        if len(seg) < 18 or is_poor_summary(seg, title):
            continue
        tail = ""
        if i + 1 < len(parts):
            tail = parts[i + 1].strip()
        text = seg
        if not text.endswith(("。", "！", "？", "!", "?")):
            text += "。"
        text = (text + tail).strip()
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text[:maxlen] + ("…" if len(text) > maxlen else "")
    return body[:maxlen] + ("…" if len(body) > maxlen else "")


def build_tags(src):
    raw = meta_content(src, "keywords", "tags")
    if not raw:
        return []
    parts = re.split(r"[,，、;；\s]+", raw)
    seen, out = set(), []
    for p in parts:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out[:6]


def run_git(args, check=True):
    r = subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError("git %s 失败：%s" % (" ".join(args), (r.stderr or r.stdout).strip()))
    return r.stdout.strip()


def site_url():
    try:
        remote = run_git(["remote", "get-url", "origin"], check=False)
        m = re.search(r"(?:git@|https?://)github\.com[:/]([^/]+)/([^/\s]+?)(?:\.git)?/?$", remote or "")
        if m:
            return "https://%s.github.io/%s/" % (m.group(1), m.group(2))
    except Exception:
        pass
    return DEFAULT_SITE_URL


# ----------------------------- 扫描 -----------------------------
def scan():
    posts = []
    if not os.path.isdir(POSTS_DIR):
        return posts
    for cat_dir in sorted(os.listdir(POSTS_DIR)):
        full = os.path.join(POSTS_DIR, cat_dir)
        if not os.path.isdir(full):
            continue
        cat_id = cat_dir.lower()
        for fn in sorted(os.listdir(full)):
            if not fn.lower().endswith((".html", ".htm")):
                continue
            path = os.path.join(full, fn)
            if not os.path.isfile(path):
                continue
            src = read_text(path)
            rel = "posts/%s/%s" % (cat_dir, fn)
            title = tidy_title(src, fn)
            posts.append({
                "title": title,
                "url": rel,
                "date": file_date(fn, src, path),
                "category": cat_id,
                "categoryLabel": CATEGORY_LABELS.get(cat_id, cat_dir),
                "desc": build_summary(src, title=title),
                "tags": build_tags(src),
                "size": round(os.path.getsize(path) / 1024.0, 1),
            })
    posts.sort(key=lambda p: (p["date"], p["title"]), reverse=True)
    return posts


def dedupe(posts):
    """同一天 + 同标题（忽略空格/标点）视为重复，只保留最新的一个"""
    seen, out = {}, []
    for p in posts:
        key = (p["date"], re.sub(r"[\s|｜·—–\-_（）()]+", "", p["title"]))
        if key in seen:
            out[seen[key]] = p   # 后者覆盖（列表已按日期倒序，保留靠前者亦可）
            continue
        seen[key] = len(out)
        out.append(p)
    return out


def categories_of(posts):
    order, seen = [], {}
    for p in posts:
        if p["category"] not in seen:
            seen[p["category"]] = 0
            order.append({"id": p["category"], "label": p["categoryLabel"]})
        seen[p["category"]] += 1
    for c in order:
        c["count"] = seen[c["id"]]
    return order


# ----------------------------- 输出 -----------------------------
def write_index(posts, cats):
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR)

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    js = "/* 本文件由 tools/publish.py 自动生成，请勿手动编辑 */\n"
    js += "/* 生成时间: %s  共 %d 篇 */\n" % (stamp, len(posts))
    js += "window.SITE_POSTS = " + json.dumps(posts, ensure_ascii=False, indent=2) + ";\n\n"
    js += "window.SITE_CATS = " + json.dumps(cats, ensure_ascii=False, indent=2) + ";\n"
    with io.open(os.path.join(DATA_DIR, "posts.js"), "w", encoding="utf-8") as f:
        f.write(js)
    with io.open(os.path.join(DATA_DIR, "posts.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"updated": stamp, "posts": posts, "categories": cats},
                           ensure_ascii=False, indent=2))
    return stamp


def write_feeds(posts, base):
    now = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
    items = []
    for p in posts[:40]:
        link = base + p["url"]
        items.append(
            u"    <item>\n"
            u"      <title>{t}</title>\n"
            u"      <link>{l}</link>\n"
            u"      <guid isPermaLink=\"true\">{l}</guid>\n"
            u"      <pubDate>{d}</pubDate>\n"
            u"      <description><![CDATA[{desc}]]></description>\n"
            u"    </item>".format(
                t=xml_escape(p["title"]), l=link, d=rss_date(p["date"]), desc=p["desc"])
        )
    rss = (
        u'<?xml version="1.0" encoding="UTF-8"?>\n'
        u'<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        u'  <channel>\n'
        u'    <title>半导体 · 财经 学习笔记</title>\n'
        u'    <link>{base}</link>\n'
        u'    <description>半导体知识脉络与每日财经金融简报</description>\n'
        u'    <language>zh-CN</language>\n'
        u'    <lastBuildDate>{now}</lastBuildDate>\n'
        u'{items}\n'
        u'  </channel>\n'
        u'</rss>\n'
    ).format(base=base, now=now, items=u"\n".join(items))
    with io.open(os.path.join(ROOT, "feed.xml"), "w", encoding="utf-8") as f:
        f.write(rss)

    urls = [u"    <url><loc>{base}</loc><priority>1.0</priority></url>".format(base=base)]
    for p in posts:
        urls.append(u"    <url><loc>{base}{u}</loc><lastmod>{d}</lastmod></url>".format(
            base=base, u=p["url"], d=p["date"]))
    sm = (u'<?xml version="1.0" encoding="UTF-8"?>\n'
          u'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          u'{urls}\n</urlset>\n'.format(urls=u"\n".join(urls)))
    with io.open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sm)


def xml_escape(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rss_date(d):
    try:
        return datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%a, %d %b %Y 00:00:00 +0800")
    except Exception:
        return datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")


# ----------------------------- 草稿 -----------------------------
def new_draft(category, name):
    cat_dir = os.path.join(POSTS_DIR, category)
    if not os.path.isdir(cat_dir):
        os.makedirs(cat_dir)
    if not name.lower().endswith(".html"):
        name += ".html"
    target = os.path.join(cat_dir, name)
    src = os.path.join(TOOLS_DIR, "template.html")
    if os.path.exists(target):
        print("! 文件已存在，未覆盖：%s" % target)
        return target
    if not os.path.exists(src):
        print("! 找不到模板 tools/template.html")
        return target
    today = datetime.date.today().isoformat()
    content = read_text(src)
    content = content.replace("{{TITLE}}", os.path.splitext(name)[0]).replace("{{DATE}}", today)
    with io.open(target, "w", encoding="utf-8") as f:
        f.write(content)
    print("+ 已创建草稿：posts/%s/%s" % (category, name))
    return target


# ----------------------------- 主流程 -----------------------------
def main():
    ap = argparse.ArgumentParser(description="扫描 posts/ 生成索引并提交推送")
    ap.add_argument("--no-push", action="store_true", help="只生成索引，不执行 git 提交推送")
    ap.add_argument("--serve", action="store_true", help="生成索引后启动本地预览服务 http://127.0.0.1:8000")
    ap.add_argument("--draft", nargs=2, metavar=("分类", "文件名"), help="从模板新建草稿，如 --draft finance 2026-10-01-早报")
    ap.add_argument("--message", "-m", default=None, help="自定义提交信息")
    args = ap.parse_args()

    print("=" * 56)
    print(" 静态博客发布脚本")
    print("=" * 56)

    if args.draft:
        new_draft(args.draft[0], args.draft[1])
        print("=" * 56)
        return

    old_count = -1
    old_js = os.path.join(DATA_DIR, "posts.js")
    if os.path.exists(old_js):
        m = re.search(r"共 (\d+) 篇", read_text(old_js))
        if m:
            old_count = int(m.group(1))

    posts = dedupe(scan())
    cats = categories_of(posts)
    if not posts:
        print("! posts/ 下没有找到任何 HTML 文章。")
    else:
        print("扫描到 %d 篇文章：" % len(posts))
        for p in posts[:200]:
            flag = "NEW " if old_count >= 0 and len(posts) > old_count and p is posts[0] else "    "
            print("  %s[%s] %s  %s" % (flag, p["date"], p["categoryLabel"], p["title"]))

    write_index(posts, cats)
    base = site_url()
    write_feeds(posts, base)
    print("\n已生成：data/posts.js / posts.json / feed.xml / sitemap.xml")
    print("站点地址：%s" % base)

    if args.serve:
        print("\n本地预览： http://127.0.0.1:8000  （Ctrl+C 结束）")
        print("=" * 56)
        subprocess.call([sys.executable, "-m", "http.server", "8000", "--bind", "127.0.0.1"], cwd=ROOT)
        return

    if args.no_push:
        print("\n已跳过推送（--no-push）。")
        print("=" * 56)
        return

    print("\n开始提交到 Git …")
    try:
        run_git(["add", "-A"])
        status = run_git(["status", "--porcelain"], check=False)
        if not status:
            print("没有文件变更，无需提交。")
            print("=" * 56)
            return
        added = len(posts) - old_count if old_count >= 0 else len(posts)
        msg = args.message or ("docs: 更新博客索引 %s（共 %d 篇%s）" % (
            datetime.date.today().isoformat(), len(posts),
            "，新增 %d 篇" % added if added > 0 else ""))
        run_git(["commit", "-m", msg])
        print("提交信息：%s" % msg)
        branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], check=False) or "main"
        run_git(["push", "origin", branch])
        print("推送成功！GitHub Pages 约 1-2 分钟后更新：%s" % base)
    except Exception as e:
        print("! Git 操作失败：%s" % e)
        print("  索引文件已生成，可稍后手动执行 git add / commit / push，或双击 发布更新.bat 重试。")
    print("=" * 56)


if __name__ == "__main__":
    main()
