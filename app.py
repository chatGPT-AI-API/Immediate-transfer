from flask import Flask, request, jsonify, render_template
import uuid
import time
import re
from dotenv import load_dotenv
import requests
import io
import base64
import qrcode
import os

load_dotenv()  # 加载环境变量

# 支付模式配置 (True=模拟模式, False=真实模式)
MOCK_MODE = os.getenv('MOCK_MODE', 'true').lower() == 'true'

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mock_payment')
def mock_payment_page():
    """Render the mock payment page"""
    return render_template('mock_payment.html')

@app.route('/payment_callback')
@app.route('/payment_callback_page')
def payment_callback_page():
    """Render the payment callback result page with order details"""
    order_id = request.args.get('order_id')
    if not order_id or order_id not in DB["orders"]:
        return render_template('payment_callback.html',
                            status='fail',
                            order_id='无',
                            amount='无',
                            pay_time='无')
    
    order = DB["orders"][order_id]
    return render_template('payment_callback.html',
                        status='success' if order['status'] == 'paid' else 'fail',
                        order_id=order_id,
                        amount=order['amount'],
                        pay_time=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(order['pay_time'])) if order['pay_time'] else '无')

@app.route('/balance_query')
def balance_query_page():
    """Render the balance query page"""
    return render_template('balance_query.html')

# 模拟数据库（内存存储，生产环境需替换为MySQL/Redis等）
DB = {
    "orders": {},          # 订单存储 {order_id: order_info}
    "users": {             # 用户余额 {user_id: {"balance": float, "update_time": float}}
        "13812345678": {"balance": 100.0, "update_time": time.time()},    # 普通用户
        "13512345678": {"balance": 50.0, "update_time": time.time()},     # 普通用户2
        "13612345678": {"balance": 200.0, "update_time": time.time()}     # 普通用户3
    }
}

# 模拟支付网关配置（实际需从支付平台获取）
PAYMENT_GATEWAY = "https://mock-payment-gateway.com"
API_SECRET = "your-secret-key"  # 支付签名密钥


### **模块1：用户中心服务（模拟账号校验）**
def validate_user(account: str) -> bool:
    """校验账号有效性（示例：假设账号为手机号格式，且必须存在于模拟数据库中）"""
    if not re.match(r'^1[3-9]\\d{9}$', account):
        return False
    return account in DB["users"] # 修改为只允许已存在的用户


### **模块2：订单服务**
class OrderService:
    @staticmethod
    def create_order(account: str, amount: float) -> str:
        """生成订单"""
        order_id = str(uuid.uuid4())
        DB["orders"][order_id] = {
            "account": account,
            "amount": amount,
            "status": "pending",  # pending/paid/recharged
            "create_time": time.time(),
            "pay_time": None,
            "recharge_time": None
        }
        return order_id

    @staticmethod
    def update_order_status(order_id: str, status: str):
        """更新订单状态"""
        if order_id in DB["orders"]:
            DB["orders"][order_id]["status"] = status
            if status == "paid":
                DB["orders"][order_id]["pay_time"] = time.time()
            elif status == "recharged":
                DB["orders"][order_id]["recharge_time"] = time.time()
        return None


### **模块3：支付服务（模拟支付网关调用）**
class PaymentService:
    @staticmethod
    def simulate_payment(order_id: str) -> dict:
        """模拟支付请求（实际需调用支付宝/微信API）"""
        # 模拟支付结果（提高成功率到95%）
        is_success = True if time.time() % 20 != 0 else False
        return {
            "order_id": order_id,
            "status": "success" if is_success else "fail",
            "transaction_id": f"txn_{str(uuid.uuid4())[:8]}",
            "timestamp": time.time()
        }

    @staticmethod
    def verify_signature(params: dict) -> bool:
        """模拟支付回调签名校验（实际需按支付平台规则实现）"""
        # 简化逻辑：校验order_id存在且签名与秘钥一致
        return params.get("order_id") in DB["orders"] and params.get("signature") == API_SECRET

    @staticmethod
    def generate_qr_code(order_id: str, amount: float) -> dict:
        """生成支付二维码"""
        # 构建支付链接（实际环境需要真实的支付网关链接）
        payment_url = f"{PAYMENT_GATEWAY}/pay?order_id={order_id}&amount={amount}"
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_url)
        qr.make(fit=True)
        
        # 创建二维码图片
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为base64字符串
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "qr_code": f"data:image/png;base64,{img_str}",
            "payment_url": payment_url,
            "order_id": order_id,
            "amount": amount
        }


### **模块4：充值服务（核心实时操作）**
class RechargeService:
    @staticmethod
    def recharge(account: str, amount: float, order_id: str) -> bool:
        """执行充值操作（需保证幂等性）"""
        # 幂等性校验：检查订单是否已充值
        if DB["orders"][order_id]["status"] == "recharged":
            return True  # 已处理过，直接返回成功

        # 模拟账户余额更新（实际需调用钱包服务）
        if account not in DB["users"]:
            DB["users"][account] = {"balance": 0.0, "update_time": time.time()}
        DB["users"][account]["balance"] += amount
        DB["users"][account]["update_time"] = time.time()
        OrderService.update_order_status(order_id, "recharged")
        return True


### **模块5：API接口**
@app.route("/api/place_order", methods=["POST"])
def place_order():
    """下单接口"""
    data = request.json
    account = data.get("account")
    amount = data.get("amount")

    # 校验参数
    if not account or not amount: # Added check for missing account or amount
        return jsonify({"code": 400, "msg": "缺少账号或金额参数"}), 400

    try:
        amount = float(amount) # Ensure amount is a float
    except (ValueError, TypeError):
        return jsonify({"code": 400, "msg": "金额格式无效"}), 400


    if not validate_user(account):
        return jsonify({"code": 400, "msg": "账号无效或不存在"}), 400
    if amount <= 0:
        return jsonify({"code": 400, "msg": "金额无效"}), 400

    # 检查余额是否充足
    if account in DB["users"] and DB["users"][account].get("balance", 0) < amount: # Added .get("balance", 0) to handle missing balance key and default to 0
         return jsonify({"code": 400, "msg": "余额不足"}), 400

    # 生成订单
    order_id = OrderService.create_order(account, amount)
    return jsonify({"code": 200, "order_id": order_id}), 200


@app.route("/api/pay", methods=["POST"])
def process_payment():
    """支付接口（支持二维码支付）
    根据MOCK_MODE决定使用模拟支付还是真实支付
    """
    data = request.json
    order_id = data.get("order_id")
    payment_method = data.get("payment_method", "direct")  # direct/qr_code
    
    if order_id not in DB["orders"]:
        return jsonify({"code": 404, "msg": "订单不存在"}), 404
    
    order = DB["orders"][order_id]
    
    # 如果是二维码支付，返回二维码信息
    if payment_method == "qr_code":
        qr_data = PaymentService.generate_qr_code(order_id, order["amount"])
        return jsonify({
            "code": 200,
            "payment_method": "qr_code",
            "data": qr_data
        }), 200
    
    # 根据模式选择支付方式
    if MOCK_MODE:
        pay_result = PaymentService.simulate_payment(order_id)
    else:
        # TODO: 调用真实支付接口
        return jsonify({"code": 501, "msg": "真实支付功能暂未实现"}), 501
    if pay_result["status"] == "success":
        OrderService.update_order_status(order_id, "paid")
        # 支付成功后扣除用户余额
        order = DB["orders"][order_id]
        if order["account"] in DB["users"]:
            # 再次校验余额(防止并发问题)
            if DB["users"][order["account"]]["balance"] >= order["amount"]:
                DB["users"][order["account"]]["balance"] -= order["amount"]
                DB["users"][order["account"]]["update_time"] = time.time()
            else:
                # 余额不足，回滚订单状态
                OrderService.update_order_status(order_id, "failed")
                return jsonify({"code": 400, "msg": "Insufficient balance"}), 400
        return jsonify({
            "code": 200,
            "msg": "Payment succeeded",
            "transaction_id": pay_result["transaction_id"]
        }), 200
    return jsonify({"code": 400, "msg": "支付失败"}), 400


@app.route("/api/generate_qr_payment", methods=["POST"])
def generate_qr_payment():
    """生成支付二维码接口"""
    data = request.json
    order_id = data.get("order_id")
    
    if not order_id or order_id not in DB["orders"]:
        return jsonify({"code": 404, "msg": "订单不存在"}), 404
    
    order = DB["orders"][order_id]
    if order["status"] != "pending":
        return jsonify({"code": 400, "msg": "订单状态不允许支付"}), 400
    
    # 生成二维码
    qr_data = PaymentService.generate_qr_code(order_id, order["amount"])
    
    return jsonify({
        "code": 200,
        "data": qr_data
    }), 200

@app.route("/api/check_order_status", methods=["GET"])
def check_order_status():
    """查询订单状态"""
    order_id = request.args.get("order_id")
    if not order_id or order_id not in DB["orders"]:
        return jsonify({"code": 404, "msg": "订单不存在"}), 404
    
    order = DB["orders"][order_id]
    return jsonify({
        "code": 200,
        "status": order["status"],
        "order_id": order_id,
        "amount": order["amount"]
    }), 200

@app.route('/qr_payment')
def qr_payment_page():
    """二维码支付页面"""
    order_id = request.args.get('order_id')
    if not order_id or order_id not in DB["orders"]:
        return "订单不存在", 404
    
    order = DB["orders"][order_id]
    qr_data = PaymentService.generate_qr_code(order_id, order["amount"])
    
    return render_template('qr_payment.html',
                         order_id=order_id,
                         amount=order["amount"],
                         qr_code=qr_data["qr_code"])

@app.route("/api/payment_callback", methods=["POST"])
def payment_callback():
    """支付回调接口（需保证安全）"""
    params = request.json
    order_id = params.get("order_id")

    # 校验签名（简化逻辑）
    if not PaymentService.verify_signature(params):
        return jsonify({"code": 403, "msg": "签名无效"}), 403

    # 处理支付结果
    if DB["orders"][order_id]["status"] == "paid":
        return jsonify({"code": 200, "msg": "Already processed"}), 200  # 幂等性处理

    # 触发充值（异步或同步，示例中直接调用）
    order = DB["orders"][order_id]
    if RechargeService.recharge(order["account"], order["amount"], order_id):
        # 通知用户（示例中用打印模拟，实际需用WebSocket/短信等）
        print(f"Recharged {order['amount']} to {order['account']}")
        return jsonify({"code": 200, "msg": "Recharge succeeded"}), 200
    return jsonify({"code": 500, "msg": "充值失败"}), 500


@app.route("/api/check_balance", methods=["GET"])
def check_balance():
    """查询余额接口"""
    account = request.args.get("account")
    return jsonify({
        "code": 200,
        "account": account,
        "balance": DB["users"].get(account, {"balance": 0.0, "update_time": 0})["balance"],
        "update_time": DB["users"].get(account, {"balance": 0.0, "update_time": 0})["update_time"]
    }), 200


@app.route("/api/payment_mode", methods=["GET"])
def get_payment_mode():
    """获取当前支付模式"""
    return jsonify({
        "code": 200,
        "mock_mode": MOCK_MODE,
        "message": "模拟模式已启用" if MOCK_MODE else "真实支付模式"
    }), 200

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)