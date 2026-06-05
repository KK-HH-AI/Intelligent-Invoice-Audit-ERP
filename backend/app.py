import os
import logging
import json
from flask_cors import CORS
from dotenv import load_dotenv
from api.global_config import ocr_manager
from api.invoice_ocr import process_invoice_images
from api.doc_analysis import analyze_document
from api.invoice_audit import invoice_audit
from flask import Flask, request, jsonify

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)

# 初始化OCR实例
ocr_manager.initialize()


# 发票OCR识别API - 支持批量上传，最多3张图片
@app.route('/api/ocr/invoice', methods=['POST'])
def ocr_invoice():
    if 'files' not in request.files:
        logger.warning("API调用缺少文件参数")
        return jsonify({'error': '没有上传文件'}), 400

    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        logger.warning("API调用上传了空文件名")
        return jsonify({'error': '没有选择文件'}), 400

    try:
        file_names = [file.filename for file in files]
        logger.info(f"开始处理发票图片: {', '.join(file_names)}")
        result = process_invoice_images(files)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        invoice_path = os.path.join(base_dir, 'invoice.json')
        with open(invoice_path, 'w', encoding='utf-8') as out_file:
            out_file.write(result)

        logger.info(f"处理发票图片成功: {', '.join(file_names)}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"OCR处理失败: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# 文档分析API
@app.route('/api/analyze/document', methods=['POST'])
def analyze_doc():
    if 'file' not in request.files:
        logger.warning("API调用缺少文件参数")
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning("API调用上传了空文件名")
        return jsonify({'error': '没有选择文件'}), 400

    try:
        logger.info(f"开始分析文档: {file.filename}")
        result = analyze_document(file)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, 'file.json')
        with open(file_path, 'w', encoding='utf-8') as out_file:
            out_file.write(result)

        logger.info(f"文档分析成功: {file.filename}")
        return jsonify(result)
    except ValueError as e:
        logger.error(f"配置错误: {str(e)}")
        return jsonify({'error': str(e), 'error_type': 'config_error'}), 500
    except Exception as e:
        logger.error(f"分析文档时发生错误: {str(e)}", exc_info=True)
        return jsonify({'error': f'处理失败: {str(e)}', 'error_type': 'unknown_error'}), 500


# 发票审核API
@app.route('/api/audit', methods=['POST'])
def audit():
    try:
        markdown_content = invoice_audit()
        return jsonify({
            "status": "success",
            "content": markdown_content
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)
