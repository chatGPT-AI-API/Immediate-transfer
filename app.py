from flask import Flask, request, jsonify, render_template
import uuid
import time
import re
from dotenv import load_dotenv
import requests

load_dotenv()  # 加载环境变量（模拟配置）

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
    "users": {             # 用户余额 {user_id: balance}
        "13812345678": 200.0    # 测试用户
    }
}

# 模拟支付网关配置（实际需从支付平台获取）
PAYMENT_GATEWAY = "https://mock-payment-gateway.com"
API_SECRET = "your-secret-key"  # 支付签名密钥


### **模块1：用户中心服务（模拟账号校验）**
def validate_user(account: str) -> bool:
    """校验账号有效性（示例：假设账号为手机号格式）"""
    if not re.match(r'^1[3-9]\d{9}$', account):
        return False
    return account in DB["users"] or True  # 允许新用户（实际需根据业务调整）


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
            DB["users"][account] = 0.0
        DB["users"][account] += amount
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
    if not validate_user(account):
        return jsonify({"code": 400, "msg": "账号无效"}), 400
    if amount <= 0:
        return jsonify({"code": 400, "msg": "金额无效"}), 400
    # 检查余额是否充足
    if account in DB["users"] and DB["users"][account] < amount:
        return jsonify({"code": 400, "msg": "余额不足"}), 400

    # 生成订单
    order_id = OrderService.create_order(account, amount)
    return jsonify({"code": 200, "order_id": order_id}), 200


@app.route("/api/pay", methods=["POST"])
def simulate_payment():
    """模拟支付接口（实际需跳转支付网关）"""
    order_id = request.json.get("order_id")
    if order_id not in DB["orders"]:
        return jsonify({"code": 404, "msg": "订单不存在"}), 404

    # 模拟支付流程
    pay_result = PaymentService.simulate_payment(order_id)
    if pay_result["status"] == "success":
        OrderService.update_order_status(order_id, "paid")
        # 支付成功后扣除用户余额
        order = DB["orders"][order_id]
        if order["account"] in DB["users"]:
            # 再次校验余额(防止并发问题)
            if DB["users"][order["account"]] >= order["amount"]:
                DB["users"][order["account"]] -= order["amount"]
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
        "balance": DB["users"].get(account, 0.0),
        "update_time": time.time()
    }), 200


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)