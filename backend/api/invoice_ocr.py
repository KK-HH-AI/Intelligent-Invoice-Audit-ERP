"""
发票OCR识别处理模块
使用PaddleOCR实现本地化的发票字段息提取，返回结构化JSON数据
文本检测模型：ch_PP-OCRv3_rec_train.tar，
文本识别模型：ch_PP-OCRv4_det_server_infer.tar，
文本方向分类器模型：ch_ppocr_mobile_v2.0_cls_infer.tar
实现逻辑：先对图片做增强，然后再将图片使用ocr识别，最后提取识别结果中的字段，然后json格式
json格式示例
{
  "image_info": {
    "width": 800,
    "height": 600
  },
  [
    {
        "text": "发票金额",
        "x": 100,
        "y": 200,
    },
    {
        "text": "100.00",
        "x": 100,
        "y": 230,
    }
  ]
}
"""

import os
import re
import tempfile
import cv2
import numpy as np
import fitz
import json
import stat 
import logging
from dotenv import load_dotenv
from openai import OpenAI
from openai import APIError, APIConnectionError

# 使用OCRManager获取OCR实例
from backend.api.global_config import ocr_manager

# 加载环境变量（从项目根目录的.env文件）
load_dotenv()

# 从环境变量获取API配置信息
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')  # DeepSeek API密钥
DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL')  # API端点URL
DEEPSEEK_MODEL_NAME = os.getenv('DEEPSEEK_MODEL_NAME')  # 默认模型名称

base_dir = os.path.dirname(os.path.abspath(__file__))
need_path = os.path.join(base_dir, 'need.txt')
ignore_path = os.path.join(base_dir, 'ignore.txt')

# 初始化日志记录器
logger = logging.getLogger(__name__)


# TODO: 后续可以写一下发票处理的多线程

def process_invoice_images(files):
    """
    批量处理发票图片的主函数
    :param files: 文件列表
    """

    # 确保OCR已初始化
    if ocr_manager.paddle_ocr is None:
        ocr_manager.initialize('ch', True)

    # 检查API配置是否完整
    if not DEEPSEEK_API_KEY or not DEEPSEEK_API_URL:
        raise ValueError("deepseek API配置缺失，请检查.env文件")

    # 结果收集，all_results是一个列表，每个元素是一张发票的处理结果，类似数组的插入。
    all_results = {}

    # 遍历处理每张发票文件
    for file in files:
        temp_file = None
        try:
            # 使用项目内的temp目录而不是系统临时目录
            # temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
            # os.makedirs(temp_dir, exist_ok=True)

            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(file.filename)[1],
                # dir=temp_dir  # 指定自定义目录（需确保目录已存在）
            )
            file.save(temp_file.name)
            temp_file.close()

            # 确保文件已关闭后再设置权限
            # os.chmod(temp_file.name, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

            # 增加对PDF格式发票的支持
            file_ext = os.path.splitext(file.filename)[1].lower()
            if file_ext == '.pdf':
                try:
                    # 1. 使用 fitz (PyMuPDF) 打开 PDF
                    doc = fitz.Document(temp_file.name)

                    # 2. 遍历 PDF 的每一页
                    for page_num in range(len(doc)):
                        page = doc[page_num]

                        # 3. 计算缩放比例 (为了图像清晰度)
                        zoom = 2.0

                        # 根据页面大小动态调整缩放比例
                        if max(page.rect.width, page.rect.height) > 2000:
                            zoom = 1.5
                        elif max(page.rect.width, page.rect.height) < 1000:
                            zoom = 2.5

                        # 4. 将 PDF 页面渲染成图像 (pixmap)
                        pix = page.get_pixmap(
                            matrix=fitz.Matrix(zoom, zoom),
                            alpha=False,
                            colorspace=fitz.csRGB
                        )

                        # 5. 将图像数据转换为 OpenCV (NumPy) 格式
                        image = np.frombuffer(pix.samples, dtype=np.uint8)
                        image = image.reshape(pix.h, pix.w, pix.n)

                        # 6. 统一颜色通道为 RGB (PaddleOCR 通常需要 BGR 或 RGB)
                        if pix.n == 4:  # RGBA
                            image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
                        elif pix.n == 1:  # 灰度
                            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

                    doc.close()

                except Exception as e:
                    raise ValueError(f"处理PDF文件失败: {str(e)}")

            # 读取图像文件，支持图片格式 PNG (.png)，JPEG/JPG (.jpg, .jpeg)，BMP (.bmp)，TIFF (.tiff, .tif)，WebP (.webp)
            else:
                image = cv2.imread(temp_file.name)
                if image is None:
                    raise ValueError(f"无法读取图像文件: {file.filename}")

            # 图像预处理
            image = preprocess_image(image)

            # 获取图片尺寸信息
            height, width = image.shape[:2]
            image_info = {
                'width': width,
                'height': height
            }

            result = ocr_manager.paddle_ocr.ocr(image)

            # 处理结果并转换为JSON格式
            ocr_results = []
            for line in result[0]:
                # 1. 提取识别出的文本内容
                text = line[1][0]
                #    - `line` 是 PaddleOCR 返回的单个识别结果条目。
                #    - `line[1]` 通常包含一个元组 (tuple)，格式为 `(识别出的文本字符串, 置信度分数)`。
                #    - `line[1][0]` 获取这个元组的第一个元素，也就是实际识别出的文本字符串。
                #    例如：如果识别出 "发票代码"，那么 text 变量的值就是 "发票代码"。

                # 2. 提取文本框的位置坐标
                position = line[0]
                #    - `line[0]` 通常包含一个列表，表示检测到的文本框的四个顶点坐标。
                #    - 格式通常是 [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]，
                #      这四个点定义了包围文本的一个（可能倾斜的）四边形。
                #    例如：position 可能看起来像 [[100, 200], [300, 205], [298, 230], [98, 225]]

                # 3. 提取所有顶点的 x 坐标
                x_coords = [p[0] for p in position]
                #    - 这是一个列表推导式 (list comprehension)。
                #    - 它遍历 `position` 列表中的每个坐标点 `p` (例如 [100, 200])。
                #    - `p[0]` 提取每个点的第一个元素，即 x 坐标。
                #    - 最终 `x_coords` 会变成一个包含所有 x 坐标的列表。
                #    例如：基于上面的 position 例子，x_coords 会是 [100, 300, 298, 98]

                # 5. 提取所有顶点的 y 坐标
                y_coords = [p[1] for p in position]
                #    - 类似地，提取 `position` 中每个点 `p` 的第二个元素，即 y 坐标。
                #    例如：y_coords 会是 [200, 205, 230, 225]

                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)

                # 6.提取中间点坐标
                x_mid = (x_min + x_max) / 2
                y_mid = (y_min + y_max) / 2

                ocr_results.append({
                    'text': text,
                    'x': int(x_mid),  # 使用计算出的最小 x 坐标
                    'y': int(y_mid),  # 使用计算出的最小 y 坐标
                })

            invoice_ocr_input = {
                'image_info': image_info,
                'ocr_results': ocr_results
            }

            # 调用deepseek的api进行分析
            invoice_result = json.loads(call_deepseek(json.dumps(invoice_ocr_input, ensure_ascii=False)))

            all_results[f"{file.filename}"] = invoice_result

        except Exception as e:
            logger.error(f"处理文件 {file.filename} 时出错: {e}", exc_info=True)  # exc_info=True 会记录堆栈跟踪

            # 将错误信息添加到结果字典中，键为 "发票X_错误"
            all_results[f"{file.filename}_错误"] = {"error": f"处理文件 {file.filename} 失败: {str(e)}"}  # 可以包含文件名和错误信息

            continue

        finally:
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    # 将all_results的列字典式转换为JSON字符串。
    # 如果不加indent=2，就会去除掉换行和缩进，然后就会以\n显示，就会挤在一起。
    all_results_str = json.dumps(all_results, ensure_ascii=False, indent=2)
    # print(all_results_str)

    return all_results_str


# -------------------- DeepSeek API交互 --------------------
def call_deepseek(content):
    """
    DeepSeek大模型API调用函数
    
    参数:
        content (str): 需要分析的文本内容（建议不超过4000字符）
    
    返回:
        dict: 包含原始响应、结构化数据和文本摘要的分析结果
    """
    if not content.strip():
        raise ValueError("分析内容不能为空")

    # 读取需要提取的字段和忽略的字段 backend\api\need.txt
    with open(need_path, 'r', encoding='utf-8') as f:
        need_fields = f.read().strip()
    with open(ignore_path, 'r', encoding='utf-8') as f:
        ignore_fields = f.read().strip()  # 开头的任何空白行或结尾的任何空白行会被移除，但文件内容中间的换行符和空格会保持原样

    # 构建结构化提示词（system prompt）
    system_prompt = """你是一个专业的电子发票字段提取与结构化处理AI助手。
你的核心任务是根据用户提供的包含文本和坐标信息的OCR识别结果，精确地提取指定的关键字段，并忽略其他无关信息。
请严格遵循以下规则进行处理：
1.  角色定位: 你是发票信息提取专家，务必保证提取结果的准确性和完整性，追求语言的真实性，不虚构不存在的内容。
2.  输入理解: 
    1.输入是包含文本 (text) 及其位置 (x, y 坐标) 的OCR结果列表。你需要利用文本和坐标信息来定位字段及其对应的值，通常字段名和其值在空间上是邻近的。
3.  字段处理:
    1. 用户将在后续消息中提供需要提取的字段列表 (`need.txt`) 和需要忽略的字段列表 (`ignore.txt`)。
    2. 你必须提取 `need.txt` 中要求的所有字段。
    3. 你必须忽略 `ignore.txt` 中列出的所有字段。
4.  处理缺失值:
    1. 如果在OCR结果中无法找到 `need.txt` 中某个字段的对应值（或该字段本身在发票中不存在），请在该字段的值处填入字符串 "无"。
    2. 对于列表类型的字段（例如'购买货物及服务'），如果发票中没有相关的项目信息，请返回一个空列表 `[]`。
5.  输出格式:
    1. JSON对象应包含所有在 `need.txt` 中要求的字段作为键。
    2. 最终结果**必须**以严格的JSON对象格式返回。
    3. **绝对不要**在JSON结果之外添加任何解释性文字、代码标记（如 ```json ... ```）、注释或其他非JSON内容。输出必须是纯粹的、可以直接解析的JSON。
"""

    # 用户提示词（user prompt）
    user_prompt = f"""请根据系统定义的规则，处理以下OCR结果：
OCR数据: {content}
need.txt: {need_fields}
ignore.txt: {ignore_fields}
"""

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_URL)

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            # stream=True, # stream=True ，返回的是生成器对象，不是直接的response对象，不能直接 .json()
            temperature=0.3,
            timeout=150,
            max_tokens=1500,
            response_format={'type': 'json_object'}  # 要求返回JSON格式
        )

        # OpenAI SDK返回的是对象
        # 只返回content字段的内容，而不是整个响应对象，返回内容是json格式的字符串
        content_str = response.choices[0].message.content

        # 新增处理代码：使用正则表达式移除标记。主要是火山引擎返回的内容会有```json和```的标记
        content_str = re.sub(r'^\s*```json\s*', '', content_str, flags=re.IGNORECASE)  # 移除开头的```json
        content_str = re.sub(r'\s*```\s*$', '', content_str, flags=re.IGNORECASE)  # 移除结尾的```

        return content_str

    except APIConnectionError as e:
        raise Exception(f"连接失败: {e}")
    except APIError as e:
        raise Exception(f"API错误: {e.status_code} - {e.message}")


def preprocess_image(image, max_size=3000):
    """
    增强图像质量以提高OCR识别率
    
    参数：
    image: OpenCV格式的BGR图像(numpy数组)
    max_size: 图像的最大尺寸限制，防止内存溢出
    
    返回：
    处理后的增强图像
    """
    # 检查输入有效性
    if image is None or image.size == 0:
        raise ValueError("输入图像无效")

    try:
        # 1. 限制图像尺寸，避免内存溢出
        height, width = image.shape[:2]

        # 如果图像太大，进行缩放
        if max(height, width) > max_size:
            scale = max_size / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            logger.info(f"图像已缩小至 {new_width}x{new_height} 以避免内存溢出")

        # 2. 转换为灰度图像进行处理
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 3. 二值化处理 - 使用自适应阈值，增强文本与背景对比度
        # 对于发票这类文档，自适应阈值通常比全局阈值效果更好
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # 4. 降噪处理 - 去除小噪点
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        # 5. 边缘增强
        edges = cv2.Canny(opening, 50, 150)
        dilated_edges = cv2.dilate(edges, kernel, iterations=1)

        # 6. 将边缘叠加回原图像，增强文本轮廓
        enhanced_binary = cv2.addWeighted(binary, 0.8, dilated_edges, 0.2, 0)

        # 7. 转回彩色图像 (PaddleOCR需要彩色图像输入)
        enhanced_color = cv2.cvtColor(enhanced_binary, cv2.COLOR_GRAY2BGR)

        # 8. 对比度增强 - 使用CLAHE (对比度受限的自适应直方图均衡化)
        lab = cv2.cvtColor(enhanced_color, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)  # noqa: E741
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        merged = cv2.merge([cl, a, b])
        final_image = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

        # 9. 锐化处理 - 使用USM(Unsharp Masking)算法
        gaussian = cv2.GaussianBlur(final_image, (0, 0), 3)
        final_image = cv2.addWeighted(final_image, 1.5, gaussian, -0.5, 0)

        # 10. 确保图像尺寸适中 - 如果图像太小，适当放大
        height, width = final_image.shape[:2]
        min_dimension = 1000  # 最小尺寸

        if min(height, width) < min_dimension:
            scale = min_dimension / min(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            final_image = cv2.resize(final_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            logger.info(f"图像已放大至 {new_width}x{new_height} 以提高OCR识别率")

        return final_image

    except cv2.error as cv_err:
        logger.error(f"OpenCV处理图像时出错: {cv_err}")
        # 如果增强处理失败，尝试基本处理
        try:
            # 基本处理 - 只调整大小和简单锐化
            height, width = image.shape[:2]
            if max(height, width) > max_size:
                scale = max_size / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

            # 简单锐化
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(image, -1, kernel)

            return sharpened
        except Exception as e:
            logger.error(f"基本图像处理也失败: {e}")
            # 如果所有处理都失败，返回原始图像
            return image

    except Exception as e:
        logger.error(f"图像预处理失败: {e}")
        # 如果处理失败，返回原始图像
        return image
