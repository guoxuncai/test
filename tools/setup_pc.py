#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
==========================================================
 新电脑初始化 · 多机协作配置
==========================================================
在每一台要维护本博客的电脑上，克隆仓库后运行一次即可（双击根目录 setup-pc.bat）。

它会完成：
  1. 启用仓库自带的 .githooks（pre-push 会在本机落后于远端时拦截推送，防止覆盖他人改动）
  2. 设置 pull.rebase + rebase.autoStash：拉取时自动变基，不产生多余的 merge 提交
  3. 开启 rerere：同一处冲突解决过一次后，下次自动复用
  4. 关闭 core.autocrlf，交由 .gitattributes 统一行尾（Windows/macOS 混用不打架）
  5. 检查提交身份（user.name / user.email）与 Python、SSH 可用性

用法：
  python tools/setup_pc.py            # 应用配置
  python tools/setup_pc.py --check    # 只体检，不改动
==========================================================
"""
import os
import re
import sys
import socket
import argparse
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 需要在本机仓库里写死的协作参数（只影响当前这台电脑，不会提交到 GitHub）
LOCAL_CONFIG = [
    ("core.hooksPath", ".githooks", "启用仓库钩子（pre-push 拦截落后推送）"),
    ("pull.rebase", "true", "拉取时自动变基，避免多余 merge 提交"),
    ("rebase.autoStash", "true", "有未提交改动时自动 stash 再变基"),
    ("rerere.enabled", "true", "记住冲突解法，下次自动复用"),
    ("core.autocrlf", "false", "行尾交给 .gitattributes 统一管理"),
    ("core.longpaths", "true", "支持 Windows 长路径"),
    ("push.default", "current", "推送当前分支"),
    ("core.quotepath", "false", "中文文件名正常显示"),
]


def run_git(args, check=False):
    r = subprocess.run(["git"] + args, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip())
    return (r.stdout or "").strip()


def machine_name():
    return os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or socket.gethostname()


def is_git_repo():
    return os.path.isdir(os.path.join(ROOT, ".git"))


def check_item(key, want):
    """返回 (状态, 当前值)；状态：ok / diff / missing"""
    cur = run_git(["config", "--local", "--get", key])
    if not cur:
        return "missing", ""
    return ("ok" if cur.strip().lower() == str(want).strip().lower() else "diff"), cur.strip()


def check_identity():
    name = run_git(["config", "--get", "user.name"])
    email = run_git(["config", "--get", "user.email"])
    return name, email


def check_ssh():
    remote = run_git(["remote", "get-url", "origin"])
    if not remote:
        return "未配置 origin 远端", False
    if remote.startswith("git@") or remote.startswith("ssh://"):
        try:
            r = subprocess.run(["ssh", "-T", "-o", "StrictHostKeyChecking=no", "git@github.com"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace",
                               timeout=20)
            out = (r.stdout or "") + (r.stderr or "")
            ok = ("successfully authenticated" in out.lower()) or r.returncode in (0, 1)
            return ("SSH 可用：%s" % out.strip().splitlines()[0] if out.strip() else "SSH 可用", ok)
        except Exception as e:
            return "SSH 检测失败：%s（可手动执行 ssh -T git@github.com 确认）" % e, False
    return "远端使用 HTTPS：%s（推送时输入令牌即可）" % remote, True


def main():
    ap = argparse.ArgumentParser(description="新电脑初始化：配置多机协作所需的 git 参数")
    ap.add_argument("--check", action="store_true", help="只体检，不改动任何配置")
    args = ap.parse_args()

    print("=" * 58)
    print(" 博客 · 新电脑初始化（%s）" % machine_name())
    print("=" * 58)

    if not is_git_repo():
        print("! 当前目录不是 git 仓库：%s" % ROOT)
        print("  请先克隆： git clone git@github.com:guoxuncai/test.git")
        print("=" * 58)
        sys.exit(1)

    apply = not args.check
    print("\n%s" % ("【体检模式】不改动任何配置" if args.check else "【配置模式】写入本机 git 配置"))

    print("\n① 协作参数")
    changed = 0
    for key, want, desc in LOCAL_CONFIG:
        status, cur = check_item(key, want)
        if status == "ok":
            print("  ✓ %-18s = %-12s %s" % (key, cur, desc))
            continue
        if apply:
            run_git(["config", "--local", key, want], check=False)
            now, _ = check_item(key, want)
            flag = "✓" if now == "ok" else "×"
            changed += 1
            print("  %s %-18s → %-12s %s" % (flag, key, want, desc))
        else:
            print("  × %-18s 当前=%-10s 应为=%-10s %s" % (key, cur or "(未设置)", want, desc))

    print("\n② 提交身份")
    name, email = check_identity()
    if name and email:
        print("  ✓ %s <%s>" % (name, email))
    else:
        print("  × 缺少提交身份 —— 请执行：")
        print("      git config --global user.name  \"你的名字\"")
        print("      git config --global user.email \"你的邮箱\"")

    print("\n③ 远端连通性")
    msg, ok = check_ssh()
    print("  %s %s" % ("✓" if ok else "×", msg))

    print("\n④ 行尾规范化（.gitattributes 已随仓库生效）")
    ga = os.path.join(ROOT, ".gitattributes")
    if os.path.exists(ga):
        print("  ✓ 已存在 .gitattributes：文本文件统一 LF，.bat/.cmd/.ps1 为 CRLF")
        if apply:
            # 让已有文件按新规则重新归一化一次（只影响本机工作区，需提交后才同步给别人）
            r = subprocess.run(["git", "add", "--renormalize", "."], cwd=ROOT,
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            print("  ✓ 已执行 git add --renormalize .（如有改动会在下次发布时一并提交）")
    else:
        print("  × 缺少 .gitattributes")

    print("\n⑤ Python")
    print("  ✓ %s" % sys.executable)

    print("\n" + "=" * 58)
    if apply:
        print("初始化完成，改动了 %d 项配置。" % changed)
        print("日常用法：写完文章双击 publish.bat（会自动先拉后推）；")
        print("          只想同步别人的改动时双击 sync.bat。")
    else:
        print("体检完成。要应用配置请运行： python tools/setup_pc.py")
    print("=" * 58)


if __name__ == "__main__":
    main()
