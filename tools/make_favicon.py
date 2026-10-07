# -*- coding: utf-8 -*-
"""
从一张源图生成站点图标素材集（favicon 全套）。

用法（在仓库根目录执行）：
    python tools/make_favicon.py
    python tools/make_favicon.py --src assets/img/favicon-source.jpg
    python tools/make_favicon.py --crop 148,62,478,392      # 自定义方形裁剪框
    python tools/make_favicon.py --center 313,227 --side 330

产出（写入 assets/img/）：
    favicon.ico          16/32/48 三尺寸内嵌（经典 BMP 条目，兼容性最好）
    favicon-32.png       标签栏高清屏
    favicon-16.png       标签栏普屏
    apple-touch-icon.png 180x180，加到主屏/收藏用
    favicon.svg          把位图以 base64 内嵌的 SVG 包装，供现代浏览器优先取用

依赖：Pillow（装在隔离 venv 里，不要污染全局环境）
"""
import argparse
import base64
import io
import os
import sys

from PIL import Image, ImageEnhance

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, 'assets', 'img')

# 本图（蓝图发光芯片）的默认裁剪：以发光环为准取正方形
DEFAULT_SRC = os.path.join(OUT_DIR, 'favicon-source.jpg')
DEFAULT_CENTER = (313, 227)
DEFAULT_SIDE = 330


def boost(im, color=1.10, contrast=1.05, sharpness=1.25):
    """小幅增艳/增对比/锐化——小尺寸下图案更容易辨认。"""
    im = ImageEnhance.Color(im).enhance(color)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Sharpness(im).enhance(sharpness)
    return im


def crop_square(im, center, side):
    cx, cy = center
    half = side // 2
    box = (cx - half, cy - half, cx + half, cy + half)
    w, h = im.size
    if box[0] < 0 or box[1] < 0 or box[2] > w or box[3] > h:
        raise SystemExit('裁剪框 %s 超出图像范围 %s' % (box, im.size))
    return im.crop(box)


def png_bytes(im):
    buf = io.BytesIO()
    im.save(buf, format='PNG', optimize=True)
    return buf.getvalue()


def write(path, data):
    with open(path, 'wb') as f:
        f.write(data)
    print('  %-22s %7d B' % (os.path.basename(path), len(data)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=DEFAULT_SRC)
    ap.add_argument('--center', default=None, help='裁剪中心 "x,y"')
    ap.add_argument('--side', type=int, default=None, help='正方形边长')
    ap.add_argument('--crop', default=None, help='直接给方形裁剪框 "x0,y0,x1,y1"')
    args = ap.parse_args()

    if not os.path.exists(args.src):
        raise SystemExit('源图不存在：%s' % args.src)

    src = Image.open(args.src).convert('RGB')
    print('源图 %s  %dx%d' % (os.path.basename(args.src), src.size[0], src.size[1]))

    if args.crop:
        x0, y0, x1, y1 = [int(v) for v in args.crop.split(',')]
        if x1 - x0 != y1 - y0:
            raise SystemExit('裁剪框必须是正方形，当前 %dx%d' % (x1 - x0, y1 - y0))
        square = src.crop((x0, y0, x1, y1))
    else:
        center = tuple(int(v) for v in args.center.split(',')) if args.center else DEFAULT_CENTER
        side = args.side or DEFAULT_SIDE
        square = crop_square(src, center, side)
    print('裁剪后 %dx%d' % square.size)

    os.makedirs(OUT_DIR, exist_ok=True)

    # 统一先缩到 512 作为所有尺寸的重采样源，避免多次缩放的锯齿差异
    base = square.resize((512, 512), Image.LANCZOS)

    p16 = boost(base.resize((16, 16), Image.LANCZOS))
    p32 = boost(base.resize((32, 32), Image.LANCZOS))
    p180 = base.resize((180, 180), Image.LANCZOS)

    print('写出：')
    write(os.path.join(OUT_DIR, 'favicon-16.png'), png_bytes(p16))
    write(os.path.join(OUT_DIR, 'favicon-32.png'), png_bytes(p32))
    write(os.path.join(OUT_DIR, 'apple-touch-icon.png'), png_bytes(p180))

    # ICO：三尺寸内嵌
    ico_path = os.path.join(OUT_DIR, 'favicon.ico')
    base.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])
    print('  %-22s %7d B  (16/32/48)' % ('favicon.ico', os.path.getsize(ico_path)))

    # SVG：内嵌位图（保留现代浏览器的 SVG favicon 引用不失效）
    emb = base.resize((160, 160), Image.LANCZOS)
    buf = io.BytesIO()
    emb.save(buf, format='JPEG', quality=82, optimize=True, progressive=True)
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160" '
        'role="img" aria-label="站点图标">\n'
        '  <image width="160" height="160" href="data:image/jpeg;base64,%s"/>\n'
        '</svg>\n' % b64
    ).encode('utf-8')
    write(os.path.join(OUT_DIR, 'favicon.svg'), svg)

    # 顺手留一份源图，方便以后换裁剪重跑
    src_path = os.path.join(OUT_DIR, 'favicon-source.jpg')
    if os.path.abspath(args.src) != os.path.abspath(src_path):
        src.save(src_path, format='JPEG', quality=88, optimize=True)
        print('  %-22s %7d B  (源图备份)' % ('favicon-source.jpg', os.path.getsize(src_path)))


if __name__ == '__main__':
    sys.exit(main())
