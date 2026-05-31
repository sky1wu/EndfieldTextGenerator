# backend.py
# 所有核心生成函数和常量定义

from pywubi import wubi as wb
from PIL import Image, ImageFont, ImageDraw
from typing import Tuple, Union, List, Optional
import math
import re
import random
import os
import sys

# 运行环境监测函数
def resource_path(relative_path):
    """获取资源的绝对路径，兼容开发环境和打包后的 exe"""
    # 判断是否为打包后的环境
    if getattr(sys, 'frozen', False):
        # Nuitka 打包后，__file__ 指向临时解压目录中的 .pyc 文件
        base_path = os.path.dirname(os.path.abspath(__file__))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# ---------------------------- 宏定义 ----------------------------
FONT_MAIN_TEXT_PATH = resource_path("assets/NotoSansHans-Black.otf")
FONT_SUB_TEXT_PATH = resource_path("assets/EndfieldByButan.ttf")
FONT_MAIN_TEXT_ENG_PATH = resource_path("assets/NovecentoWideUltraBold.otf")

MAIN_TEXT_HEIGHT = 0.2472
MAIN_TEXT_SEP = 0.021875
MIN_MAIN_TEXT_SEP_PIXEL = 1

SUB_TEXT_HEIGHT = 0.025
SUB_TEXT_SEP_PIXEL = 1

MAIN_TEXT_HEIGHT_WITH_SECOND_LINE = 0.184
MAIN_TEXT_SEP_WITH_SECOND_LINE = 0.00165
SUB_TEXT_HEIGHT_WITH_SECOND_LINE = 0.029

SECOND_LINE_TEXT_HEIGHT = 0.108
SECOND_LINE_TEXT_SEP = 0.0015

SECOND_LINE_TEXT_POSITION_Y = 0.924
SUB_LINE_TEXT_POSITION_SEP = 0.004

SUB_TEXT_SEP_MIDDLE = 0.0113

SECOND_LINE_FADE_SCALE = 0.3
SUB_TEXT_FADE_SCALE = 0.5
SUB_TEXT_FADE_MIN_ALPHA = 0.05

DYNAMIC_SPACING_MIN_RATIO = 0.002
DYNAMIC_SPACING_DECAY_RATE = 1

SHADOW_LONG_AXIS_RATIO = 1.2
SHADOW_SHORT_AXIS_RATIO = 1
SHADOW_EDGE_AREA_RATIO = 0.33
SHADOW_NOISE_RATE = 0.4
SHADOW_DEFAULT_OPACITY = 0.15
SHADOW_OFF = 0.2

COLOR = (255, 255, 255)

# ---------------------------- 辅助函数 ----------------------------
def is_chinese_char(ch: str) -> bool:
    return '\u4e00' <= ch <= '\u9fff'

def wb_generate(text):
    return wb(text)[0].upper()

# ---------------------------- 核心图层生成函数 ----------------------------
def create_text_layer_exact(
    text: str,
    font_size: int,
    spacing_px: float = 0,
    color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    font_path: Union[str, List[str]] = [FONT_MAIN_TEXT_PATH, FONT_MAIN_TEXT_ENG_PATH]
) -> Image.Image:
    # 请在此处粘贴您原有的完整实现
    # 为节省篇幅，此处为占位，实际使用时请替换为完整函数体
    pass

def create_subtitle_layer(
    paragraphs: List[str],
    font_size: int,
    color: Tuple[int, int, int, int] = COLOR,
    spacing_px: int = SUB_TEXT_SEP_PIXEL,
    font_path: str = FONT_SUB_TEXT_PATH,
) -> Image.Image:
    # 请在此处粘贴您原有的完整实现
    pass

def create_text_layer_exact(
    text: str,
    font_size: int,
    spacing_px: float = 0,
    color: Tuple[int, int, int, int] = (255, 255, 255, 255),
    font_path: Union[str, List[str]] = [FONT_MAIN_TEXT_PATH, FONT_MAIN_TEXT_ENG_PATH]
) -> Image.Image:
    """
    创建刚好容纳文字的透明图层。
    font_path: 字符串（单字体）或长度为2的列表 [中文字体路径, 英文字体路径]
    """
    # 加载字体对象（单字体或双字体）
    if isinstance(font_path, str):
        fonts = {'default': ImageFont.truetype(font_path, font_size)}
        use_mixed = False
    else:
        font_cn = ImageFont.truetype(font_path[0], font_size)
        font_en = ImageFont.truetype(font_path[1], font_size)
        fonts = {'cn': font_cn, 'en': font_en}
        use_mixed = True

    # 临时画布用于度量
    temp_img = Image.new('RGBA', (1, 1))
    draw = ImageDraw.Draw(temp_img)

    # 辅助函数：获取字符对应的字体
    def get_font(ch: str):
        if not use_mixed:
            return fonts['default']
        return fonts['cn'] if is_chinese_char(ch) else fonts['en']

    # 计算整体边界和每个字符的宽度
    total_width = 0.0
    min_top = float('inf')
    max_bottom = -float('inf')
    char_widths = []
    char_fonts = []

    for i, ch in enumerate(text):
        font = get_font(ch)
        char_fonts.append(font)
        bbox = draw.textbbox((0, 0), ch, font=font)
        ch_w = bbox[2] - bbox[0]
        char_widths.append(ch_w)
        total_width += ch_w
        if i < len(text) - 1:
            total_width += spacing_px
        # 更新垂直边界
        min_top = min(min_top, bbox[1])
        max_bottom = max(max_bottom, bbox[3])

    if not text:
        # 空字符串返回 1x1 透明图层
        return Image.new('RGBA', (1, 1), (0, 0, 0, 0))

    width = int(round(total_width))
    height = max_bottom - min_top
    offset_y = -min_top
    # 水平偏移：第一个字符的 left 可能为负
    first_char_font = get_font(text[0])
    first_bbox = draw.textbbox((0, 0), text[0], font=first_char_font)
    offset_x = -first_bbox[0]

    # 创建实际图层
    layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw_layer = ImageDraw.Draw(layer)

    # 逐字符绘制
    x = offset_x
    y = offset_y
    for i, ch in enumerate(text):
        font = char_fonts[i]
        bbox = draw.textbbox((0, 0), ch, font=font)
        ch_w = bbox[2] - bbox[0]
        # 绘制字符（坐标取整）
        draw_layer.text((int(round(x)), int(round(y))), ch, font=font, fill=color)
        x += ch_w + spacing_px

    return layer

# 副标题文字生成
def create_subtitle_layer(
    paragraphs: List[str],
    font_size: int,
    color: Tuple[int, int, int, int] = COLOR,
    spacing_px: int = SUB_TEXT_SEP_PIXEL,
    font_path: str = FONT_SUB_TEXT_PATH,           # 英文字体路径
) -> Image.Image:
    """针对纯大写英文的副标题图层生成（无中文字体切换）"""
    if not paragraphs:
        return Image.new('RGBA', (1, 1), (0, 0, 0, 0))

    font = ImageFont.truetype(font_path, font_size)
    temp_img = Image.new('RGBA', (1, 1))
    draw = ImageDraw.Draw(temp_img)

    block_images = []

    for para in paragraphs:
        first_line = para[:2]
        second_line = para[2:]   # 剩余字符（可能为空）
        if not second_line:
            # 只有一行
            width = 0.0
            for ch in first_line:
                bbox = draw.textbbox((0, 0), ch, font=font)
                width += bbox[2] - bbox[0]
            width = int(round(width))
            if first_line:
                bbox0 = draw.textbbox((0, 0), first_line[0], font=font)
                height = bbox0[3] - bbox0[1]
                offset_y = -bbox0[1]
            else:
                width, height, offset_y = 1, 1, 0
            layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw_layer = ImageDraw.Draw(layer)
            x = 0.0
            y = offset_y
            for ch in first_line:
                bbox = draw.textbbox((0, 0), ch, font=font)
                ch_w = bbox[2] - bbox[0]
                draw_layer.text((int(round(x)), int(round(y))), ch, font=font, fill=color)
                x += ch_w
            block_images.append((layer, width, height))
            continue

        # 有两行，强制重叠
        def get_line_metrics(line):
            total = 0.0
            tops = []
            bottoms = []
            for ch in line:
                bbox = draw.textbbox((0, 0), ch, font=font)
                total += bbox[2] - bbox[0]
                tops.append(bbox[1])
                bottoms.append(bbox[3])
            line_top = min(tops) if tops else 0
            line_bottom = max(bottoms) if bottoms else 0
            return total, line_top, line_bottom

        w1, t1, b1 = get_line_metrics(first_line)
        w2, t2, b2 = get_line_metrics(second_line)
        para_width = int(round(max(w1, w2)))
        para_height = int(round((b1 - t1) + (b2 - t2)))
        layer = Image.new('RGBA', (para_width, para_height), (0, 0, 0, 0))
        draw_layer = ImageDraw.Draw(layer)

        # 绘制第一行
        y1 = -t1
        x = 0.0
        for ch in first_line:
            bbox = draw.textbbox((0, 0), ch, font=font)
            ch_w = bbox[2] - bbox[0]
            draw_layer.text((int(round(x)), int(round(y1))), ch, font=font, fill=color)
            x += ch_w

        # 绘制第二行，紧贴第一行底部
        y2 = (b1 - t1) - t2
        x = 0.0
        for ch in second_line:
            bbox = draw.textbbox((0, 0), ch, font=font)
            ch_w = bbox[2] - bbox[0]
            draw_layer.text((int(round(x)), int(round(y2))), ch, font=font, fill=color)
            x += ch_w

        block_images.append((layer, para_width, para_height))

    # 水平排列
    total_width = sum(w for _, w, _ in block_images) + spacing_px * (len(block_images) - 1)
    max_height = max(h for _, _, h in block_images)
    subtitle_layer = Image.new('RGBA', (int(round(total_width)), max_height), (0, 0, 0, 0))
    x_offset = 0.0
    for img, w, h in block_images:
        y_offset = (max_height - h) // 2
        subtitle_layer.alpha_composite(img, (int(round(x_offset)), y_offset))
        x_offset += w + spacing_px

    return subtitle_layer

# Alpha通道渐变函数
def apply_vertical_alpha_gradient(
    layer: Image.Image,
    y_start: int,
    y_end: int,
    start_alpha: int,
    end_alpha: int,
    preserve_original_shape: bool = True
) -> Image.Image:
    """
    对图层的指定垂直范围应用 Alpha 渐变。
    :param layer: RGBA 模式的图像
    :param y_start: 渐变起始 Y 坐标（像素，包含）
    :param y_end: 渐变结束 Y 坐标（像素，包含）
    :param start_alpha: 起始 Alpha 值（0-255）
    :param end_alpha: 结束 Alpha 值（0-255）
    :param preserve_original_shape: 是否保持原有的抗锯齿/半透明边缘的形状（若 True，则新 alpha = 原alpha * 渐变因子；若 False，则直接覆盖 alpha）
    :return: 修改后的图层（直接修改原图并返回）
    """
    if layer.mode != 'RGBA':
        layer = layer.convert('RGBA')
    
    pixels = layer.load()
    width, height = layer.size
    
    # 确保 y 范围有效
    y_start = max(0, min(y_start, height-1))
    y_end = max(0, min(y_end, height-1))
    if y_start == y_end:
        return layer
    
    for y in range(y_start, y_end + 1):
        # 计算当前 y 的渐变因子 (0~1)
        t = (y - y_start) / (y_end - y_start)
        alpha_factor = start_alpha * (1 - t) + end_alpha * t
        # 遍历 x
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            if preserve_original_shape:
                # 新 alpha = 原 alpha * (目标渐变 alpha / 255) ，保持边缘半透明形状
                new_a = int(a * (alpha_factor / 255.0))
            else:
                new_a = int(alpha_factor)
            # 限制范围
            new_a = max(0, min(255, new_a))
            pixels[x, y] = (r, g, b, new_a)
    return layer

def main_text_generate(text: str, img: Image.Image, only_one_line: bool = True, spacing_px: int = MAIN_TEXT_SEP):
    width, height = img.size
    return create_text_layer_exact(text=text, font_size=int(round(height * MAIN_TEXT_HEIGHT)), spacing_px=spacing_px) if only_one_line else create_text_layer_exact(text=text, font_size=int(round(height * MAIN_TEXT_HEIGHT_WITH_SECOND_LINE)), spacing_px=spacing_px)

def second_line_text_generate(text: str, img: Image.Image):
    width, height = img.size
    ori_second_line_text_layer = create_text_layer_exact(text=text, font_size=int(round(height * SECOND_LINE_TEXT_HEIGHT)), spacing_px=int(round(width * SECOND_LINE_TEXT_SEP)))
    text_height = ori_second_line_text_layer.size[1]
    second_line_text_layer = apply_vertical_alpha_gradient(ori_second_line_text_layer, 0, int(round(SECOND_LINE_FADE_SCALE * text_height)), 0, 255)
    return second_line_text_layer

def sub_text_generate(text: str, img: Image.Image, only_one_line: bool = True):
    """
    为给定的文本生成五笔副标题图层（每个字符的五笔编码段落）
    """
    #去标点符号
    remove_chars = '[·’!"#$%&\'()＃！（）*+,-./:;<=>?@，：?￥★、…．＞【】［］《》？“”‘’[\\]^_`{|}~]+'
    text = re.sub(remove_chars, "", text)
    
    # 生成段落列表：每个字符转换为五笔98编码
    paragraphs = [wb_generate(ch) for ch in text]
    height = img.size[1]
    ori_sub_layer = create_subtitle_layer(paragraphs=paragraphs, font_size=int(round(height * SUB_TEXT_HEIGHT))) if only_one_line else create_subtitle_layer(paragraphs=paragraphs, font_size=int(round(height * SUB_TEXT_HEIGHT_WITH_SECOND_LINE)))
    text_height = ori_sub_layer.size[1]
    sub_layer = apply_vertical_alpha_gradient(ori_sub_layer, int(round(SUB_TEXT_FADE_SCALE * text_height)), text_height-1, 255, SUB_TEXT_FADE_MIN_ALPHA)
    return sub_layer

# 水平合并副标题函数
def combine_horizontal(images: List[Image.Image], spacing: int) -> Image.Image:
    """
    将多个 RGBA 图像水平排列，间距为 spacing 像素，返回合并后的图像。
    所有图像在垂直方向上居中对齐。
    """
    if not images:
        return Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    if len(images) == 1:
        return images[0]
    total_width = sum(img.width for img in images) + spacing * (len(images) - 1)
    max_height = max(img.height for img in images)
    combined = Image.new('RGBA', (total_width, max_height), (0, 0, 0, 0))
    x = 0
    for img in images:
        y = (max_height - img.height) // 2
        combined.alpha_composite(img, (x, y))
        x += img.width + spacing
    return combined

# 垂直居中函数
def composite_layers_centered(
    layers: List[Tuple[Image.Image, int, int]],
    canvas_size: Optional[Tuple[int, int]] = None,
    background: Optional[Image.Image] = None
) -> Image.Image:
    """
    将多个图层按各自偏移组合，并整体居中于画布。

    :param layers: 列表，每个元素为 (layer_image, offset_x, offset_y)
                   偏移量是相对于组合原点的坐标（可为负）。
    :param canvas_size: 最终画布尺寸 (width, height)。若为 None 且 background 也为 None，
                        则画布自动缩放到刚好容纳所有图层（无额外边距）。
    :param background: 可选的背景图片（RGBA模式），若提供则以此图为底，忽略 canvas_size。
    :return: 合成后的 RGBA 图像。
    """
    if not layers:
        return Image.new('RGBA', (1, 1), (0, 0, 0, 0))

    # 计算所有图层的整体边界（组合外框）
    min_x = min(off_x for _, off_x, _ in layers)
    max_x = max(off_x + layer.width for layer, off_x, _ in layers)
    min_y = min(off_y for _, _, off_y in layers)
    max_y = max(off_y + layer.height for layer, _, off_y in layers)

    comp_width = max_x - min_x
    comp_height = max_y - min_y

    # 确定最终画布
    if background is not None:
        final = background.convert('RGBA')
        canvas_width, canvas_height = final.size
    else:
        if canvas_size is None:
            canvas_width, canvas_height = comp_width, comp_height
        else:
            canvas_width, canvas_height = canvas_size
        final = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))

    # 计算组合居中于画布的起始点（相对于组合原点）
    start_x = (canvas_width - comp_width) // 2 - min_x
    start_y = (canvas_height - comp_height) // 2 - min_y

    # 合成每个图层
    for layer, off_x, off_y in layers:
        dest_x = start_x + off_x
        dest_y = start_y + off_y
        final.alpha_composite(layer, (dest_x, dest_y))

    return final

# 字间距调整函数
def calc_dynamic_spacing(base_spacing: float, char_count: int, 
                         min_ratio: float = DYNAMIC_SPACING_MIN_RATIO,
                         decay_rate: float = DYNAMIC_SPACING_DECAY_RATE) -> float:
    """
    根据字符数动态计算字间距比例。
    base_spacing: 基础字间距比例（字符数为1时的值）
    char_count: 主标题字符个数（>=1）
    min_ratio: 最小允许字间距比例
    decay_rate: 衰减速率（指数系数）
    """
    if char_count <= 1:
        return base_spacing
    # 指数衰减公式
    ratio = min_ratio + (base_spacing - min_ratio) * math.exp(-decay_rate * (char_count - 1))
    return max(min_ratio, ratio)  # 确保不低于最小比例

# 生成底影函数
def create_ellipse_shadow(comp_width: int, comp_height: int, opacity: float = SHADOW_DEFAULT_OPACITY) -> tuple:
    """
    根据文字组合的尺寸生成椭圆阴影图层。
    返回 (shadow_layer, offset_x, offset_y)，其中 offset_x, offset_y 为整数像素偏移。
    """
    # 椭圆参数
    long_axis = comp_width * SHADOW_LONG_AXIS_RATIO
    short_axis = comp_height * SHADOW_SHORT_AXIS_RATIO
    # 椭圆中心相对坐标（相对于组合矩形中心，再向下偏移 comp_height*SHADOW_OFF）
    center_x = comp_width / 2
    center_y = comp_height / 2 + comp_height * SHADOW_OFF

    # 椭圆外接矩形尺寸
    shadow_w = int(math.ceil(long_axis))
    shadow_h = int(math.ceil(short_axis))
    # 椭圆在图层中的绘制区域（居中）
    ellipse_bbox = [
        (shadow_w - long_axis) / 2, (shadow_h - short_axis) / 2,
        (shadow_w + long_axis) / 2, (shadow_h + short_axis) / 2
    ]

    # 创建透明图层
    shadow = Image.new('RGBA', (shadow_w, shadow_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)

    # 绘制黑色椭圆，整体不透明度 opacity
    base_alpha = int(255 * opacity)
    draw.ellipse(ellipse_bbox, fill=(0, 0, 0, base_alpha))

    # 添加噪点：40% 的像素变成浅灰色
    pixels = shadow.load()
    for x in range(shadow_w):
        for y in range(shadow_h):
            r, g, b, a = pixels[x, y]
            if a > 0 and random.random() < SHADOW_NOISE_RATE:
                gray = random.randint(128, 200)
                pixels[x, y] = (gray, gray, gray, a)

    # 羽化边缘：边缘宽度为短半轴的33%
    cx = shadow_w / 2
    cy = shadow_h / 2
    a_len = long_axis / 2
    b_len = short_axis / 2
    edge_width = min(a_len, b_len) * SHADOW_EDGE_AREA_RATIO

    for x in range(shadow_w):
        for y in range(shadow_h):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            dx = (x - cx) / a_len
            dy = (y - cy) / b_len
            dist = math.sqrt(dx*dx + dy*dy)
            if dist >= 1:
                pixels[x, y] = (0, 0, 0, 0)
            else:
                inner_dist = 1 - dist
                norm_edge = edge_width / min(a_len, b_len)
                if inner_dist < norm_edge:
                    factor = inner_dist / norm_edge
                    new_alpha = int(a * factor)
                    pixels[x, y] = (r, g, b, new_alpha)

    # 计算偏移并取整
    offset_x = int(round(center_x - shadow_w / 2))
    offset_y = int(round(center_y - shadow_h / 2))
    return shadow, offset_x, offset_y

# ---------------------------- 统一生成接口 ----------------------------
def generate_image(
    width: int,
    height: int,
    main_text: str,
    second_line: str = "",
    sub_text_enabled: bool = False,
    shadow_enabled: bool = False,
    shadow_opacity: float = 0.08,
    background_path: Optional[str] = None
) -> Image.Image:
    """
    根据参数生成最终图像，返回 PIL Image 对象。
    """
    # 加载背景
    if background_path and os.path.exists(background_path):
        bg = Image.open(background_path).convert('RGBA')
        canvas_width, canvas_height = bg.size
        bg_img = bg
    else:
        canvas_width, canvas_height = width, height
        bg_img = None

    # 动态字间距
    main_len = len(main_text)
    if second_line:
        base_sep = MAIN_TEXT_SEP_WITH_SECOND_LINE
    else:
        base_sep = MAIN_TEXT_SEP
    dynamic_sep_ratio = calc_dynamic_spacing(base_sep, main_len)
    spacing_px = max(1, int(round(canvas_width * dynamic_sep_ratio)))

    temp_canvas = Image.new('RGBA', (canvas_width, canvas_height), (0,0,0,0))

    layers = []

    # 主标题
    if second_line:
        main_layer = main_text_generate(main_text, temp_canvas, only_one_line=False, spacing_px=spacing_px)
    else:
        main_layer = main_text_generate(main_text, temp_canvas, only_one_line=True, spacing_px=spacing_px)
    layers.append((main_layer, 0, 0))

    # 第二行
    if second_line:
        second_layer = second_line_text_generate(second_line, temp_canvas)
        layers.append((second_layer, 0, 0))

    # 副标题
    if sub_text_enabled:
        main_sub_layer = sub_text_generate(main_text, temp_canvas, only_one_line=not second_line)
        sub_layers = [main_sub_layer]
        if second_line:
            second_sub_layer = sub_text_generate(second_line, temp_canvas, only_one_line=False)
            sub_layers.append(second_sub_layer)
        combined_sub_layer = combine_horizontal(sub_layers, spacing=int(round(canvas_width * SUB_TEXT_SEP_MIDDLE)))
        layers.append((combined_sub_layer, 0, 0))

    if not layers:
        return Image.new('RGBA', (canvas_width, canvas_height), (0,0,0,0))

    # 水平居中
    widths = [layer.width for layer, _, _ in layers]
    max_width = max(widths)
    centered_layers = []
    for layer, _, _ in layers:
        offset_x = (max_width - layer.width) // 2
        centered_layers.append((layer, offset_x, 0))
    layers = centered_layers

    # 垂直堆叠
    current_y = 0
    idx = 0
    # 主标题
    main_layer, main_off_x, _ = layers[idx]
    layers[idx] = (main_layer, main_off_x, current_y)
    current_y += main_layer.height
    idx += 1
    # 第二行
    if second_line:
        second_layer, second_off_x, _ = layers[idx]
        y_offset = int(round(main_layer.height * SECOND_LINE_TEXT_POSITION_Y))
        layers[idx] = (second_layer, second_off_x, y_offset)
        current_y = y_offset + second_layer.height
        idx += 1
    # 副标题
    if sub_text_enabled:
        combined_sub_layer, sub_off_x, _ = layers[idx]
        spacing = int(round(canvas_height * SUB_LINE_TEXT_POSITION_SEP))
        y_offset = current_y + spacing
        layers[idx] = (combined_sub_layer, sub_off_x, y_offset)

    # 翻转顺序（使主标题在最上层）
    layers.reverse()

    # 添加阴影
    if shadow_enabled:
        min_x = min(off_x for _, off_x, _ in layers)
        max_x = max(off_x + layer.width for layer, off_x, _ in layers)
        min_y = min(off_y for _, _, off_y in layers)
        max_y = max(off_y + layer.height for _, _, off_y in layers)
        comp_width = max_x - min_x
        comp_height = max_y - min_y
        shadow_layer, shadow_off_x, shadow_off_y = create_ellipse_shadow(comp_width, comp_height, shadow_opacity)
        layers.insert(0, (shadow_layer, shadow_off_x, shadow_off_y))

    final = composite_layers_centered(layers, canvas_size=(canvas_width, canvas_height), background=bg_img)
    return final