@echo off
REM start.bat - 启动泉策通智能体服务 (Windows)

echo ======================================
echo 启动泉策通智能体服务 v2.0
echo ======================================

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    pause
    exit /b 1
)

REM 检查依赖
echo 检查依赖...
pip install -q fastapi uvicorn python-dotenv httpx pydantic

REM 创建日志目录
if not exist logs mkdir logs

REM 启动服务
echo 启动服务（端口 8000）...
start /b python app.py > logs\app.log 2>&1

echo.
echo ✅ 服务启动成功！
echo    访问地址: http://127.0.0.1:8000
echo    健康检查: http://127.0.0.1:8000/health
echo    查询接口: POST http://127.0.0.1:8000/query
echo.
echo 查看日志: type logs\app.log
echo 停止服务: Ctrl+C 或关闭窗口
echo ======================================

REM 保持窗口打开
pause
