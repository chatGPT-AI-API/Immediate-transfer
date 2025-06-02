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