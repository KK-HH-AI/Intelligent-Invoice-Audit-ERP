# API模块初始化文件

# 导入文档分析相关功能
from .doc_analysis import (
    extract_file_content,
    extract_pdf_content,
    extract_docx_content,
    extract_excel_content,
    process_image_ocr,
)

# 初始化OCR相关功能
from .global_config import (
    check_paddle_dependencies,
    initialize_ocr,
)

# 导入发票OCR相关功能
from .invoice_ocr import (
    process_invoice_images,
    preprocess_image,
)

# 导入审计相关功能
from .invoice_audit import (
    invoice_audit,
)

# 版本信息
__version__ = '1.0.0'

# 模块说明
__all__ = [
    # 文档分析功能
    'extract_file_content',
    'extract_pdf_content',
    'extract_docx_content',
    'extract_excel_content',
    'process_image_ocr',

    # 初始化OCR功能
    'initialize_ocr',
    'check_paddle_dependencies',

    # 发票OCR功能
    'process_invoice_images',
    'preprocess_image',

    # 审计功能
    'invoice_audit',
]
