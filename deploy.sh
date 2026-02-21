#!/usr/bin/env bash
# ===========================================================
# JiangEquityRequestAPI 后端 Ubuntu 一键部署脚本
# 用法: scp -r PythonBackend/ ubuntu@<IP>:~/JiangEquityRequestAPI/
#        ssh ubuntu@<IP> "cd ~/JiangEquityRequestAPI && bash deploy.sh"
# ===========================================================
set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="jiang-equity-request-api"
PYTHON_MIN="3.11"

echo "=== JiangEquityRequestAPI Backend Deploy ==="
echo "Install dir: $INSTALL_DIR"

# 1. 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "[install] Installing Python3..."
    sudo apt-get update -qq
    sudo apt-get install -y python3 python3-venv python3-pip
fi
PYTHON=$(command -v python3)
echo "[ok] Python: $($PYTHON --version)"

# 2. 建 venv + 安装依赖
if [ ! -d "$INSTALL_DIR/.venv" ]; then
    echo "[venv] Creating virtual environment..."
    $PYTHON -m venv "$INSTALL_DIR/.venv"
fi
echo "[pip] Installing requirements..."
"$INSTALL_DIR/.venv/bin/pip" install -q --upgrade pip
"$INSTALL_DIR/.venv/bin/pip" install -q -r "$INSTALL_DIR/requirements.txt"
echo "[ok] Dependencies installed"

# 3. 确保 .env 存在
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo ""
    if [ -f "$INSTALL_DIR/.env.example" ]; then
        cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
        echo "⚠️  .env not found. 已从 .env.example 创建模板。"
    else
        cat > "$INSTALL_DIR/.env" <<'EOF'
# LongPort API 凭证（必填）
LONGPORT_APP_KEY=YOUR_APP_KEY
LONGPORT_APP_SECRET=YOUR_APP_SECRET
LONGPORT_ACCESS_TOKEN=YOUR_ACCESS_TOKEN

# 服务配置（可选）
SERVER_HOST=0.0.0.0
SERVER_PORT=8765
PUBLIC_BASE_URL=http://localhost:8765
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
        echo "⚠️  .env not found. 已创建模板。"
    fi
    echo "   请编辑 $INSTALL_DIR/.env 后重新运行此脚本"
    exit 1
fi

# 4. 安装 systemd 服务
PYTHON_BIN="$INSTALL_DIR/.venv/bin/python"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "[systemd] Installing service..."
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=JiangEquityRequestAPI Backend
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$PYTHON_BIN $INSTALL_DIR/main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable  "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

sleep 2
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo ""
    echo "✅ 部署成功！服务运行中"
    echo "   状态: sudo systemctl status $SERVICE_NAME"
    echo "   日志: sudo journalctl -u $SERVICE_NAME -f"
    echo ""
    # 开放防火墙端口（如果安装了 ufw）
    if command -v ufw &>/dev/null; then
        sudo ufw allow 8765/tcp 2>/dev/null && echo "   UFW: 8765/tcp 已放行"
    fi
else
    echo "❌ 服务启动失败，查看日志："
    sudo journalctl -u "$SERVICE_NAME" -n 30 --no-pager
    exit 1
fi
