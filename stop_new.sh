#!/bin/bash
# stop.sh - 停止泉策通智能体服务

echo "======================================"
echo "停止泉策通智能体服务"
echo "======================================"

if [ -f "app.pid" ]; then
    PID=$(cat app.pid)
    if ps -p $PID > /dev/null; then
        echo "停止服务 (PID: $PID)..."
        kill -15 $PID
        sleep 2
        if ps -p $PID > /dev/null; then
            echo "强制停止..."
            kill -9 $PID
        fi
        rm app.pid
        echo "✅ 服务已停止"
    else
        echo "⚠️  服务未运行 (PID: $PID 不存在)"
        rm app.pid
    fi
else
    echo "⚠️  未找到 app.pid 文件"
    echo "尝试查找并停止 python app.py 进程..."
    pkill -f "python app.py"
    if [ $? -eq 0 ]; then
        echo "✅ 服务已停止"
    else
        echo "未找到运行中的服务"
    fi
fi

echo "======================================"
