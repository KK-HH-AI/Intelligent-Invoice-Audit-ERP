# 智能发票系统项目 README

## 项目简介

智能发票系统是一个基于人工智能技术开发的财务发票审核工具。我们是一支富有理想与创新能力的团队，虽编程经验尚浅，但致力于通过技术创新赋能审计行业，解决传统财务发票审核效率低、成本高、易疏漏等问题，实现票据核对的自动化与智能化。



## 项目背景

在数字经济快速发展的背景下，企业财务流程的智能化升级成为必然趋势。传统审计场景中，人工核对发票与采购单存在诸多痛点，如效率低下、容易出现疏漏、人力成本高、统计困难等。为了满足企业对提升财务效率、降低运营成本、增强数据准确性的需求，我们开发了这款智能发票系统。



## 项目功能

### 核心功能

  * **OCR 识别** ：利用 PaddleOCR 技术，对发票进行光学字符识别，无需使用特定发票或核对单格式，能够快速准确地提取发票信息。
  * **语义匹配** ：通过微调 Deepseek-R1 7b 大模型，实现发票信息与采购单信息的语义匹配，大幅提升票据语义匹配准确率，确保审核结果的准确性。
  * **可视化交互** ：采用 Html + JavaScript + Flask 框架开发，结合 MVC 架构和动态文件管理模块，实现前端页面与后端服务器之间的高效通信，为用户提供安全便捷的可视化交互界面。
  * **发票追踪看板** ：开发动态文件管理模块，引入 “发票追踪看板” 设计，实现上传文件的智能分类与异常定位，结合 Bootstrap 优化响应式界面，使错误排查效率翻倍提升。
  * **用户身份认证** ：集成 JWT 鉴权的账户系统，保障用户信息安全，确保只有授权用户才能访问系统。
  * **可视化日志追踪** ：通过可视化日志追踪功能，方便用户随时查看系统运行状态和操作记录，便于问题排查和系统维护。



### 优化功能

  * **发票识别数量优化** ：在指导老师的建议下，将原先的 3 张发票识别功能优化至 10 张发票识别审查，大大提高了用户的办公效率与实用性。
  * **识别结果展示优化** ：提出前端页面添加发票识别结果查看与文档识别结果查看的功能，加快用户在寻找错误发票的便捷度。将发票识别结果做成抽屉式展示，使网页更加简洁，便于用户的查阅使用。
  * **模型调用速率优化** ：通过调整 LoRA 参数，自建训练数据集，完成 deepseek-r1-7b 模型的定向微调，使调用速率从直接调用普通 API 的 30 分钟降低到原先的四分之一不到。
  * **OCR 冷启动优化** ：针对 OCR 框架冷启动延迟问题，创新设计 “预加载 + 动态调用” 双模块机制，将识别响应时间大大压缩。



## 技术架构

### 前端

  * **开发语言** ：html  + css + JavaScript
  * **框架** ：Bootstrap
  * **功能模块** ：发票识别结果查看、文档识别结果查看、发票追踪看板、登录页面等。

### 后端

  * **开发语言** ：Python 3.10
  * **框架** ：Flask
  * **功能模块** ：OCR 识别、语义匹配、动态文件管理、用户身份认证、日志追踪等。

### 数据库

  * **数据库类型** ：SQLite
  * **特点** ：轻量级、跨平台应用更加便捷，无需单独进程。



## 项目优势

  * **高效性** ：通过 OCR 识别和语义匹配技术，大幅提升发票审核效率，减少人工核对时间。
  * **准确性** ：微调的大模型能够精准匹配发票信息与采购单信息，降低审核错误率。
  * **易用性** ：简洁直观的可视化交互界面，易于上手操作，无需复杂培训。
  * **安全性** ：集成 JWT 鉴权的账户系统，保障用户信息安全，防止数据泄露。
  * **可扩展性** ：基于 Flask 框架和 MVC 架构开发，便于后期功能扩展和维护。



## 项目团队

本项目由一个四人学生团队开发，团队成员虽编程经验还比较生疏，但富有理想，具有创新能力。在项目开发过程中，团队成员分工明确，紧密协作，共同攻克了多项技术难题，成功完成了智能发票系统的开发。



## 使用说明

### 环境准备

确保使用 Python 3.10 版本。安装所需依赖：`pip install -r requirements.txt`。配置环境变量（创建 `.env` 文件）：

```
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com/v1
PADDLE_OCR_MODEL_DIR=./models
PADDLE_OCR_DET_MODEL=your_det_model_here
PADDLE_OCR_REC_MODEL=your_rec_model_here
PADDLE_OCR_CLS_MODEL=your_cls_model_here
```

### 作为独立服务运行

启动 Flask 服务：`python app.py`，服务将在 `http://localhost:7860 上运行，提供 Web 界面和 API 接口。



### 后端直接调用 API 模块

#### 发票 OCR 识别

```python
import os
from api.invoice_ocr import process_invoice_images

# 单张或多张发票处理
def process_invoices(image_paths):
    class MockFile:
        def __init__(self, file_path):
            self.filename = os.path.basename(file_path)
            self.path = file_path
            
        def save(self, dst_path):
            import shutil
            shutil.copy(self.path, dst_path)
    
    mock_files = [MockFile(path) for path in image_paths]
    result = process_invoice_images(mock_files)
    return result

# 使用示例 - 单张发票
invoice_result = process_invoices(["samples/电子发票.png"])
print(invoice_result)

# 使用示例 - 多张发票
multi_invoice_result = process_invoices(["samples/电子发票.png", "samples/电子发票2.png"])
print(multi_invoice_result)
```

#### 文档内容分析

```python
import os
from api.doc_analysis import analyze_document

# 分析文档
def analyze_doc_file(file_path):
    class MockFile:
        def __init__(self, file_path):
            self.filename = os.path.basename(file_path)
            self.path = file_path
            
        def save(self, dst_path):
            import shutil
            shutil.copy(self.path, dst_path)
    
    mock_file = MockFile(file_path)
    result = analyze_document(mock_file)
    return result

# 使用示例 - PDF 文档
doc_result = analyze_doc_file("samples/采购单.pdf")
print(doc_result)

# 使用示例 - Word 文档
docx_result = analyze_doc_file("samples/采购单.docx")
print(docx_result)

# 使用示例 - Excel 文档
excel_result = analyze_doc_file("samples/采购单.xlsx")
print(excel_result)
```



### 集成到现有 Flask 项目

复制 `api` 目录到你的项目中。在你的 Flask 应用中注册路由：

```python
from flask import Flask, request, jsonify
from api.invoice_ocr import process_invoice_image
from api.doc_analysis import analyze_document

app = Flask(__name__)

# 注册发票 OCR 路由
@app.route('/api/ocr/invoice', methods=['POST'])
def ocr_invoice():
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件', 'error_type': 'NO_FILE'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件', 'error_type': 'NO_FILENAME'}), 400
    
    try:
        result = process_invoice_image(file)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'error_type': 'PROCESSING_ERROR'}), 500

# 注册文档分析路由
@app.route('/api/analyze/document', methods=['POST'])
def analyze_doc():
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件', 'error_type': 'NO_FILE'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件', 'error_type': 'NO_FILENAME'}), 400
    
    try:
        result = analyze_document(file)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'error_type': 'PROCESSING_ERROR'}), 500

if __name__ == '__main__':
    app.run(debug=True)
```



### 前端调用 API

#### 使用 JavaScript Fetch API

```javascript
// 发票 OCR 识别示例 - 支持多文件上传
async function uploadInvoices(files) {
  const formData = new FormData();
  
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }
  
  try {
    const response = await fetch('/api/ocr/invoice', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || '上传失败');
    }
    
    console.log("发票识别结果:", result);
    
    const isMultiple = Array.isArray(result);
    
    if (isMultiple) {
      result.forEach((invoice, index) => {
        console.log(`发票 ${index + 1} 识别结果:`, invoice);
      });
    } else {
      console.log("单张发票识别结果:", result);
    }
    
    return result;
  } catch (error) {
    console.error('发票识别失败:', error);
    throw error;
  }
}

// 文档分析示例
async function analyzeDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch('/api/analyze/document', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.error || '分析失败');
    }
    
    console.log("文档分析结果:", result);
    return result;
  } catch (error) {
    console.error('文档分析失败:', error);
    throw error;
  }
}

// 文件上传事件处理示例
document.getElementById('invoice-upload').addEventListener('change', async (event) => {
  const files = event.target.files;
  if (files.length > 0) {
    try {
      const result = await uploadInvoices(files);
      console.log('处理完成的发票数据:', result);
    } catch (error) {
      console.error('发票处理失败:', error);
    }
  }
});

document.getElementById('document-upload').addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (file) {
    try {
      const result = await analyzeDocument(file);
      console.log('文档分析结果:', result);
    } catch (error) {
      console.error('文档分析失败:', error);
    }
  }
});
```



### API 返回数据格式

### 发票 OCR 识别 API

  * **URL** : `/api/ocr/invoice`
  * **方法** : POST
  * **参数** : 文件上传，字段名为 `files`（支持多文件上传，最多 3 个文件）
  * **返回** : JSON 格式的识别结果

#### 单张图片返回格式：

```json
{
  "image_info": {
    "width": 800,
    "height": 600
  },
  "ocr_results": [
    {
      "text": "发票金额",
      "x": 100,
      "y": 200
    },
    {
      "text": "100.00",
      "x": 100,
      "y": 230
    }
  ]
}
```

#### 多张图片或 PDF 文件返回格式：

```json
[
  {
    "image_info": {
      "width": 800,
      "height": 600,
    },
    "ocr_results": [
      {
        "text": "发票金额",
        "x": 100,
        "y": 200
      },
      {
        "text": "100.00",
        "x": 100,
        "y": 230
      }
    ]
  },
  {
    "image_info": {
      "width": 800,
      "height": 600,
    },
    "ocr_results": [
      {
        "text": "发票代码",
        "x": 150,
        "y": 180
      },
      {
        "text": "123456789",
        "x": 150,
        "y": 210
      }
    ]
  }
]
```



### AI智能处理后的返回结果

```json
{
  "电子发票.png": {
    "发票名称": "广东增值税电子普通发票",
    "发票号码": "15506870",
    "开票日期": "2023年07月26日",
    "购买方名称": "刘恩妍",
    "销售方名称": "东莞京东旭弘贸易有限公司",
    "销售方纳税人识别号": "91441900MA55D6UJ41",
    "销售方地址、电话": "广东省东莞市凤岗镇京东路1号19号楼212室22165500",
    "销售方开户行及账号": "中国银行股份有限公司东莞麻涌支行660073845512",
    "项目列表": [
      {
        "货物或应税劳务、服务名称": "电子计算机*机械革命（MECHREVO）极光Pro15.6英寸游戏本笔记本电脑(i7-12650H16G512G RTX4",
        "金额": "5574.34",
        "税率": "13%",
        "税额": "724.66"
      },
      {
        "货物或应税劳务、服务名称": "现代服务*退换无忧服务费",
        "金额": "0.44",
        "税率": "13%",
        "税额": "0.06"
      }
    ],
    "合计金额": "5574.78",
    "合计税额": "724.72",
    "价税合计(小写)": "6299.50"
  }
}
```



### 文档内容分析 API

  * **URL** : `/api/analyze/document`
  * **方法** : POST
  * **参数** : 文件上传，字段名为 `file`
  * **返回** : DeepSeek 分析后的结构化 JSON 数据

```json
{
    "项目名称": "基于域迁移的肿瘤信息排查",
    "项目金额": "100万元（人民币）",
    "执行周期": "202X年1月-202X年12月（3年）",
    "直接费用": {
    "总预算": "850,000元",
    "设备费": {
    "预算": "170,000元",
    "占比": "≤20%总经费",
    "设备列表": [
            {
            "设备名称": "高性能计算服务器",
            "型号/参数要求": "NVIDIA A100 GPU×4，内存256GB",
            "数量": "1台",
            "单价": "150,000元",
            "用途说明": "跨域肿瘤数据模型训练"
        },
        {
            "设备名称": "医学图像标注工作站",
            "型号/参数要求": "4K显示器，Intel i9处理器",
            "数量": "2台",
            "单价": "15,000/台",
            "用途说明": "肿瘤图像标注与预处理"
        },
        {
            "设备名称": "数据存储阵列",
            "型号/参数要求": "RAID 10，容量≥100TB",
            "数量": "1套",
            "单价": "50,000元",
            "用途说明": "多模态肿瘤数据存储与备份"
        }
     ],
        "小计": "230,000元",
        "调整后": "压缩设备费至总经费20%（200,000元），优化配置（例如减少1台工作站），确保符合规定。"
    },
        "材料费": {
        "预算": "120,000元",
        "材料列表": [
            {
                "材料类型": "公开肿瘤数据集",
                "来源/用途": "TCGA、BraTS数据集采购",
                "金额": "50,000元",
                "依据说明": "官网公开报价（约$5000）"
            },
            {
                "材料类型": "医院合作私有数据",
                "来源/用途": "与XX医院签署数据使用协议",
                "金额": "30,000元",
                "依据说明": "包含脱敏与标注服务费"
            },
            {
                "材料类型": "实验耗材",
                "来源/用途": "生物样本冷冻管、存储硬盘等",
                "金额": "40,000元",
                "依据说明": "按年均消耗量预估（3年）"
            }
    	],
        "小计": "120,000元"
    },
    "测试/分析费": {
        "预算": "110,000元",
    "测试列表": [
    {
        "测试内容": "病理样本验证",
        "合作单位/服务方": "XX医学检验中心（1000例样本）",
        "金额": "60,000元",
        "执行阶段": "第2年模型验证阶段"
    },
    {
        "测试内容": "云计算资源租赁",
        "合作单位/服务方": "阿里云GPU实例（2000小时）",
        "金额": "40,000元",
        "执行阶段": "第1-2年模型训练"
    },
    {
        "测试内容": "算法性能第三方评测",
        "合作单位/服务方": "国家超算中心",
        "金额": "10,000元",
        "执行阶段": "第3年结题前验收"
    }
    ],
        "小计": "110,000元"
    },
    "差旅/会议费": {
        "预算": "80,000元",
    "差旅列表": [
    {
        "类型": "国内学术会议",
        "具体内容": "中国医学影像AI大会（2人次）",
        "金额": "20,000元",
        "备注": "年均1次，含注册费与差旅"
    },
    {
        "类型": "跨机构协作差旅",
        "具体内容": "赴合作医院（北京/上海）",
        "金额": "40,000元",
        "备注": "年均4次，交通住宿补贴"
    },
    {
        "类型": "学术培训",
        "具体内容": "深度学习技术培训（3人次）",
        "金额": "20,000元",
        "备注": "第1年集中培训"
    }
    ],
        "小计": "80,000元"
    },
    "国际合作与交流费": {
    "预算": "60,000元",
    "国际合作列表": [
    {
        "活动类型": "国际会议",
        "合作方/会议名称": "MICCAI 202X（欧洲）",
        "金额": "30,000元",
        "目标": "发表论文1篇，算法展示"
    },
    {
        "活动类型": "海外专家咨询",
        "合作方/会议名称": "美国斯坦福大学Dr. Smith",
        "金额": "20,000元",
        "目标": "线上/线下联合算法优化"
    },
    {
        "活动类型": "国际数据共享",
        "合作方/会议名称": "英国癌症研究院数据访问",
        "金额": "10,000元",
        "目标": "支付数据使用许可费"
    }
    ],
        "小计": "60,000元"
    },
    "劳务费": {
        "预算": "127,500元",
        "占比": "≤15%直接费用",
    "人员列表": [
    {
        "人员类型": "博士研究生",
        "人数": "2",
        "月均津贴": "3,000元",
        "总时长": "36月",
        "总金额": "216,000元"
    },
    {
        "人员类型": "科研助理（硕士）",
        "人数": "1",
        "月均津贴": "2,500元",
        "总时长": "24月",
        "总金额": "60,000元"
    }
    ],
        "调整后": "总劳务费需≤15%×850,000=127,500元，按比例压缩至2名博士生（月均2,500元）与1名科研助理（2,000元）。",
        "小计": "228,000元 → 压缩至127,500元"
    },
    "专家咨询费": {
        "预算": "40,000元",
        "专家列表": [
        {
            "专家类型": "临床医学专家",
            "频次": "4次/年",
            "金额": "24,000元",
            "任务": "数据标注标准制定"
        },
        {
            "专家类型": "人工智能领域顾问",
            "频次": "2次/年",
            "金额": "16,000元",
            "任务": "模型架构设计评审"
        }
        ],
            "小计": "40,000元"
        }
    },
    "间接费用": {
        "总预算": "150,000元",
        "占比": "总经费15%",
        "管理费": "100,000元",
        "绩效支出": "50,000元"
    },
    "年度资金执行计划": {
    "科目": [
        {
            "科目名称": "设备费",
            "第1年": "150,000元",
            "第2年": "40,000元",
            "第3年": "10,000元",
            "合计": "200,000元"
        },
        {
            "科目名称": "材料费",
            "第1年": "50,000元",
            "第2年": "40,000元",
            "第3年": "30,000元",
            "合计": "120,000元"
        },
        {
            "科目名称": "测试费",
            "第1年": "30,000元",
            "第2年": "60,000元",
            "第3年": "20,000元",
            "合计": "110,000元"
        },
        {
            "科目名称": "差旅费",
            "第1年": "30,000元",
            "第2年": "30,000元",
            "第3年": "20,000元",
            "合计": "80,000元"
        },
        {
            "科目名称": "国际合作",
            "第1年": "20,000元",
            "第2年": "30,000元",
            "第3年": "10,000元",
            "合计": "60,000元"
        },
        {
            "科目名称": "劳务费",
            "第1年": "40,000元",
            "第2年": "50,000元",
            "第3年": "37,500元",
            "合计": "127,500元"
        },
        {
            "科目名称": "专家费",
            "第1年": "10,000元",
            "第2年": "20,000元",
            "第3年": "10,000元",
            "合计": "40,000元"
        },
        {
            "科目名称": "间接费用",
            "第1年": "50,000元",
            "第2年": "50,000元",
            "第3年": "50,000元",
            "合计": "150,000元"
        },
        {
            "科目名称": "总计",
            "第1年": "380,000元",
            "第2年": "320,000元",
            "第3年": "197,500元",
            "合计": "1,000,000元"
            }
        ]
    },
    "关键预算依据": [
        "设备采购：服务器选型参考《医疗AI硬件配置白皮书》（2023），满足大规模迁移学习需求。",
        "数据合规性：医院数据合作协议明确伦理审批与隐私保护条款（附件：XX医院合作备忘录）。",
        "国际合作必要性：斯坦福团队在Nature子刊发表相关论文3篇，提供算法理论支持（附件：合作意向书）。",
        "劳务费标准：参照《国家自然科学基金劳务费管理办法》（2022版）硕士生≤3,000元/月。"
    ],
    "风险控制与调整机制": [
        "设备采购风险：若供应商延迟交货，启用云平台临时算力租赁（预留10,000元备用金）。",
        "数据获取风险：若合作医院数据延迟，优先使用公开数据集（TCGA占比提升至70%）。",
        "预算动态调整：每年末根据进展重新分配≤10%的科目经费，报基金委备案。"
    ],
    "附件": [
        "设备报价单（3家供应商比价）",
        "医院数据使用协议（脱敏条款页）",
        "国际合作单位支持函"
    ],
    "备注": "红色标记部分需根据依托单位财务要求校对，建议与科研处逐项核对合规性。",
    "summary": "本项目为基于域迁移的肿瘤信息排查，总预算100万元，执行周期3年。直接费用850,000元，包括设备费、材料费、测试费、差旅费、国际合作费、劳务费和专家咨询费。间接费用150,000元，用于管理费和绩效支出。年度资金执行计划详细列出了各科目的年度预算和总预算。关键预算依据包括设备采购、数据合规性、国际合作必要性和劳务费标准。风险控制措施包括设备采购风险、数据获取风险和预算动态调整机制。"
}
```

## 注意事项

    1. 对于大型文档，分析可能需要较长时间。
    2. 确保使用 Python 3.10 版本运行项目。
    3. 对于发票 OCR，建议使用清晰的图片以获得更准确的识别结果。



## 项目演示

  * **登录页面** ：用户通过用户名和密码登录系统。
  * **发票上传与识别** ：用户上传发票图片后，系统自动调用 OCR 识别技术提取发票信息，并通过语义匹配技术与采购单信息进行匹配审核。
  * **发票追踪看板** ：系统自动对上传的发票文件进行智能分类与异常定位，方便用户快速查找和处理异常发票。
  * **识别结果查看** ：用户可以在前端页面查看发票识别结果和文档识别结果，识别结果采用抽屉式展示，简洁明了。
  * **日志追踪** ：系统提供可视化日志追踪功能，用户可以随时查看系统运行状态和操作记录，便于问题排查和系统维护。



## 项目维护

### 代码维护

  * **代码规范** ：遵循 PEP 8 编程规范，确保代码的可读性和一致性。
  * **代码审查** ：团队成员定期进行代码审查，及时发现和修复潜在问题。

### 数据库维护

  * **数据备份** ：定期备份数据库，防止数据丢失。
  * **数据优化** ：根据系统运行情况，定期对数据库进行优化，提升查询性能。

### 系统维护

  * **性能监控** ：定期监控系统性能，及时发现和解决性能瓶颈。
  * **安全检查** ：定期进行安全检查，修复系统漏洞，确保系统安全稳定运行。



## 项目展望

未来，我们将继续优化智能发票系统，进一步提升系统的性能和功能。具体计划如下：

  * **功能扩展** ：增加更多类型的发票识别和审核功能，满足不同用户的需求。
  * **性能优化** ：持续优化 OCR 识别和语义匹配算法，提升系统运行效率。
  * **用户体验提升** ：优化前端界面设计，提升用户体验。
  * **多语言支持** ：增加多语言支持，满足国际化用户的需求。
  * **与其他系统集成** ：探索将智能发票系统与其他财务系统或企业资源规划（ERP）系统集成，实现更高效的财务流程自动化。



## 联系方式

如果您在使用过程中遇到任何问题或有任何建议，欢迎随时与我们联系：

  * **邮箱** ：2981770180@qq.com