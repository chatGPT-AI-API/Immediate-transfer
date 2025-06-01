# 模拟支付与充值后端服务

这是一个使用 Flask 构建的简单后端服务，用于模拟支付下单、支付处理、支付回调和用户充值流程。

## 技术栈

- Python
- Flask

## 功能模块

- **用户中心服务**: 模拟用户账号的有效性校验。
- **订单服务**: 负责订单的创建和状态更新。
- **支付服务**: 模拟与支付网关的交互，包括模拟支付请求和回调签名校验。
- **充值服务**: 处理用户充值操作，并包含幂等性处理以防止重复充值。
- **API接口**: 提供外部调用的接口，用于下单、模拟支付、接收支付回调和查询用户余额。

## API 接口说明

### 1. 下单接口 (`POST /api/place_order`)

用于创建新的支付订单。

- **请求体示例:**
```json
{
  "account": "13800138000",
  "amount": 100.50
}
```
- **响应体示例:**
```json
{
  "code": 200,
  "order_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```

### 2. 模拟支付接口 (`POST /api/pay`)

模拟支付网关的处理过程。实际应用中应重定向到支付平台的支付页面。

- **请求体示例:**
```json
{
  "order_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
}
```
- **响应体示例 (成功):**
```json
{
  "code": 200,
  "msg": "Payment succeeded",
  "transaction_id": "txn_abcdefg"
}
```
- **响应体示例 (失败):**
```json
{
  "code": 400,
  "msg": "Payment failed"
}
```

### 3. 支付回调接口 (`POST /api/payment_callback`)

模拟接收支付网关发送的支付结果通知，并进行充值操作。包含签名校验和幂等性处理。

- **请求体示例:**
```json
{
  "order_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "status": "success",
  "transaction_id": "txn_abcdefg",
  "signature": "your-secret-key" // 模拟签名
}
```
- **响应体示例 (成功):**
```json
{
  "code": 200,
  "msg": "Recharge succeeded"
}
```
- **响应体示例 (已处理):**
```json
{
  "code": 200,
  "msg": "Already processed"
}
```
- **响应体示例 (签名无效):**
```json
{
  "code": 403,
  "msg": "Invalid signature"
}
```

### 4. 查询余额接口 (`GET /api/check_balance`)

查询用户当前的账户余额。

- **请求参数:**
  - `account`: 用户账号 (query parameter)

- **响应体示例:**
```json
{
  "code": 200,
  "balance": 100.50
}
```

## 如何运行

1. 克隆仓库。
2. 安装依赖：`pip install Flask python-dotenv requests uuid`
3. 运行应用：`python app.py`
4. 应用将在：`http://127.0.0.1:5000/` 运行。 