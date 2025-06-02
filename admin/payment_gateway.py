import uuid
import time
import requests
import qrcode
import io
import base64
import logging
from typing import Dict, Optional
from enum import Enum

# 初始化日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class PaymentMethod(Enum):
    QR_CODE = "qr_code"
    DIRECT = "direct"
    WECHAT = "wechat"
    ALIPAY = "alipay"

class PaymentStatus(Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentGateway:
    def __init__(self, config: Dict):
        """
        初始化支付网关
        :param config: 支付网关配置
        """
        self.config = config
        self.api_secret = config.get("api_secret", "your-secret-key")
        self.mock_mode = config.get("mock_mode", True)
        self.payment_methods = {
            PaymentMethod.QR_CODE: self._process_qr_payment,
            PaymentMethod.DIRECT: self._process_direct_payment,
            PaymentMethod.WECHAT: self._process_wechat_payment,
            PaymentMethod.ALIPAY: self._process_alipay_payment
        }

    def process_payment(self, order_id: str, amount: float,
                       method: PaymentMethod, **kwargs) -> Dict:
        """
        统一支付处理接口
        :param order_id: 订单ID
        :param amount: 支付金额
        :param method: 支付方式
        :return: 支付结果
        """
        logger.info(f"开始处理支付: 订单ID={order_id}, 金额={amount}, 方式={method}")
        
        if method not in self.payment_methods:
            error_msg = f"不支持的支付方式: {method}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            processor = self.payment_methods[method]
            result = processor(order_id, amount, **kwargs)
            logger.info(f"支付处理成功: 订单ID={order_id}, 结果={result}")
            return result
        except Exception as e:
            logger.error(f"支付处理失败: 订单ID={order_id}, 错误={str(e)}")
            raise

    def _process_qr_payment(self, order_id: str, amount: float) -> Dict:
        """处理二维码支付"""
        qr_data = self.generate_qr_code(order_id, amount)
        return {
            "code": 200,
            "payment_method": PaymentMethod.QR_CODE.value,
            "data": qr_data
        }

    def _process_direct_payment(self, order_id: str, amount: float) -> Dict:
        """处理直接支付"""
        if self.mock_mode:
            is_success = True if time.time() % 20 != 0 else False
            return {
                "order_id": order_id,
                "status": PaymentStatus.PAID.value if is_success else PaymentStatus.FAILED.value,
                "transaction_id": f"txn_{str(uuid.uuid4())[:8]}",
                "timestamp": time.time()
            }
        else:
            # TODO: 实现真实支付接口
            raise NotImplementedError("真实支付功能暂未实现")

    def generate_qr_code(self, order_id: str, amount: float) -> Dict:
        """生成支付二维码"""
        payment_url = f"{self.config.get('gateway_url', '')}/pay?order_id={order_id}&amount={amount}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "qr_code": f"data:image/png;base64,{img_str}",
            "payment_url": payment_url,
            "order_id": order_id,
            "amount": amount
        }

    def verify_callback(self, params: Dict) -> bool:
        """验证支付回调签名"""
        signature = params.get("signature")
        is_valid = signature == self.api_secret
        if is_valid:
            logger.info(f"回调验证成功: 订单ID={params.get('order_id')}")
        else:
            logger.warning(f"回调验证失败: 订单ID={params.get('order_id')}, 签名={signature}")
        return is_valid

    def check_payment_status(self, order_id: str) -> Dict:
        """检查支付状态"""
        if self.mock_mode:
            # Mock模式下随机返回支付状态
            status = PaymentStatus.PAID.value if time.time() % 10 != 0 else PaymentStatus.PENDING.value
            return {
                "order_id": order_id,
                "status": status,
                "transaction_id": f"txn_{str(uuid.uuid4())[:8]}",
                "last_checked": time.time()
            }
        else:
            # TODO: 实现真实支付状态查询
            raise NotImplementedError("真实支付状态查询功能暂未实现")

    def refund(self, order_id: str, amount: float) -> Dict:
        """处理退款"""
        if self.mock_mode:
            return {
                "order_id": order_id,
                "refund_id": f"ref_{str(uuid.uuid4())[:8]}",
                "amount": amount,
                "status": PaymentStatus.REFUNDED.value,
                "timestamp": time.time()
            }
        else:
            # TODO: 实现真实退款接口
            raise NotImplementedError("真实退款功能暂未实现")

    def _process_wechat_payment(self, order_id: str, amount: float) -> Dict:
        """处理微信支付"""
        if self.mock_mode:
            return {
                "order_id": order_id,
                "payment_method": PaymentMethod.WECHAT.value,
                "status": PaymentStatus.PAID.value,
                "transaction_id": f"wx_{str(uuid.uuid4())[:8]}",
                "timestamp": time.time()
            }
        else:
            # TODO: 实现真实微信支付接口
            raise NotImplementedError("真实微信支付功能暂未实现")

    def _process_alipay_payment(self, order_id: str, amount: float) -> Dict:
        """
        处理支付宝支付
        
        Args:
            order_id: 订单ID
            amount: 支付金额(单位:元)
            
        Returns:
            Dict: 支付宝支付结果，包含:
                - order_id: 订单ID
                - payment_method: 支付方式
                - status: 支付状态
                - transaction_id: 支付宝交易号
                - timestamp: 支付时间戳
                
        Note:
            真实实现需要调用支付宝支付API，当前为模拟模式
        """
        if self.mock_mode:
            return {
                "order_id": order_id,
                "payment_method": PaymentMethod.ALIPAY.value,
                "status": PaymentStatus.PAID.value,
                "transaction_id": f"ali_{str(uuid.uuid4())[:8]}",
                "timestamp": time.time()
            }
        else:
            # TODO: 实现真实支付宝支付接口
            raise NotImplementedError("真实支付宝支付功能暂未实现")