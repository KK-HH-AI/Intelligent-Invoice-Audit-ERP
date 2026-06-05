"""
文档智能分析模块
本模块提供文档解析、内容分析和与DeepSeek API交互的功能
支持格式：PDF、Word(.docx)、Excel(.xls,.xlsx)等
"""

import os
import re
import logging
import time
import tempfile

import fitz  # PyMuPDF
import cv2
import numpy as np
import stat
import requests
from PyPDF2 import PdfReader
from openai import OpenAI
from openai import APIError, APIConnectionError

import json  # 将json字符串转换为Python对象或字典

# 导入python-docx库并加载文档
from docx import Document
from dotenv import load_dotenv

# 处理excel
import pandas as pd

from backend.api.global_config import ocr_manager

# 加载环境变量（从项目根目录的.env文件）
load_dotenv()

# 从环境变量获取API配置信息
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')  # DeepSeek API密钥
DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL')  # API端点URL
DEEPSEEK_MODEL_NAME = os.getenv('DEEPSEEK_MODEL_NAME')  # 默认模型名称


def analyze_document(file):
    # 这里的file是一个文件对象
    """
    文档分析主函数：处理上传文件，提取内容并进行智能分析
    
    Args:
        file (FileStorage): 通过Web表单上传的文件对象（Flask/Werkzeug格式）
        
    Returns:
        analysis: 分析结果
            
    Raises:
        ValueError: 当API配置缺失时
        Exception: 处理过程中发生错误时
    """
    # 检查API配置是否完整
    if not DEEPSEEK_API_KEY or not DEEPSEEK_API_URL:
        raise ValueError("deepseek API配置缺失，请检查.env文件")

    # 使用项目内的temp目录而不是系统临时目录
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=os.path.splitext(file.filename)[1],
        dir=temp_dir  # 指定自定义目录（需确保目录已存在）
    )
    file.save(temp_file.name)
    temp_file.close()

    # 确保文件已关闭后再设置权限
    os.chmod(temp_file.name, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    try:
        # 步骤1：提取文件内容，file.filename 是上传文件的文件名，返回结果是字符串
        file_content = extract_file_content(temp_file.name, file.filename) # temp_file.name其实就是文件路径

        # 步骤2：调用DeepSeek API进行智能分析，返回python字典
        analysis_result = call_deepseek(file_content)

        return analysis_result

    except Exception as e:
        raise Exception(f"文档分析失败: {str(e)}")
    finally:
        # 确保清理临时文件
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


def extract_file_content(file_path, filename):
    """
    多格式文件内容提取器
    
    Args:
        file_path (str): 本地文件路径
        filename (str): 原始文件名（用于判断文件类型）
        
    Returns:
        str: 提取的文本内容
        
    Raises:
        ValueError: 遇到不支持的文件类型时
    """
    # 获取文件扩展名并统一转为小写
    file_ext = os.path.splitext(filename)[1].lower()

    # 根据文件类型选择对应的提取方法
    if file_ext == '.pdf':
        return extract_pdf_content(file_path)
    elif file_ext == '.docx':
        return extract_docx_content(file_path)
    # elif file_ext == '.doc':
    #     return extract_doc_content(file_path)
    elif file_ext in ['.xls', '.xlsx']:
        return extract_excel_content(file_path)
    # 暂时不支持对其它格式文件的处理
    else:
        raise ValueError(f"不支持的文件类型: {file_ext}")


# -------------------- PDF处理相关函数 --------------------
# def extract_pdf_content(file_path):
#     """
#     PDF内容提取器（支持文本型PDF和扫描版PDF）

#     处理流程：
#     1. 优先使用PyPDF2提取文本内容
#     2. 如果文本为空，使用OCR处理扫描版PDF
#     3. OCR处理使用PaddleOCR进行文字识别

#     Returns:
#         str: 提取的文本内容，失败时返回错误信息字符串
#     """
#     try:
#         # from PyPDF2 import PdfReader

#         # 尝试常规PDF文本提取
#         # with open(file_path, 'rb') as f:
#         #     reader = PdfReader(f)
#         #     text = "\n".join(page.extract_text() or '' for page in reader.pages)

#         # # 检测到扫描版PDF（文本为空）时启用OCR流程
#         # if not text.strip():

#         return _process_scanned_pdf(file_path)

#         # return text
#     except ImportError as e:
#         return f"[PDF处理需要安装依赖库: {str(e)}]"
#     except Exception as e:
#         return f"[PDF提取失败: {str(e)}]"

def extract_pdf_content(file_path):
    """
    PDF内容提取器（支持文本型PDF和扫描版PDF）

    处理流程：
        1. 优先使用PyPDF2提取文本内容
        2. 如果文本为空，使用OCR处理扫描版PDF
        3. OCR处理使用PaddleOCR进行文字识别

    Returns:
        str: 提取的文本内容，失败时返回错误信息字符串
    """
    try:
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
        # 逐页提取文本，并用换行符连接起来
        text = "\n".join(page.extract_text() or '' for page in reader.pages)

        # 检测到扫描版PDF（文本为空）时启用OCR流程
        if not text.strip():
            # 获取PDF页面对象
            doc = fitz.Document(file_path)
            full_text = []

            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    # 计算合适的缩放比例，确保图像清晰度
                    zoom = 2.0  # 基础缩放比例

                    # 根据页面大小动态调整缩放比例
                    if max(page.rect.width, page.rect.height) > 2000:
                        zoom = 1.5
                    elif max(page.rect.width, page.rect.height) < 1000:
                        zoom = 2.5

                    # 转换PDF页面为高质量图像，将PDF页面转换为RGB格式
                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(zoom, zoom),
                        alpha=False,
                        colorspace=fitz.csRGB  # 使用fitz.csRGB常量替代字符串"rgb"
                    )

                    # 转换为numpy数组
                    img_array = np.frombuffer(pix.samples, dtype=np.uint8)
                    img_array = img_array.reshape(pix.h, pix.w, pix.n)  # 重塑为三维数组，维度为(高度, 宽度, 通道数)

                    # 统一图像格式并增强对比度
                    if pix.n == 4:
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
                    elif pix.n == 1:
                        img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)

                    # 1. 转换为灰度图像(对文本识别更有效)
                    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

                    # 2. 自适应阈值处理，增强文本与背景对比度(对扫描文档特别有效)
                    binary = cv2.adaptiveThreshold(
                        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                        cv2.THRESH_BINARY, 11, 2
                    )

                    # 3. 降噪处理
                    denoised = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)

                    # 4. 锐化处理，增强文本边缘
                    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                    sharpened = cv2.filter2D(denoised, -1, kernel)

                    # 5. 根据图像质量选择最佳处理结果(计算原图与处理后图像的对比度)
                    orig_contrast = cv2.Laplacian(gray, cv2.CV_64F).var()
                    proc_contrast = cv2.Laplacian(sharpened, cv2.CV_64F).var()

                    # 如果处理后对比度显著提高，使用处理后的图像
                    if proc_contrast > orig_contrast * 1.2:
                        # 转回RGB用于OCR
                        img_array = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2RGB)
                    else:
                        # 否则使用原始图像的增强版本
                        img_array = cv2.convertScaleAbs(img_array, alpha=1.3, beta=10)
                        # 轻度锐化
                        img_array = cv2.filter2D(img_array, -1, kernel)

                    # 执行OCR并处理结果
                    ocr_result = process_image_ocr(img_array)

                    # 判断OCR结果是否为空
                    if ocr_result:
                        # OCR结果不为空，直接添加到full_text
                        full_text.append(str(ocr_result))
                    else:
                        # OCR结果为空，添加提示信息
                        full_text.append(f"[第{page_num + 1}页OCR结果为空]")
                except Exception as e:
                    logging.error(f"PDF页面{page_num + 1}处理失败: {str(e)}")
                    full_text.append(f"[第{page_num + 1}页处理失败: {str(e)}]")
                finally:
                    # 释放内存
                    if 'img_array' in locals():
                        del img_array
                    if 'pix' in locals():
                        del pix

            if not full_text:
                text = "[未能提取到有效文本]"
            else:
                text = "\n".join(full_text)  # 使用双换行分隔不同页面
            # 关闭PDF文档
            if doc:
                doc.close()
    except Exception as e:
        logging.error(f"PDF处理失败: {file_path}, 错误: {str(e)}")
        return f"[PDF处理失败: {str(e)}]"

    return text


# -------------------- Word文档处理 --------------------
# 这里要添加一个机制，就是我刚才使用一个markdown转word的在线工具导出的word会读取不到内容。
# 但是如果吧这个新建一个word文档，然后再将markdown内容复制粘贴进去，又可以正常读取了。
# 所以应该在读取内容失败后，也像处理pdf那样处理word文档的内容。
def extract_docx_content(file_path):
    """
    使用python-docx库提取.docx文件内容
    
    功能：
    - 解析.docx文档内容，包括段落文本和表格数据
    - 对标题段落进行特殊格式化处理

    Returns:
        str: 提取的文本内容，失败时返回错误信息字符串
    """
    try:
        doc = Document(file_path)  # 加载.docx文件

        text = []  # 存储提取的文本内容

        # 处理文档中的段落
        for para in doc.paragraphs:
            # 跳过空段落
            if para.text.strip():
                # 标题段落添加额外换行符以增强可读性
                if para.style.name.startswith('Heading'):
                    text.append(f"\n{para.text}\n")
                else:
                    text.append(para.text)

        # 处理文档中的表格
        for table in doc.tables:
            text.append("\n")  # 表格前添加空行

            # 表格有数据时才处理
            if table.rows:
                # 提取表头并格式化为Markdown
                header = [cell.text.strip() for cell in table.rows[0].cells]
                text.append("| " + " | ".join(header) + " |")

                # 添加Markdown表格分隔线
                text.append("| " + " | ".join(["---" for _ in header]) + " |")

                # 处理表格数据行
                for row in table.rows[1:]:
                    cells = [cell.text.strip() for cell in row.cells]
                    text.append("| " + " | ".join(cells) + " |")

            text.append("\n")  # 表格后添加空行

        # 合并所有文本并去除首尾空白
        return "\n".join(text).strip()

    except ImportError:
        # 处理python-docx库未安装的情况
        logging.error("python-docx库未安装")
        return "[请安装python-docx库]"

    except Exception as e:
        # 捕获并记录其他异常
        logging.exception(f"DOCX解析失败: {str(e)}")
        return f"[DOCX提取失败: {str(e)}]"


# -------------------- Excel文档处理 --------------------
def extract_excel_content(file_path):
    """
    提取Excel文件内容并保持表格排版
    
    支持格式：
    - .xlsx (Excel 2007+)
    - .xls (Excel 97-2003)
    
    Args:
        file_path (str): Excel文件的本地路径
        
    Returns:
        str: 提取的文本内容，转化为markdown格式表格
    """
    try:
        # 使用pandas读取Excel文件(自动处理.xls和.xlsx)
        excel_data = pd.ExcelFile(file_path)
        sheet_contents = []

        # 处理每个工作表
        for sheet_name in excel_data.sheet_names:
            df = pd.read_excel(excel_data, sheet_name=sheet_name)

            # 跳过空工作表
            if df.empty:
                continue

            # 添加工作表名称作为标题
            sheet_contents.append(f"\n## 工作表: {sheet_name}\n")

            # 直接添加Markdown格式的表格
            md_table = df.to_markdown(index=False)
            if md_table:
                sheet_contents.append(md_table)

            # 在工作表之间添加分隔符
            sheet_contents.append("\n" + "-" * 80 + "\n")

        # 关闭Excel文件
        excel_data.close()

        # 合并所有工作表内容
        if not sheet_contents:
            return "[Excel文件未包含有效数据]"

        return "\n".join(sheet_contents)

    except ImportError as e:
        # 处理pandas库未安装的情况
        logging.error(f"Excel处理需要pandas库: {str(e)}")
        return f"[Excel处理需要安装pandas库: {str(e)}]"

    except Exception as e:
        # 捕获并记录其他异常
        logging.exception(f"Excel解析失败: {str(e)}")
        return f"[Excel提取失败: {str(e)}]"


# def call_deepseek(content):
#     """
#     DeepSeek大模型API调用函数

#     参数:
#         content (str): 需要分析的文本内容（建议不超过4000字符）

#     返回:
#         dict: 包含原始响应、结构化数据和文本摘要的分析结果
#     """
#     if not content.strip():
#         raise ValueError("分析内容不能为空")
# HTTP请求头
# 后续的 API 请求准备好必要的身份认证和数据格式声明，确保你能安全、正确地与 DeepSeek API 通信。
#     headers = {
#         'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
#         'Content-Type': 'application/json'
#     }

#     # 构建结构化提示词（system prompt）
#     system_prompt = """你是一个专业发票审核单分析AI，请严格按以下步骤处理：
# 1. 提取关键字段并转化为结构化的json数据，保证数据的准确性和真实性，追求语言的真实性，不虚构不存在的内容。
# 2. 生成简洁摘要为summary字段添加在最后。
# 3. 保证提取到审核单中所有的关键信息并返回，若对应字段名无字段信息则返回字段名：无。
# 3. 输出格式：
#     1. 最终结果**必须**以严格的JSON对象格式返回。
#     2. **绝对不要**在JSON结果之外添加任何解释性文字、代码标记（如 ```json ... ```）、注释或其他非JSON内容。输出必须是纯粹的、可以直接解析的JSON。
# 必须返回纯JSON格式，不要任何额外文本，确保所有字段都有值（没有相关信息时使用空字符串或空数组）。"""

#     # 用户提示词（user prompt）
#     user_prompt = f"""请分析以下文本信息：
#     {content}"""

#     payload = {
#         'model': DEEPSEEK_MODEL_NAME,
#         'messages': [
#             {'role': 'system', 'content': system_prompt},
#             {'role': 'user', 'content': user_prompt}
#         ],
#         'temperature': 0.3,
#         'max_tokens': 2000,
#         'response_format': {'type': 'json_object'}  # 要求返回JSON格式
#     }

#     try:
#         # 直接调用API（保留700秒超时），response是http请求的响应对象
#         response = requests.post(
#             f"{DEEPSEEK_API_URL}/chat/completions",
#             headers=headers,
#             json=payload,
#             timeout=700
#         )
#         response.raise_for_status()  # 自动处理4xx/5xx错误

#         # 解析响应内容
#         result = response.json()
#         if not result.get('choices'):
#             raise ValueError("无效的API响应结构")

#         # 只返回content字段的内容，而不是整个响应对象，返回内容是json格式
#         content_str = result['choices'][0]['message']['content']

#         try:
#             # 1. 解析原始字符串为Python字典并返回
#             data = json.loads(content_str)

#             # 2. 重新序列化为紧凑格式
#             compact_json = json.dumps(
#                 data,
#                 ensure_ascii=False,
#                 indent=None,
#                 separators=(',', ':')
#             )

#             # return data
#             return compact_json

#         except Exception as e:
#             logging.error(f"JSON处理失败: {e}")

#     except requests.exceptions.RequestException as e:
#         raise Exception(f"API请求失败: {str(e)}")
#     except ValueError as ve:
#         raise Exception(f"响应解析错误: {str(ve)}")
#     except Exception as ex:
#         raise Exception(f"处理过程中发生意外错误: {str(ex)}")


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

    # 构建结构化提示词（system prompt）
    system_prompt = """你是一个专业发票审核单分析AI，请严格按以下步骤处理：
1. 提取审核单中与金额相关的关键字段，并提取这个金额字段相关的关键信息，最后转化为结构化的json数据，若对应字段名无字段信息则返回字段名：无。
2. 保证数据的准确性和真实性，追求语言的真实性，不虚构不存在的内容。
3. 生成简洁摘要为summary字段添加在最后。
4. 输出示例：（主要抓住金额字段的具体数目、数量，类别等属性）
"国际合作与交流费": {
    "预算": "60,000元",
    "国际合作列表": [
        {
            "活动类型": "国际会议",
            "金额": "30,000元",
            "备注": 利于发票审核的备注信息,
        },
        {
            "活动类型": "海外专家咨询",
            "金额": "20,000元",
            "备注": 利于发票审核的备注信息,
        },
        {
            "活动类型": "国际数据共享",
            "金额": "10,000元",
            "备注": 利于发票审核的备注信息,
        }
    ],
    "小计": "60,000元"
},
"劳务费": {
    "预算": "127,500元",
    "调整后": "127,500元",
    "人员列表": [
        {
            "人员类型": "博士研究生",
            "人数": "2",
            "月均津贴": "3,000元",
            "总金额": "216,000元"
        },
        {
            "人员类型": "科研助理（硕士）",
            "人数": "1",
            "月均津贴": "2,500元",
            "总金额": "60,000元"
        }
    ],
    "小计": "228,000元"
},
5. 输出格式：
    1. 最终结果必须以严格的JSON对象格式返回。
    2. 绝对不要在JSON结果之外添加任何解释性文字、代码标记（如 ```json ... ```）、注释或其他非JSON内容。输出必须是纯粹的、可以直接解析的JSON。
必须返回纯JSON格式，不要任何额外文本，确保所有字段都有值（没有相关信息时使用空字符串或空数组）。"""

    # 用户提示词（user prompt）
    user_prompt = f"""请分析以下文本信息：
    {content}"""

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_API_URL)

    print(f"正在发送请求到DeepSeek API...")  # 输出请求开始提示

    try:
        # 记录请求发送前的时间戳
        request_start_time = time.time()

        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            # stream=True, # stream=True ，返回的是生成器对象，不是直接的response对象，不能直接 .json()
            temperature=0.3,
            timeout=250,
            max_tokens=2500,
            response_format={'type': 'json_object'}  # 要求返回JSON格式
        )

        # 记录收到响应的时间戳，并计算耗时
        request_end_time = time.time()
        elapsed = request_end_time - request_start_time
        print(f"DeepSeek API响应耗时: {elapsed:.2f}秒")  # 输出API响应耗时

        # OpenAI SDK返回的是对象
        # 只返回content字段的内容，而不是整个响应对象，返回内容是json格式的字符串
        content_str = response.choices[0].message.content

        # 新增处理代码：使用正则表达式移除标记。主要是火山引擎返回的内容会有```json和```的标记
        content_str = re.sub(r'^\s*```json\s*', '', content_str, flags=re.IGNORECASE)  # 移除开头的```json
        content_str = re.sub(r'\s*```\s*$', '', content_str, flags=re.IGNORECASE)  # 移除结尾的```

        # print("模型原始返回：", content_str)
        return content_str

    except APIConnectionError as e:
        raise Exception(f"连接失败: {e}")
    except APIError as e:
        raise Exception(f"API错误: {e.status_code} - {e.message}")


def process_image_ocr(image_data):
    """
    处理图片OCR的主函数

    Args:
        image_data (numpy.ndarray): 图片数据(OpenCV格式)

    Returns:
        str: 识别后的文本内容，失败时返回错误信息字符串

    返回格式：
    [
        {
            "text": str,  # 识别出的文本内容
            "x": int,  # 左上角x坐标
            "y": int,  # 左上角y坐标
        },
        {
            "text": str,  # 识别出的文本内容
            "x": int,  # 左上角x坐标
            "y": int   # 左上角y坐标
            }
        }
    ]
    """
    try:
        # 确保OCR已初始化
        if ocr_manager.paddle_ocr is None:
            ocr_manager.initialize('ch', True)

        result = ocr_manager.paddle_ocr.ocr(image_data)

        # 处理结果并转换为JSON格式
        ocr_results = []
        for line in result[0]:
            text = line[1][0]
            position = line[0]

            # 转换坐标格式
            x_coords = [p[0] for p in position]
            y_coords = [p[1] for p in position]
            x_min, x_max = min(x_coords), max(x_coords)
            y_min, y_max = min(y_coords), max(y_coords)

            x_mid = (x_min + x_max) / 2
            y_mid = (y_min + y_max) / 2

            ocr_results.append({
                'text': text,
                'x': int(x_mid),
                'y': int(y_mid),
            })

        return ocr_results

    except Exception as e:
        return f"[图片OCR处理失败: {str(e)}]"
