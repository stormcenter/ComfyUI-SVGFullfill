import os
import base64
from PIL import Image
import numpy as np
from xml.etree import ElementTree as ET
import cairosvg
from io import BytesIO
import torch
import re

def tensor2pil(image):
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8))

class SVGUploader:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "svg_string": ("STRING", {"default": "", "multiline": False, "visible": False}),
        }}
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("svg_text",)
    OUTPUT_NODE = True
    FUNCTION = "upload_svg"
    CATEGORY = "SVGFullfill"

    # 添加节点尺寸定义
    @classmethod
    def IS_CHANGED(cls, *args, **kwargs):
        return float("NaN")  # 总是更新

    # 定义节点的默认大小
    SIZE = [200, 320]  # [宽度, 高度]

    def __init__(self):
        self._svg_content = None

    def upload_svg(self, svg_string):
        if not svg_string:
            return ("")
        return (svg_string,)

class SVGEditor:
    def __init__(self):
        self.font_dir = os.path.join(os.path.dirname(__file__), "font")
        if not os.path.exists(self.font_dir):
            os.makedirs(self.font_dir)
        # 获取字体目录下的所有字体文件
        self.fonts = [f for f in os.listdir(self.font_dir) if f.endswith(('.ttf', '.otf'))]
        if not self.fonts:
            print("警告：font 目录下没有找到字体文件(.ttf 或 .otf)")
            
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "svg_text": ("STRING", {"multiline": True}),
            },
            "optional": {
                "image1": ("IMAGE", {"default": None}),
                "image2": ("IMAGE", {"default": None}),
                "image3": ("IMAGE", {"default": None}),
                "text1": ("STRING", {"default": "", "multiline": True}),
                "text2": ("STRING", {"default": "", "multiline": True}),
                "text3": ("STRING", {"default": "", "multiline": True}),
                "text4": ("STRING", {"default": "", "multiline": True}),
                "text5": ("STRING", {"default": "", "multiline": True}),
                "text6": ("STRING", {"default": "", "multiline": True}),
                "text7": ("STRING", {"default": "", "multiline": True}),
                "text8": ("STRING", {"default": "", "multiline": True}),
                "text9": ("STRING", {"default": "", "multiline": True}),
                "text10": ("STRING", {"default": "", "multiline": True}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "edit_svg"
    CATEGORY = "SVGFullfill"

    def edit_svg(self, svg_text, image1=None, image2=None, image3=None, **kwargs):
        try:
            if not svg_text or len(svg_text.strip()) == 0:
                print("No SVG content received")
                blank_image = torch.zeros((1, 64, 64, 3))
                return (blank_image,)
            
            # 解析SVG获取尺寸
            parser = ET.XMLParser(encoding='utf-8')
            root = ET.fromstring(svg_text.encode('utf-8'), parser=parser)
            
            # 获取SVG的宽度和高度
            width = root.get('width')
            height = root.get('height')
            
            # 如果宽高使用百分比或其他单位，需要处理
            def parse_dimension(value):
                if value is None:
                    return 800  # 默认值
                # 移除单位（px、pt等）
                value = re.sub(r'[^0-9.]', '', value)
                try:
                    return int(float(value))
                except ValueError:
                    return 800  # 转换失败时的默认值
            
            output_width = parse_dimension(width)
            output_height = parse_dimension(height)
            
            # 获取viewBox属性
            viewbox = root.get('viewBox')
            if viewbox and not (width or height):
                # viewBox格式：min-x min-y width height
                try:
                    vb_parts = [float(x) for x in viewbox.split()]
                    if len(vb_parts) == 4:
                        output_width = int(vb_parts[2])
                        output_height = int(vb_parts[3])
                except ValueError:
                    pass
            
            # 使用XML解析器处理SVG
            parser = ET.XMLParser(encoding='utf-8')
            root = ET.fromstring(svg_text.encode('utf-8'), parser=parser)
            
            # 在处理文本之前，添加字体样式定义
            # 查找或创建 defs 元素
            defs = root.find('{http://www.w3.org/2000/svg}defs')
            if defs is None:
                defs = ET.SubElement(root, '{http://www.w3.org/2000/svg}defs')
            
            # 添加字体样式
            if self.fonts:
                font_path = os.path.join(self.font_dir, self.fonts[0])
                style = ET.SubElement(defs, '{http://www.w3.org/2000/svg}style')
                style.set('type', 'text/css')
                font_face = f"""
                    @font-face {{
                        font-family: 'CustomFont';
                        src: url('file://{font_path}');
                    }}
                """
                style.text = font_face
            
            # 处理文本替换时设置字体
            for i in range(1, 11):
                text_key = f"text{i}"
                if text_key in kwargs and kwargs[text_key]:
                    for text_elem in root.findall(f".//*[@id='{text_key}']"):
                        if text_elem is not None:
                            text_elem.text = kwargs[text_key].strip()
                            # 设置字体样式
                            text_elem.set('style', 'font-family: CustomFont;')
                            print(f"Updated text {i}: {kwargs[text_key]}")
            
            # 处理图片替换
            for i, img_batch in enumerate([image1, image2, image3], 1):
                if img_batch is not None and img_batch.shape[0] > 0:
                    print(f"Processing image {i}")
                    # 将tensor转换为PIL图像
                    img_tensor = img_batch[0]
                    img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
                    img = Image.fromarray(img_np)
                    
                    # 转换为PNG base64
                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    img_str = base64.b64encode(buffer.getvalue()).decode()
                    
                    # 修改查找方式，增加命名空间处理
                    for image_elem in root.findall(f".//*[@id='image{i}']"):
                        if image_elem is not None:
                            # 保持原有的宽度和高度属性
                            current_width = image_elem.get('width', '200')
                            current_height = image_elem.get('height', '200')
                            image_elem.set('width', current_width)
                            image_elem.set('height', current_height)
                            # 保持原有的位置属性
                            current_x = image_elem.get('x', str(50 + (i-1)*250))
                            current_y = image_elem.get('y', '180')
                            image_elem.set('x', current_x)
                            image_elem.set('y', current_y)
                            # 更新图片内容
                            image_elem.set('{http://www.w3.org/1999/xlink}href', f'data:image/png;base64,{img_str}')
            
            # 转换回字符串
            svg_content = ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
            
            # 使用cairosvg进行转换
            png_data = cairosvg.svg2png(
                bytestring=svg_content.encode('utf-8'),
                output_width=output_width,
                output_height=output_height,
                scale=1.0,
                background_color='white',
                unsafe=True,
                dpi=96
            )
            
            # 转换为PIL图像
            png_image = Image.open(BytesIO(png_data))
            png_image = png_image.convert('RGB')
            
            # 转换为tensor（值范围0-1）
            image_tensor = torch.from_numpy(np.array(png_image).astype(np.float32) / 255.0)
            image_tensor = image_tensor.unsqueeze(0)
            
            return (image_tensor,)
            
        except Exception as e:
            print(f"Error processing SVG: {str(e)}")
            import traceback
            traceback.print_exc()
            blank_image = torch.zeros((1, 64, 64, 3), dtype=torch.float32)
            return (blank_image,)

# Register nodes
NODE_CLASS_MAPPINGS = {
    "SVGUploader": SVGUploader,
    "SVGEditor": SVGEditor
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SVGUploader": "SVG Uploader",
    "SVGEditor": "SVG Editor"
}
