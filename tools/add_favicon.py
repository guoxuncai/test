# -*- coding: utf-8 -*-
"""为站内所有 HTML 注入 favicon 声明（幂等）。

用法： python tools/add_favicon.py
说明：
  - 按每个文件相对站点根的深度自动计算相对路径前缀（根页面 ""，posts/xxx/ 为 "../../"）
  - tools/template.html 是草稿模板，生成到 posts/<分类>/ 下，固定用 "../../"
  - 已注入过的文件跳过，不重复写入
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BLOCK = '''<!-- favicon -->
<link rel="icon" href="{p}favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="{p}favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="{p}favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="{p}favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="{p}apple-touch-icon.png">
'''


def prefix_for(path):
    """相对站点根的目录深度 -> ../ 前缀"""
    rel = os.path.relpath(path, ROOT).replace('\\', '/')
    depth = rel.count('/')
    return '../' * depth + 'assets/img/'


def inject(path, prefix=None):
    s = io.open(path, encoding='utf-8').read()
    if 'rel="icon"' in s or '<!-- favicon -->' in s:
        return 'skip'
    if '</head>' not in s:
        return 'nohead'
    if prefix is None:
        prefix = prefix_for(path)
    block = BLOCK.format(p=prefix)
    s = s.replace('</head>', block + '</head>', 1)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)
    return 'ok:' + prefix


def main():
    changed = skipped = 0
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in ('.git', 'assets', 'node_modules')]
        for fn in sorted(files):
            if not fn.lower().endswith('.html'):
                continue
            full = os.path.join(base, fn)
            # 模板生成到 posts/<分类>/ 下，前缀固定两级
            pfx = '../../assets/img/' if fn == 'template.html' else None
            r = inject(full, pfx)
            rel = os.path.relpath(full, ROOT).replace('\\', '/')
            if r.startswith('ok'):
                changed += 1
                print('  + %-58s %s' % (rel, r[3:]))
            elif r == 'skip':
                skipped += 1
            else:
                print('  ! %-58s %s' % (rel, r))
    print('injected %d, skipped(already) %d' % (changed, skipped))


if __name__ == '__main__':
    main()
