# 立即到账支付系统

## 功能特性

- 支持模拟支付和真实支付两种模式
- 默认启用模拟支付模式(MOCK_MODE=true)
- 提供支付模式查询接口(/api/payment_mode)

## 配置说明

在.env文件中设置以下参数：
```
MOCK_MODE=true  # true启用模拟模式，false启用真实支付模式
API_SECRET=your-secret-key  # 支付签名密钥
```

## API接口

### 支付模式查询
GET /api/payment_mode
返回当前支付模式状态

### 模拟支付
POST /api/pay
在模拟模式下自动返回成功/失败结果

## API 接口说明

### 1. 下单接口 (`POST /api/place_order`)

用于创建新的支付订单。

 **请求体示例:**
```json
{
  "account": "13800138000",
  "amount": 100.50
}
```
 **响应体示例:**
```json
{
  "code": 200,
  "order_id": "a1b2c3d4e5f678901234567890abcdef"
}
```

### 2. 模拟支付接口 (`POST /api/pay`)

模拟支付网关的处理过程。实际应用中应重定向到支付平台的支付页面。

 **请求体示例:**
```json
{
  "order_id": "a1b2c3d4e5f678901234567890abcdef"
}
```
 **响应体示例 (成功):**
```json
{
  "code": 200,
  "msg": "Payment succeeded",
  "transaction_id": "txn_abcdefg"
}
```
 **响应体示例 (失败):**
```json
{
  "code": 400,
  "msg": "Payment failed"
}
```

### 3. 支付回调接口 (`POST /api/payment_callback`)

模拟接收支付网关发送的支付结果通知，并进行充值操作。包含签名校验和幂等性处理。

 **请求体示例:**
```json
{
  "order_id": "a1b2c3d4e5f678901234567890abcdef",
  "status": "success",
  "transaction_id": "txn_abcdefg",
  "signature": "yoursecretkey" // 模拟签名
}
```
 **响应体示例 (成功):**
```json
{
  "code": 200,
  "msg": "Recharge succeeded"
}
```
 **响应体示例 (已处理):**
```json
{
  "code": 200,
  "msg": "Already processed"
}
```
 **响应体示例 (签名无效):**
```json
{
  "code": 403,
  "msg": "Invalid signature"
}
```

### 4. 查询余额接口 (`GET /api/check_balance`)

查询用户当前的账户余额。

 **请求参数:**
   `account`: 用户账号 (query parameter)

 **响应体示例:**
```json
{
  "code": 200,
  "balance": 100.50
}
```

## 开发说明

1. 开发测试时建议使用模拟模式(MOCK_MODE=true)
2. 生产环境切换为真实模式前需实现真实支付接口
3. 模拟支付成功率约为95%，用于测试各种支付场景
4. 可通过修改.env文件或环境变量切换模式

## 快速开始

1. 安装依赖: `pip install -r requirements.txt`
2. 配置.env文件
3. 启动服务: `python app.py`
4. 访问http://localhost:5000使用支付功能