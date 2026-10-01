# -*- coding: utf-8 -*-
"""校验系列导航：每篇的导航项数、当前项、链接文件是否存在。"""
import re, os, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'posts', 'semiconductor')

RE_SERIES = re.compile(r'<div class="series">.*?</ol>', re.S)
RE_LI = re.compile(r'<li[^>]*>(.*?)</li>', re.S)
RE_HREF = re.compile(r'href="([^"]+)"')
RE_META = re.compile(r'集成电路学习路径 · 第 (\d+) 篇')

files = [f for f in sorted(os.listdir(BASE)) if f.endswith('.html') and RE_SERIES.search(open(os.path.join(BASE, f), encoding='utf-8').read())]
print('含系列导航的文章：%d 篇\n' % len(files))

missing = []
for f in files:
    src = open(os.path.join(BASE, f), encoding='utf-8').read()
    block = RE_SERIES.search(src).group(0)
    lis = [m.group(0) for m in RE_LI.finditer(block)]
    cur = [x for x in lis if 'class="current"' in x]
    cur_txt = re.sub(r'<[^>]+>', '', cur[0]).strip() if cur else '!! 无当前项'
    m = RE_META.search(src)
    num = m.group(1) if m else '?'
    print('%-62s 导航%2d项 meta第%s篇 %s' % (f[:60], len(lis), num, cur_txt))
    for li in lis:
        h = RE_HREF.search(li)
        if h and not os.path.exists(os.path.join(BASE, h.group(1))):
            missing.append((f, h.group(1)))

print('\n链接缺失:', missing if missing else '无')
