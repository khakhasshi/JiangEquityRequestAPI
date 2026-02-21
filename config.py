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
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
CORS_ALLOW_ORIGINS = [
	o.strip()
	for o in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
	if o.strip()
]
