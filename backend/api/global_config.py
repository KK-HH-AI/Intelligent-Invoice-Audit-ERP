import os
import importlib
# import pkg_resources # 这个pkg_resources检查python包的方法已经过时了。
import importlib.metadata
from dotenv import load_dotenv
from paddleocr import PaddleOCR
import packaging
import logging

# PaddleOCR 类的工作机制是：
# 如果检测到本地模型路径有效 ➜ 直接加载本地模型
# 如果未指定或模型不存在 ➜ 自动下载官方模型

# 加载环境变量（从项目根目录的.env文件）
load_dotenv()

# 初始化日志记录器
logger = logging.getLogger(__name__)


# OCR管理器类，使用单例模式确保全局只有一个实例
class OCRManager:
    _instance = None

    # `__new__` 确保全局只有一个实例（单例模式），而`__init__` 负责初始化这个实例。
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OCRManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, lang='ch', use_angle_cls=True):
        if self._initialized:
            return

        self._initialized = True
        self.paddle_ocr = None
        self.initialize(lang, use_angle_cls)

    def initialize(self, lang='ch', use_angle_cls=True):
        """
        初始化PaddleOCR，使用指定的语言和参数。
        :param lang: 语言，默认为'ch'（中文）
        :param use_angle_cls: 是否使用文本方向分类器，默认为True
        """
        if self.paddle_ocr is None:
            model_dir = os.path.join(os.getenv('PADDLE_OCR_MODEL_DIR'))

            det_model = os.path.join(model_dir, os.getenv('PADDLE_OCR_DET_MODEL'))
            rec_model = os.path.join(model_dir, os.getenv('PADDLE_OCR_REC_MODEL'))
            cls_model = os.path.join(model_dir, os.getenv('PADDLE_OCR_CLS_MODEL'))

            ocr_params = {
                'use_angle_cls': use_angle_cls,
                'lang': lang,
                'use_gpu': False,
                'det_model_dir': det_model,
                'rec_model_dir': rec_model,
                'cls_model_dir': cls_model
            }

            try:
                self.paddle_ocr = PaddleOCR(**ocr_params)
                logger.info("PaddleOCR初始化成功")
            except Exception as e:
                logger.error(f"PaddleOCR初始化失败：{str(e)}")
                raise RuntimeError(f"PaddleOCR初始化失败：{str(e)}")

    def get_ocr(self):
        """
        获取PaddleOCR实例
        :return: PaddleOCR实例
        """
        return self.paddle_ocr


# 创建全局OCR管理器实例
ocr_manager = OCRManager()

# 为了向后兼容，保留paddle_ocr变量
paddle_ocr = ocr_manager.get_ocr()


############################################################################

# 这部分代码似乎都没有用上
def check_paddle_dependencies():
    """
    检查PaddleOCR所需依赖包的安装状态和版本
    """
    # 定义需要检查的依赖包及其要求版本
    dependencies = {
        'paddlepaddle': {'installed': False, 'version': None, 'required': '2.0.0'},  # paddlepaddle核心框架
        'paddleocr': {'installed': False, 'version': None, 'required': '2.0.0'},  # paddleocr OCR工具包
        'all_installed': False,  # 预先添加，标记是否所有依赖都已安装
        'all_requirements_met': False  # 预先添加，标记是否所有依赖都满足版本要求
    }

    # 检查paddlepaddle的安装状态
    try:
        # 获取paddlepaddle包的安装信息
        paddle_spec = importlib.metadata.version('paddlepaddle')
        # 导入paddle模块
        paddle_module = importlib.import_module('paddle')
        # 更新安装状态和版本信息
        dependencies['paddlepaddle']['installed'] = True
        dependencies['paddlepaddle']['version'] = paddle_spec.version
        # 获取构建信息，如果获取失败则使用'Unknown'
        dependencies['paddlepaddle']['build_info'] = getattr(paddle_module, '__version__', 'Unknown')
    except (importlib.metadata.PackageNotFoundError, ImportError):
        # 如果包未安装或导入失败，保持默认值
        pass

    # 检查paddleocr的安装状态
    try:
        # 获取paddleocr包的安装信息
        paddleocr_spec = importlib.metadata.version('paddleocr')
        # 更新安装状态和版本信息
        dependencies['paddleocr']['installed'] = True
        dependencies['paddleocr']['version'] = paddleocr_spec.version
    except importlib.metadata.PackageNotFoundError:
        # 如果包未安装，保持默认值
        pass

    # 检查每个包的版本是否满足要求
    for package, info in dependencies.items():
        if info['installed']:
            # 将版本号字符串转换为可比较的版本对象
            # importlib.metadata 不支持版本比较，它返回的结果是一个版本的字符串，它会按字典序比较，就不对了。
            installed_version = packaging.version.parse(info['version'])
            required_version = packaging.version.parse(info['required'])
            # 比较版本号，检查是否满足最低版本要求
            info['meets_requirement'] = installed_version >= required_version
        else:
            # 如果包未安装，则不满足要求
            info['meets_requirement'] = False

    # 检查是否所有依赖包都已安装
    dependencies['all_installed'] = all(dependencies[pkg]['installed'] for pkg in ['paddlepaddle', 'paddleocr'])
    # 检查是否所有依赖包都满足版本要求
    dependencies['all_requirements_met'] = all(
        dependencies[pkg]['meets_requirement'] for pkg in ['paddlepaddle', 'paddleocr'])

    # 返回依赖检查结果
    return dependencies


# 还可以加一个图像预处理的功能，提高图像质量：preprocess_enabled=True，具体功能要查文档
# 这个函数已经被封装到上面的共享类中了。
def initialize_ocr(lang='ch', use_angle_cls=True):
    """
    
    初始化PaddleOCR，使用指定的语言和参数。
    :param lang: 语言，默认为'ch'（中文）
    :param use_angle_cls: 是否使用文本方向分类器，默认为True

    """

    global paddle_ocr

    if paddle_ocr is None:
        model_dir = os.path.join(os.getenv('PADDLE_OCR_MODEL_DIR'))

        # 这里如果没有找到模型，似乎是会自动去网上下载
        det_model = os.path.join(model_dir, os.getenv('PADDLE_OCR_DET_MODEL', 'ch_PP-OCRv4_det_infer'))
        rec_model = os.path.join(model_dir, os.getenv('PADDLE_OCR_REC_MODEL', 'ch_PP-OCRv4_rec_infer'))
        cls_model = os.path.join(model_dir, os.getenv('PADDLE_OCR_CLS_MODEL', 'ch_ppocr_mobile_v2.0_cls_infer'))

        ocr_params = {
            'use_angle_cls': use_angle_cls,
            'lang': lang,
            'use_gpu': False,
            'det_model_dir': det_model,
            'rec_model_dir': rec_model,
            'cls_model_dir': cls_model
        }

        try:
            paddle_ocr = PaddleOCR(**ocr_params)
        except Exception as e:
            raise RuntimeError(f"PaddleOCR初始化失败：{str(e)}")
