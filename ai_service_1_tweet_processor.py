# AI 服务 1: 处理推文
import json
import logging
import re
import sys
import os
# 确保 common 目录在 Python 路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.rabbitmq_utils import get_rabbitmq_connection, create_channel, declare_queue, publish_message

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - AI 服务 1 - %(levelname)s - %(message)s')

# 队列名称
TWEET_QUEUE = 'tweet_queue'
TOKEN_QUEUE = 'token_queue'
URL_QUEUE = 'url_queue'

# 用于查找潜在代币（例如 $XYZ）和 URL 的简单正则表达式
TOKEN_REGEX = re.compile(r'\$[A-Z]{2,}') # 查找 $ 后跟2个或更多大写字母
URL_REGEX = re.compile(r'https?://\S+')   # 查找 http:// 或 https:// 后跟非空白字符

def process_tweet(tweet_data):
    """模拟 AI 处理以提取代币或 URL。"""
    text = tweet_data.get('text', '')
    tweet_id = tweet_data.get('id', '未知')

    # 尝试查找代币
    token_match = TOKEN_REGEX.search(text)
    if token_match:
        token = token_match.group(0)
        logging.info(f"[{tweet_id}] 找到代币: {token}")
        # 创建结构化的代币信息（模拟）
        token_info = {
            "source_tweet_id": tweet_id,
            "token_symbol": token,
            "status": "从推文提取",
            "details": f"在推文文本中找到 {token}。"
        }
        return 'token', json.dumps(token_info, ensure_ascii=False)

    # 如果没有找到代币，尝试查找 URL
    url_match = URL_REGEX.search(text)
    if url_match:
        url = url_match.group(0)
        logging.info(f"[{tweet_id}] 未找到代币，找到 URL: {url}")
        # 准备 URL 信息
        url_info = {
            "source_tweet_id": tweet_id,
            "url": url
        }
        return 'url', json.dumps(url_info, ensure_ascii=False)

    # 如果既没有找到代币也没有找到 URL
    logging.warning(f"[{tweet_id}] 推文中未找到代币或 URL: {text}")
    return 'none', None


def callback(ch, method, properties, body):
    """当收到消息时执行的回调函数。"""
    tweet_id_for_log = '未知' # 日志记录的默认值
    try:
        message_str = body.decode('utf-8')
        logging.info(f"收到消息: {message_str}")
        tweet_data = json.loads(message_str)
        tweet_id_for_log = tweet_data.get('id', '未知') # 获取 ID 用于日志记录

        result_type, result_data = process_tweet(tweet_data)

        if result_type == 'token':
            publish_message(ch, TOKEN_QUEUE, result_data)
        elif result_type == 'url':
            publish_message(ch, URL_QUEUE, result_data)
        # 如果 result_type 是 'none'，我们只记录日志并确认消息

        # 确认消息已成功处理
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.info(f"已确认消息: {tweet_id_for_log}")

    except json.JSONDecodeError:
        logging.error(f"解析 JSON 失败: {body.decode('utf-8')}")
        # 拒绝格式错误的消息，不重新入队
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        logging.warning("已拒绝格式错误的消息。")
    except Exception as e:
        logging.error(f"处理消息 ID {tweet_id_for_log} 时出错: {body.decode('utf-8', errors='ignore')}. 错误: {e}", exc_info=True)
        # 发送否定确认，不重新入队以避免持久性错误导致的处理循环
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        logging.warning(f"因处理错误已 Nack 消息 ID {tweet_id_for_log}。")

def main():
    connection = get_rabbitmq_connection()
    if not connection:
        return

    channel = create_channel(connection)
    if not channel:
        if connection.is_open:
            connection.close()
        return

    # 声明必要的队列
    logging.info("正在声明队列...")
    declare_queue(channel, TWEET_QUEUE)
    declare_queue(channel, TOKEN_QUEUE)
    declare_queue(channel, URL_QUEUE)
    logging.info("队列声明完成。")

    # 设置服务质量 (QoS): 一次只处理一条消息，直到该消息被确认为止
    channel.basic_qos(prefetch_count=1)
    logging.info("QoS prefetch count 设置为 1。")

    # 开始从 TWEET_QUEUE 消费消息
    consumer_tag = channel.basic_consume(queue=TWEET_QUEUE, on_message_callback=callback)
    logging.info(f"消费者标签: {consumer_tag}")

    logging.info(f"[*] 正在等待 '{TWEET_QUEUE}' 上的消息。按 CTRL+C 退出")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logging.info("用户中断。正在停止消费者...")
        # 优雅地停止消费者 - 不需要检查 is_consuming
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