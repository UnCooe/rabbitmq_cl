# RabbitMQ 实用工具
import pika
import sys
import os
import logging
from pika.exceptions import AMQPConnectionError # 明确导入异常类

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost') # 从环境变量获取RabbitMQ主机，默认为localhost

def get_rabbitmq_connection():
    """建立到 RabbitMQ 的连接。"""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        logging.info("成功连接到 RabbitMQ。")
        return connection
    except AMQPConnectionError as e: # 直接使用导入的异常类
        logging.error(f"连接 RabbitMQ ({RABBITMQ_HOST}) 失败: {e}")
        logging.error("请确保 RabbitMQ 正在运行并且可以访问。")
        # 可选：在此处实现重试逻辑
        sys.exit("因 RabbitMQ 连接失败而退出。") # 如果初始连接失败则退出

def declare_queue(channel, queue_name):
    """声明一个持久化的队列。"""
    try:
        channel.queue_declare(queue=queue_name, durable=True) # durable=True 确保队列持久化
        logging.info(f"队列 '{queue_name}' 声明成功。")
    except Exception as e:
        logging.error(f"声明队列 '{queue_name}' 失败: {e}")
        # 根据错误类型，可能需要不同的处理方式或退出

def publish_message(channel, queue_name, message):
    """向指定队列发布一条持久化消息。"""
    try:
        channel.basic_publish(
            exchange='', # 使用默认交换机
            routing_key=queue_name,
            body=message.encode('utf-8'), # 确保消息是 bytes 类型
            properties=pika.BasicProperties(
                delivery_mode=2,  # 使消息持久化
            ))
        logging.info(f"向队列 '{queue_name}' 发送消息: '{message[:50]}...'") # 记录截断后的消息
    except Exception as e:
        logging.error(f"向队列 '{queue_name}' 发布消息失败: {e}")
        # 处理发布错误，例如重试或记录日志

def create_channel(connection):
    """从连接创建一个新的信道。"""
    if connection is None or connection.is_closed:
        logging.error("无法创建信道。连接未打开。")
        return None
    try:
        channel = connection.channel()
        logging.info("信道创建成功。")
        return channel
    except Exception as e:
        logging.error(f"创建信道失败: {e}")
        return None

# 如果需要，以后可以在这里添加一个基本的消费者设置函数。 