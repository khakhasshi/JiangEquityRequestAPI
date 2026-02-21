import os
from dotenv import load_dotenv

load_dotenv()

# LongPort API 凭证（从 .env 或环境变量读取）
LONGPORT_APP_KEY = os.environ["LONGPORT_APP_KEY"]
LONGPORT_APP_SECRET = os.environ["LONGPORT_APP_SECRET"]
LONGPORT_ACCESS_TOKEN = os.environ["LONGPORT_ACCESS_TOKEN"]

# 服务配置
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8765"))
