# -*- coding: utf-8 -*-
"""
同步「集成电路学习路径 · 全系列导航」。

维护三处：
  1. 33 篇专题文章文末的 .series 导航（编号 1..33，current = 自己，末位挂总纲）
  2. 路径地图（总纲页）文末的导航卡片 —— 该类页用独立样式，自带 CSS
  3. 目录页 index.html 的「全系列导航」区块 —— 该类页用 site.css 变量，适配双主题

新增文章时：
  - 在 NAV 里按顺序补一行（编号、文件名、标题）
  - 重跑本脚本

用法（仓库根目录）：
    python tools/sync_series_nav.py
    python tools/sync_series_nav.py --check     # 只检查是否已同步，不写盘
"""
import argparse
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'posts', 'semiconductor') + os.sep

NAV_TITLE = '集成电路学习路径 · 全系列导航'

NAV = [
    (1, '2026-10-01-固体物理基础-晶格晶向晶胞与晶面.html', '固体物理基础 · 晶格、晶向、晶胞与晶面'),
    (2, '2026-10-06-薛定谔方程泡利不相容与费米狄拉克分布-固体物理的量子三基石.html', '薛定谔方程、泡利不相容与费米-狄拉克分布 · 固体物理的量子三基石'),
    (3, '2026-10-01-半导体物理基础-能带与载流子.html', '半导体物理基础 · 能带与载流子'),
    (4, '2026-10-01-PN结原理与特性.html', 'PN 结原理与特性'),
    (5, '2026-10-01-MOSFET工作原理与特性曲线.html', 'MOSFET 工作原理与特性曲线'),
    (6, '2026-10-01-CMOS集成电路基础-反相器与逻辑门.html', 'CMOS 集成电路基础 · 反相器与逻辑门'),
    (7, '2026-10-02-摩尔定律与器件微缩-从平面到FinFET与GAA.html', '摩尔定律与器件微缩 · 从平面到 FinFET 与 GAA'),
    (8, '2026-10-02-存储器原理-DRAM-NAND与新型存储.html', '存储器 · DRAM、NAND 与新型存储'),
    (9, '2026-10-02-半导体材料全景-Si-SiC-GaN与宽禁带.html', '半导体材料全景 · Si、SiC、GaN 与宽禁带'),
    (10, '2026-10-01-硅单晶生长与衬底制备工艺.html', '硅单晶生长与衬底制备工艺'),
    (11, '2026-10-01-芯片制造工艺流程详解.html', '芯片制造工艺流程详解'),
    (12, '2026-10-01-光刻工艺详解-从光学原理到EUV.html', '光刻工艺详解 · 从光学原理到 EUV'),
    (13, '2026-10-01-刻蚀工艺详解-湿法与等离子体.html', '刻蚀工艺详解 · 湿法与等离子体'),
    (14, '2026-10-01-薄膜沉积与掺杂工艺详解.html', '薄膜沉积与掺杂工艺详解'),
    (15, '2026-10-01-CMP平坦化量测与良率控制.html', 'CMP 平坦化、量测与良率控制'),
    (16, '2026-10-01-芯片设计与EDA工具链.html', '芯片设计与 EDA 工具链'),
    (17, '2026-10-01-版图设计实战-DRC-LVS与匹配技巧.html', '版图设计实战 · DRC、LVS 与匹配技巧'),
    (18, '2026-10-01-芯片封装测试与失效分析.html', '芯片封装测试与失效分析'),
    (19, '2026-10-02-先进封装与系统级集成-2.5D-3D-Chiplet与HBM.html', '先进封装与系统级集成 · 2.5D/3D、Chiplet 与 HBM'),
    (20, '2026-10-02-半导体设备与产业链-核心装备全景.html', '半导体设备与产业链 · 核心装备全景'),
    (21, '2026-10-05-类脑计算与存算一体-后摩尔时代的两条突围路线.html', '类脑计算与存算一体 · 后摩尔时代的两条突围路线'),
    (22, '2026-10-05-光计算-用光子代替电子的算力革命.html', '光计算 · 用光子代替电子的算力革命'),
    (23, '2026-10-05-量子计算-从量子比特到量子优越性.html', '量子计算 · 从量子比特到量子优越性'),
    (24, '2026-10-05-雷达信号处理全链路-从回波到目标.html', '雷达信号处理全链路 · 从回波到目标'),
    (25, '2026-10-06-计算机发展史-从电子管到晶体管-计算机如何工作.html', '计算机发展史 · 从电子管到晶体管，计算机如何工作'),
    (26, '2026-10-06-数字电路模拟电路与芯片家族-MCU-FPGA-CPU-GPU.html', '数字电路、模拟电路与芯片家族 · MCU、FPGA、CPU、GPU 是什么'),
    (27, '2026-10-06-硅基的语言-从晶体管开关到编程语言与操作系统.html', '硅基的语言 · 从晶体管开关到编程语言与操作系统'),
    (28, '2026-10-07-模拟集成电路设计-电流镜带隙基准与运放.html', '模拟集成电路设计 · 电流镜、带隙基准与运放'),
    (29, '2026-10-07-数字后端物理设计-布局布线时钟树与静态时序分析.html', '数字后端物理设计 · 布局布线、时钟树与静态时序分析'),
    (30, '2026-10-07-芯片可靠性物理-电迁移TDDB-NBTI与ESD.html', '芯片可靠性物理 · 电迁移、TDDB、NBTI 与 ESD'),
    (31, '2026-10-07-芯片产业分工与商业模式-IDM-Fabless-Foundry与OSAT.html', '芯片产业分工与商业模式 · IDM、Fabless、Foundry 与 OSAT'),
    (32, '2026-10-07-晶圆厂经济学与芯片成本模型.html', '晶圆厂经济学与芯片成本模型'),
    (33, '2026-10-07-一颗芯片的诞生全流程-从需求到量产.html', '一颗芯片的诞生全流程 · 从需求到量产'),
]
APPENDIX = ('2026-06-01-半导体器件新手路径地图.html', '附：半导体器件新手路径地图（总纲）')

MAP_PAGE = '2026-06-01-半导体器件新手路径地图.html'
INDEX_PAGE = 'index.html'

B = '<!-- SERIES-NAV:BEGIN -->'
E = '<!-- SERIES-NAV:END -->'

CSS_B = '/* SERIES-NAV-CSS:BEGIN */'
CSS_E = '/* SERIES-NAV-CSS:END */'


def inject_css(s, css):
    """把 CSS 注入 <style> 尾部；已存在则整体替换（幂等）。"""
    if CSS_B in s and CSS_E in s:
        return re.sub(re.escape(CSS_B) + r'.*?' + re.escape(CSS_E), lambda _: css, s, flags=re.S)
    i = s.find('</style>')
    assert i != -1, '找不到 </style>'
    return s[:i] + css + '\n' + s[i:]


def build_items(current_file, indent):
    out = []
    for num, fn, title in NAV:
        text = '第 %d 篇：%s' % (num, title)
        if fn == current_file:
            out.append('%s<li class="current">%s</li>' % (indent, text))
        else:
            out.append('%s<li><a href="%s">%s</a></li>' % (indent, fn, text))
    fn, title = APPENDIX
    if fn == current_file:
        out.append('%s<li class="current">%s</li>' % (indent, title))
    else:
        out.append('%s<li><a href="%s">%s</a></li>' % (indent, fn, title))
    return '\n'.join(out)


# ---------------------------------------------------------------- 1. 文章页
def sync_articles(write):
    changed = 0
    for num, fn, title in NAV:
        path = P + fn
        s = io.open(path, encoding='utf-8').read()
        # 统一标题用词（历史上有「系列导航 / 全系列导航」两种写法）
        s2 = s.replace('集成电路学习路径 · 系列导航', NAV_TITLE)
        m = re.search(r'(<div class="series-title">[^<]*</div>\s*<ol>\n)(.*?)(\n\s*</ol>)', s2, re.S)
        if not m:
            print('  !! 找不到导航块：%s' % fn)
            continue
        items = build_items(fn, '            ')
        new = s2[:m.start()] + m.group(1) + items + m.group(3) + s2[m.end():]
        if new != s:
            if write:
                io.open(path, 'w', encoding='utf-8').write(new)
            changed += 1
    print('文章页导航：%d / %d 需更新' % (changed, len(NAV)))
    return changed


# --------------------------------------------------- 2. 总纲页（独立样式）
MAP_CSS = """%s
    /* 全系列导航（由 tools/sync_series_nav.py 生成，请勿手改） */
    .series-nav-card { margin: 2rem 0 0; padding: 1.6rem; }
    .series-nav-head {
        display: flex; align-items: baseline; gap: 0.8rem; flex-wrap: wrap;
        margin-bottom: 1rem;
    }
    .series-nav-title {
        font-size: 0.8rem; letter-spacing: 0.12em; text-transform: uppercase;
        font-weight: 700; color: #7ad0e0;
    }
    .series-nav-count { font-size: 0.75rem; color: #9ac7d9; opacity: 0.8; }
    .series-nav-ol { padding-left: 1.7em; margin: 0; font-size: 0.85rem; line-height: 1.95; }
    .series-nav-ol li { color: #9ac7d9; }
    .series-nav-ol li a { color: #c8e6f2; text-decoration: none; }
    .series-nav-ol li a:hover { color: #4effe0; text-decoration: underline; text-underline-offset: 3px; }
    .series-nav-ol li.current { list-style: none; margin-left: -1.7em; font-weight: 700; color: #4effe0; }
    .series-nav-ol li.current::before { content: "▸ "; }
    .series-nav-note {
        margin-top: 1rem; padding-top: 0.9rem; border-top: 1px dashed #2c6a7a;
        font-size: 0.78rem; color: #9ac7d9;
    }
%s""" % (CSS_B, CSS_E)


def map_block():
    n = len(NAV)
    return '''%s
    <div class="card series-nav-card">
        <div class="series-nav-head">
            <span class="series-nav-title">%s</span>
            <span class="series-nav-count">共 %d 篇专题 + 1 篇总纲</span>
        </div>
        <ol class="series-nav-ol">
%s
        </ol>
        <div class="series-nav-note">
            编号即推荐阅读顺序：前 7 篇是物理与器件地基，8–20 篇走通材料与制造，21 篇之后是设计与前沿。
            如果你刚开始，先回到上面第 0 阶段，按五阶段路径推进；想直接照单读，就从上往下点。
        </div>
    </div>
    %s''' % (B, NAV_TITLE, n, build_items(MAP_PAGE, '            '), E)


def sync_map(write):
    path = P + MAP_PAGE
    s = io.open(path, encoding='utf-8').read()
    changed = False

    # CSS：注入/替换
    s2 = inject_css(s, MAP_CSS)
    if s2 != s:
        s = s2
        changed = True

    # HTML：插到页脚之前
    if B in s:
        new = re.sub(re.escape(B) + r'.*?' + re.escape(E), lambda _: map_block(), s, flags=re.S)
    else:
        anchor = '    <div class="footer">'
        assert s.count(anchor) == 1, '找不到页脚锚点'
        new = s.replace(anchor, map_block() + '\n\n' + anchor)
    if new != s:
        s = new
        changed = True

    if changed and write:
        io.open(path, 'w', encoding='utf-8').write(s)
    print('总纲页导航：%s' % ('已更新' if changed else '已是最新'))
    return changed


# ------------------------------------------------ 3. 目录页（site.css 变量）
IDX_CSS = """%s
/* 全系列导航（由 tools/sync_series_nav.py 生成，请勿手改） */
.series-nav{max-width:860px;margin:0 auto;padding:22px 26px;background:var(--surface);
  border:1px solid var(--border);border-radius:var(--radius);box-shadow:var(--shadow-sm)}
.series-nav-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:12px}
.series-nav-title{font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;
  font-weight:700;color:var(--semi)}
.series-nav-count{font-size:12.5px;color:var(--text-mute)}
.series-nav ol{margin:0;padding-left:1.7em;font-size:.9rem;line-height:2}
.series-nav li{color:var(--text-soft)}
.series-nav li a{color:var(--text);text-decoration:none}
.series-nav li a:hover{color:var(--semi);text-decoration:underline;text-underline-offset:3px}
.series-nav-note{margin-top:12px;padding-top:12px;border-top:1px dashed var(--border);
  font-size:12.5px;color:var(--text-mute)}
%s""" % (CSS_B, CSS_E)


def idx_block():
    n = len(NAV)
    return '''%s
  <section id="seriesNavSection" style="margin:0 0 60px">
    <h2 class="sec-title">全系列导航</h2>
    <p class="sec-sub">按学习顺序排列的完整清单，与每篇文章底部的系列导航保持一致；上面的阶段视图便于按主题选读，这里给出的是从头到尾的顺序。</p>
    <div class="series-nav">
      <div class="series-nav-head">
        <span class="series-nav-title">%s</span>
        <span class="series-nav-count">共 %d 篇专题 + 1 篇总纲</span>
      </div>
      <ol>
%s
      </ol>
      <div class="series-nav-note">本区块由 <code>tools/sync_series_nav.py</code> 自动生成，新增文章后重跑脚本即可同步。</div>
    </div>
  </section>
  %s''' % (B, NAV_TITLE, n, build_items(None, '        '), E)


def sync_index(write):
    path = P + INDEX_PAGE
    s = io.open(path, encoding='utf-8').read()
    changed = False

    s2 = inject_css(s, IDX_CSS)
    if s2 != s:
        s = s2
        changed = True

    if B in s:
        new = re.sub(re.escape(B) + r'.*?' + re.escape(E), lambda _: idx_block(), s, flags=re.S)
    else:
        anchor = '  <section id="archiveSection"'
        assert s.count(anchor) == 1, '找不到 archiveSection 锚点'
        new = s.replace(anchor, idx_block() + '\n\n' + anchor)
    if new != s:
        s = new
        changed = True

    if changed and write:
        io.open(path, 'w', encoding='utf-8').write(s)
    print('目录页导航：%s' % ('已更新' if changed else '已是最新'))
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true', help='只检查，不写盘')
    args = ap.parse_args()
    write = not args.check

    total = sync_articles(write)
    total += sync_map(write)
    total += sync_index(write)
    if args.check:
        print('\n%s' % ('全部已同步' if not total else '有 %d 处待同步' % total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
