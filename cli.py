# cli.py
# 命令行入口，复用 backend 模块

import argparse
from backend import generate_image

def main():
    parser = argparse.ArgumentParser(description='生成带文字的透明背景图片')
    parser.add_argument('--background', type=str, help='背景图片路径')
    parser.add_argument('--width', type=int, default=1920, help='画布宽度')
    parser.add_argument('--height', type=int, default=1080, help='画布高度')
    parser.add_argument('--sub-text', action='store_true', help='添加副标题')
    parser.add_argument('--shadow', action='store_true', help='添加阴影')
    parser.add_argument('--main-text', type=str, default='主标题', help='主标题文字')
    parser.add_argument('--second-line', type=str, default='', help='第二行文字')
    parser.add_argument('--output', type=str, default='./output.png', help='输出路径')
    parser.add_argument('--shadow-opacity', type=float, default=0.08, help='阴影不透明度')

    args = parser.parse_args()
    img = generate_image(
        width=args.width,
        height=args.height,
        main_text=args.main_text,
        second_line=args.second_line,
        sub_text_enabled=args.sub_text,
        shadow_enabled=args.shadow,
        shadow_opacity=args.shadow_opacity,
        background_path=args.background
    )
    img.save(args.output)
    print(f"图片已保存至: {args.output}")

if __name__ == '__main__':
    main()