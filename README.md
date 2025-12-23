# 泉策通智能体 v2.0

面向城市消费政策场景的 AI 咨询与决策支持服务。项目内置政策与企业知识库，通过大模型意图识别 + 关键词/向量混合检索 + 多工作流决策逻辑，为用户提供政策解析、个人福利测算、区域政策对比和企业投资信号灯等能力。

## 功能概览

- 统一入口服务：单一 FastAPI 服务，端口 **8000**，对外暴露 `POST /query`、`GET /health`。
- 大模型意图识别：基于通义千问，对自然语言查询解析为 4 类意图：
  - `policy_parse`：政策条款解析与结构化抽取
  - `personal_welfare`：个人福利额度测算
  - `regional_compare`：多地区政策条款对比
  - `investment_signal`：企业投资/招商信号灯
- RAG 检索引擎：对政策、企业知识库同时构建关键词 + 向量索引，支持按地区、行业等结构化过滤。
- 多工作流决策逻辑：按意图路由到对应工作流模块，输出结构化 JSON 结果以及自然语言解读。
- 扁平化输出：统一响应结构，便于前端或外部系统直接消费。

## 快速开始

### 1. 环境准备

1. 安装依赖（建议使用虚拟环境）：

   pip install -r requirements.txt

   或参考 `快速开始.md` 中的最小依赖安装命令：

   pip install fastapi uvicorn python-dotenv httpx pydantic requests

2. 配置 `.env`（大模型配置）：

   DASHSCOPE_API_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
   DASHSCOPE_API_KEY=你的_API_Key
   DASHSCOPE_CHAT_MODEL=qwen-plus
   DASHSCOPE_EMBED_MODEL=text-embedding-v3

### 2. 启动服务

在项目根目录执行：

- 直接启动：

  python app.py

- Windows 一键脚本：

  start.bat

服务启动后：

- 健康检查：`GET http://127.0.0.1:8000/health`
- 统一查询接口：`POST http://127.0.0.1:8000/query`
- 自动生成文档（Swagger）：`http://127.0.0.1:8000/docs`

### 3. 快速测试

使用内置测试脚本：

- 测试单个问题：

  python test_query.py "在济南买了3000元的空调能领多少补贴？"

- 运行基础服务测试：

  python test_service.py

更多示例问题见 `快速开始.md` 中的 4 种意图示例。

## 目录结构

项目关键目录与文件如下（省略部分中间层级）：

- `app.py`：统一入口服务，封装意图解析、工作流路由与最终回答生成。
- `workflows/`：核心业务工作流模块。
  - `intent_parser.py`：大模型意图识别与实体抽取。
  - `rag_retriever.py`：政策/企业知识库的 RAG 检索逻辑。
  - `policy_parser.py`：政策条款解析与结构化结果生成。
  - `welfare_calculator.py`：个人福利额度计算。
  - `regional_comparator.py`：区域政策对比与指标汇总。
  - `company_signal.py`：企业投资信号灯评分与推荐。
  - `llm_writer.py`：基于工作流结果生成自然语言回答。
- `data/`：数据与知识库目录。
  - `policies/`：各类政策原文、结构化文件与汇总。
  - `companies/`：分行业企业知识库及统计报表。
- `mcp_tools/`：MCP 工具相关封装（图表、高德地图、网页抓取等，可选）。
- `model_evaluate/`：模型测试与评估结果（离线分析用）。
- `start.bat`：Windows 一键启动脚本。
- `快速开始.md`：面向使用者的快速上手说明。
- `新架构说明.md`：v2.0 架构设计与与旧版对比说明。

## 统一接口说明

- `POST /query`
  - 入参：
    - `query`：用户自然语言问题，例如“在济南买了3000元的空调能领多少补贴？”
    - `user_context`（可选）：调用方传入的上下文信息。
  - 出参（简化）：
    - `success`: 是否成功
    - `intent`: 解析出的意图类型
    - `raw_text`: 原始查询文本
    - `entities`: 抽取出的实体（地区、产品、企业、时间等）
    - `result`: 对应工作流的结构化结果
    - `final_answer`: 面向用户的自然语言回答
    - `citations`: 使用到的政策/企业信息来源

- `GET /health`
  - 返回服务状态、名称与版本号。

## 工作流简介

1. **意图解析工作流**（`workflows/intent_parser.py`）  
   基于 LLM 对用户输入进行意图分类和实体抽取，输出统一字段，驱动下游工作流。

2. **政策解析工作流**（`workflows/policy_parser.py`）  
   调用 RAG 检索命中相关政策，将条款解析为结构化 JSON（补贴比例、封顶金额、申领条件等）。

3. **个人福利计算工作流**（`workflows/welfare_calculator.py`）  
   结合用户购买金额、产品类型与命中政策条款，计算可享受的补贴额度，并输出计算过程说明。

4. **区域政策对比工作流**（`workflows/regional_comparator.py`）  
   支持多地区并行检索与指标对比，生成“哪个地区政策更优”的结构化结论与可视化输入数据。

5. **企业投资信号灯工作流**（`workflows/company_signal.py`）  
   检索企业知识库，按创新能力、扩张意愿、渠道情况等维度打分，输出适合招商或重点关注的企业列表。

6. **LLM 润色生成器**（`workflows/llm_writer.py`）  
   将上述工作流的结构化结果与引用信息，转化为用户可以直接理解的自然语言回答。

## RAG 检索系统（概览）

- 政策知识库：
  - 使用 `policies.jsonl` 保存结构化政策记录，结合 Markdown 补充文档进行语义检索与引用解释。
  - 检索时先按地区/行业等字段过滤，再进行 Embedding + 关键词混合召回。
- 企业知识库：
  - 分行业 JSONL 文件存储企业基础信息与多维评分（创新、招聘意向、扩张意愿等）。
  - 支持按省市、行业过滤后进行相似度检索与排序。

详细设计可以参考根目录下的《RAG检索系统》、《泉策通开发文档.md》与《新架构说明.md》。

## 开发与调试

- 推荐从 `test_query.py` 入手，快速验证不同意图的端到端效果。
- 若需要扩展新意图或工作流，可：
  1) 在 `workflows/` 新增对应模块；
  2) 在 `intent_parser` 中增加意图枚举与解析逻辑；
  3) 在 `app.py` 的路由分发逻辑中接入新的工作流调用。
- MCP 图表、高德地图等增强能力，可按需使用 `mcp_tools/` 中的组件进行集成。

## 注意事项

- `.env` 中的 API Key 仅供本地开发使用，不应提交至版本控制或暴露给前端。
- 数据文件（尤其是政策与企业知识库）如有更新，需保证字段结构与现有工作流保持一致。
- 评估脚本与结果位于 `model_evaluate/` 目录，仅供离线分析使用，不影响在线服务。
