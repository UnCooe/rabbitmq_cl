# RabbitMQ 学习项目

本项目使用 Python 和 RabbitMQ 演示了一个模拟的数据处理流水线。

## 项目结构

```
rabbitmq_demo/
├── backend_1_crawler_mock.py         # 模拟发送推文数据
├── ai_service_1_tweet_processor.py   # 处理推文，提取代币或 URL
├── backend_2_url_processor.py        # 模拟根据 URL 获取网页内容
├── ai_service_2_web_processor.py   # 处理网页内容，提取代币
├── common/
│   ├── __init__.py                 # 使 common 成为 Python 包
│   └── rabbitmq_utils.py             # RabbitMQ 工具函数
├── requirements.txt                  # 项目依赖
└── README.md                         # 本文件
```

## 环境设置

1.  **安装 RabbitMQ:**
    通常最简单的方式是使用 Docker:
    ```bash
    docker run -d --hostname my-rabbit --name some-rabbit -p 5672:5672 -p 15672:15672 rabbitmq:3-management
    ```
    这将启动 RabbitMQ 并启用管理插件（访问地址 http://localhost:15672，默认用户名/密码: guest/guest）。

2.  **安装 Python 依赖:**
    ```bash
    pip install -r requirements.txt
    ```

## 运行组件

您需要在 **不同** 的终端窗口中分别运行各个 Python 脚本：

1.  `python rabbitmq_demo/ai_service_1_tweet_processor.py` （启动 AI 服务 1）
2.  `python rabbitmq_demo/backend_2_url_processor.py` （启动后端服务 2）
3.  `python rabbitmq_demo/ai_service_2_web_processor.py` （启动 AI 服务 2）
4.  `python rabbitmq_demo/backend_1_crawler_mock.py` （运行此脚本发送初始消息，它会自动退出）

观察各个终端的输出日志以及 RabbitMQ 管理界面（Queues 标签页），您可以看到消息在系统中的流转过程。 