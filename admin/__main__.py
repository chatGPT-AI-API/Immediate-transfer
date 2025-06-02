# admin/__main__.py
from flask import Flask
from .payment_gateway import PaymentGateway, PaymentMethod, PaymentStatus
import logging

__all__ = ['PaymentGateway', 'PaymentMethod', 'PaymentStatus', 'start_admin']

def start_admin():
    """启动 Admin 服务"""
    # 初始化日志
    logger = logging.getLogger("admin")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info("Starting Admin Service...")

    # 初始化 Flask 应用
    app = Flask(__name__)

    @app.route("/")
    def index():
        return "Admin Service is running!"

    # 启动服务
    app.run(debug=True, host="127.0.0.1", port=5001)



if __name__ == "__main__":
    start_admin()