# AI 服务 2: 处理网页内容
import pika
import json
import logging
import re
import sys
import os
# 确保 common 目录在 Python 路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.rabbitmq_utils import get_rabbitmq_connection, create_channel, declare_queue, publish_message

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - AI 服务 2 - %(levelname)s - %(message)s')

# 队列名称
WEB_CONTENT_QUEUE = 'web_content_queue'
TOKEN_QUEUE = 'token_queue' # 与 AI 服务 1 成功提取代币后使用的队列相同
ERROR_QUEUE = 'error_queue' # 用于最终失败的队列

# 用于查找潜在代币（例如 $XYZ）的简单正则表达式
TOKEN_REGEX = re.compile(r'\$[A-Z]{2,}') # 与之前使用的正则表达式相同

def process_web_content(content_data):
    """模拟对网页内容进行 AI 处理以查找代币。"""
    content = content_data.get('fetched_content', '')
    source_tweet_id = content_data.get('source_tweet_id', '未知')
    original_url = content_data.get('original_url', '未知')

    # 尝试在获取的内容中查找代币
    token_match = TOKEN_REGEX.search(content)
    if token_match:
        token = token_match.group(0)
        logging.info(f"[{source_tweet_id}] 在网页内容中找到代币: {token} (来自 URL: {original_url})")
        # 创建结构化的代币信息（模拟）
        token_info = {
            "source_tweet_id": source_tweet_id,
            "original_url": original_url,
            "token_symbol": token,
            "status": "从网页内容提取",
            "details": f"在从 {original_url} 获取的内容中找到 {token}。"
        }
        return 'token', json.dumps(token_info, ensure_ascii=False)
    else:
        # 如果在网页内容中未找到代币
        logging.warning(f"[{source_tweet_id}] 在来自 URL 的网页内容中未找到代币: {original_url}")
        error_info = {
            "source_tweet_id": source_tweet_id,
            "original_url": original_url,
            "error": "无法从网页内容中提取代币。",
            "content_snippet": content[:100] + "..." # 包含内容片段以供参考
        }
        return 'error', json.dumps(error_info, ensure_ascii=False)


def callback(ch, method, properties, body):
    """当收到消息时执行的回调函数。"""
    source_tweet_id_for_log = '未知'
    try:
        message_str = body.decode('utf-8')
        logging.info(f"收到网页内容消息: {message_str[:100]}...") # 记录截断后的消息
        content_data = json.loads(message_str)
        source_tweet_id_for_log = content_data.get('source_tweet_id', '未知')

        result_type, result_data = process_web_content(content_data)

        if result_type == 'token':
            publish_message(ch, TOKEN_QUEUE, result_data)
        elif result_type == 'error':
            publish_message(ch, ERROR_QUEUE, result_data)
            # 可选：仅记录日志而不是发送到错误队列：
            # logging.error(f"推文 {source_tweet_id_for_log} 的最终处理错误: {result_data}")

        # 确认消息
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.info(f"已确认推文的网页内容消息: {source_tweet_id_for_log}")

    except json.JSONDecodeError:
        logging.error(f"解析网页内容 JSON 失败: {body.decode('utf-8')}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        logging.warning(f"已拒绝格式错误的网页内容消息。")
    except Exception as e:
        logging.error(f"处理推文 {source_tweet_id_for_log} 的网页内容时出错: {body.decode('utf-8', errors='ignore')[:100]}... 错误: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        logging.warning(f"因处理错误已 Nack 推文 {source_tweet_id_for_log} 的网页内容消息。")

def main():
    connection = get_rabbitmq_connection()
    if not connection: return

    channel = create_channel(connection)
    if not channel:
        if connection.is_open: connection.close()
        return

    # 声明必要的队列
    logging.info("正在声明队列...")
    declare_queue(channel, WEB_CONTENT_QUEUE)
    declare_queue(channel, TOKEN_QUEUE)
    declare_queue(channel, ERROR_QUEUE) # 同时声明错误队列
    logging.info("队列声明完成。")

    # 设置服务质量 (QoS)
    channel.basic_qos(prefetch_count=1)
    logging.info("QoS prefetch count 设置为 1。")

    # 开始从 WEB_CONTENT_QUEUE 消费
    consumer_tag = channel.basic_consume(queue=WEB_CONTENT_QUEUE, on_message_callback=callback)
    logging.info(f"消费者标签: {consumer_tag}")

    logging.info(f"[*] 正在等待 '{WEB_CONTENT_QUEUE}' 上的网页内容消息。按 CTRL+C 退出")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logging.info("用户中断。正在停止消费者...")
        channel.stop_consuming()
        logging.info("消费者已停止。正在关闭连接...")
        if connection.is_open:
            connection.close()
        logging.info("连接已关闭。")
    except Exception as e:
        logging.error(f"消费者遇到未处理的错误: {e}", exc_info=True)
        if connection.is_open:
            connection.close()
        sys.exit("因消费者错误而退出。")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.critical(f"应用程序发生严重错误: {e}", exc_info=True)
        sys.exit(1) 