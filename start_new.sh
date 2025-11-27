#!/bin/bash
# start.sh - 启动泉策通智能体服务

echo "======================================"
echo "启动泉策通智能体服务 v2.0"
echo "======================================"

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: 未找到Python环境"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
pip install -q fastapi uvicorn python-dotenv httpx pydantic

# 创建日志目录
mkdir -p logs

# 启动服务
echo "启动服务（端口 8000）..."
nohup python app.py > logs/app.log 2>&1 &
echo $! > app.pid

echo ""
echo "✅ 服务启动成功！"
echo "   访问地址: http://127.0.0.1:8000"
echo "   健康检查: http://127.0.0.1:8000/health"
echo "   查询接口: POST http://127.0.0.1:8000/query"
echo ""
echo "查看日志: tail -f logs/app.log"
echo "停止服务: ./stop.sh"
echo "======================================"
