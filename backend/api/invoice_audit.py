import os
import requests
import logging
import time
import re
from dotenv import load_dotenv

load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def invoice_audit():
    """
    主函数：读取发票和审核单信息，调用DeepSeek API进行分析，并输出结果
    """
    # 加载.env文件中的环境变量，确保API密钥等敏感信息不直接硬编码在代码中
    load_dotenv()

    # 从环境变量获取DeepSeek API的配置信息
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')  # 获取API密钥
    DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL')  # 获取API基础URL
    DEEPSEEK_MODEL_NAME = os.getenv('DEEPSEEK_MODEL_NAME')  # 获取模型名称，默认为DeepSeek-V3

    # 构建文件路径：获取当前脚本所在目录，并拼接相关文件路径
    # base_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本的绝对路径的目录部分
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    invoice_path = os.path.join(base_dir, 'invoice.json')  # 发票信息文件路径
    file_path = os.path.join(base_dir, 'file.json')  # 审核单文件路径
    summary_path = os.path.join(base_dir, 'summary.md')  # 输出摘要文件路径

    try:
        # 读取发票信息文件内容
        with open(invoice_path, 'r', encoding='utf-8') as f1:
            invoice_content = re.sub(r'\s+', '', f1.read().strip())  # 读取并去除所有空白字符（包括换行符和缩进）

        # 读取审核单文件内容
        with open(file_path, 'r', encoding='utf-8') as f2:
            file_content = re.sub(r'\s+', '', f2.read().strip())  # 读取并去除所有空白字符（包括换行符和缩进）

        # 合并两个文件内容，添加标题标识
        merged_content = (
                "【发票信息】\n" + invoice_content +
                "\n【审核单】\n" + file_content
        )

        # print(merged_content)
    except Exception as e:
        # 如果读取文件失败，直接返回，终止程序
        logger.error(f"读取文件失败: {str(e)}")  # 注意：这里有拼写错误，应为logging
        return

    # 构造API请求头，包含认证信息和内容类型
    headers = {
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}',  # Bearer认证方式，使用API密钥
        'Content-Type': 'application/json'  # 指定请求内容类型为JSON
    }

    # 构建系统提示词，指导AI如何分析发票和审核单
    system_prompt = """你是一个专业发票审核分析师，追求发票审核的严谨性和正确性。请严格按以下步骤处理：
1. 识别要求：
    1. 识别发票信息相关的json格式内容，区分出多张发票的信息。
2. 审核要求：
    1. 对比审核单中的支出要求，对每张发票进行审核，判断对应分类的商品的支出金额、商品数量、商品单价、商品税额等信息有没有超出审核单的限制
    2. 对每张发票进行审核，判断是否存在重复项（重复项指发票信息完全一致的发票）
    3. 对每张发票进行审核，判断是否存在异常项，如商品名称、商品数量、商品单价、商品金额、商品税额等
3.输出要求：
    1. 输出格式：
        - 输出内容为markdown格式
    2. 输出审核结果
        一、发票总体情况
        二、发票审核结果（每张发票单独分析）
        三、重复项检查
        四、异常项检查
        五、审核结论与建议。
    3. 每张发票的审核结果示例：
        发票文件名称（发票号码）：
        - 审核结果（对发票中的支出条目分点回答）：
        - 异常项：XX。
        - 建议：XX。
    4. 以专业的发票审核师的角度给出详细的审核报告内容，结尾加上审核时间。
"""

    # 构建用户提示词，将合并后的内容作为分析对象
    user_prompt = f"""请分析以下内容：{merged_content}"""

    # 构建完整的API请求参数
    payload = {
        'model': DEEPSEEK_MODEL_NAME,  # 指定使用的模型
        'messages': [  # 消息数组，包含系统提示和用户提示
            {'role': 'system', 'content': system_prompt},  # 系统角色消息
            {'role': 'user', 'content': user_prompt}  # 用户角色消息
        ],
        'temperature': 0.3,  # 温度参数，控制输出的随机性，数字小创造性强，数字大确定性强
        'max_tokens': 3000,  # 最大生成令牌数，限制输出长度
        'stream': False  # 非流式响应，等待完整结果返回
    }

    print(f"正在发送请求到DeepSeek API...")  # 输出请求开始提示

    try:
        api_endpoint = DEEPSEEK_API_URL  # 获取API端点URL

        # 记录请求发送前的时间戳
        request_start_time = time.time()

        # 发送POST请求到DeepSeek API，设置500秒超时
        response = requests.post(
            f"{api_endpoint}/chat/completions",  # 完整的API端点URL
            headers=headers,  # 请求头
            json=payload,  # JSON格式的请求体
            timeout=200  # 请求超时时间（秒）
        )

        # 记录收到响应的时间戳，并计算耗时
        request_end_time = time.time()
        elapsed = request_end_time - request_start_time
        print(f"DeepSeek API响应耗时: {elapsed:.2f}秒")  # 输出API响应耗时

        response.raise_for_status()  # 自动处理4xx/5xx错误

        # 解析JSON响应内容
        result = response.json()

        # 验证响应结构是否符合预期
        if not result.get('choices'):
            raise ValueError("无效的API响应结构")  # 如果没有choices字段，抛出异常

        # 只返回content字段的内容，而不是整个响应对象
        content_str = result['choices'][0]['message']['content']

        # 输出生成的内容到控制台
        # print(content_str)

        # 将分析结果写入文件，如果要输出到前端，这部分可以注释掉。
        with open(summary_path, 'w', encoding='utf-8') as out_file:
            out_file.write(content_str)  # 将内容写入summary.md文件

        return content_str  # 返回生成的内容

    except requests.exceptions.RequestException as e:
        # 捕获并记录API请求过程中的异常
        logging.error(f"请求DeepSeek API失败: {str(e)}")


# 当脚本直接运行时（而非被导入时）执行main函数
if __name__ == "__main__":
    invoice_audit()
