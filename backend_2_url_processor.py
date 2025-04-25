# 后端 2: 处理 URL 以获取网页内容
import pika
import json
import logging
import time
import sys
import os
# 确保 common 目录在 Python 路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.rabbitmq_utils import get_rabbitmq_connection, create_channel, declare_queue, publish_message

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - 后端 2 - %(levelname)s - %(message)s')

# 队列名称
URL_QUEUE = 'url_queue'
WEB_CONTENT_QUEUE = 'web_content_queue'

def simulate_fetch_web_content(url_info):
    """模拟为给定 URL 获取网页内容。"""
    url = url_info.get('url', '')
    source_tweet_id = url_info.get('source_tweet_id', '未知')
    logging.info(f"[{source_tweet_id}] 模拟获取 URL 内容: {url}")
    time.sleep(1) # 模拟网络延迟

    # 基于 URL 的模拟内容（非常基础的示例）
    mock_content = f"<html><body>{url} 的模拟内容。 "
    if "xyz" in url:
        mock_content += "此页面详细讨论了 $XYZ 项目。潜力巨大！"
    elif "abc-partner" in url:
        mock_content += "突发新闻：$ABC 币的合作关系已确认。价格飙升。"
    elif "web3" in url:
        mock_content += "Web 3.0 概念介绍。"
    elif "market" in url:
        mock_content += "一般市场分析，未提及特定代币。"
    elif "def" in url: # 根据推文 5 的 URL 添加
        mock_content += "分析表明 $DEF 可能被低估了。"
    else:
        mock_content += "在这里找到了一些通用的网页内容。"
    mock_content += "</body></html>"

    content_data = {
        "source_tweet_id": source_tweet_id,
        "original_url": url,
        "fetched_content": mock_content,
        "status": "内容已获取"
    }
    logging.info(f"[{source_tweet_id}] 模拟内容获取完成。")
    return json.dumps(content_data, ensure_ascii=False)

def callback(ch, method, properties, body):
    """当收到消息时执行的回调函数。"""
    source_tweet_id_for_log = '未知'
    try:
        message_str = body.decode('utf-8')
        logging.info(f"收到 URL 消息: {message_str}")
        url_info = json.loads(message_str)
        source_tweet_id_for_log = url_info.get('source_tweet_id', '未知')

        # 模拟获取内容
        web_content_message = simulate_fetch_web_content(url_info)

        # 发布获取到的内容
        publish_message(ch, WEB_CONTENT_QUEUE, web_content_message)

        # 确认消息
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.info(f"已确认推文的 URL 消息: {source_tweet_id_for_log}")

    except json.JSONDecodeError:
        logging.error(f"解析 URL JSON 失败: {body.decode('utf-8')}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        logging.warning(f"已拒绝格式错误的 URL 消息。")
    except Exception as e:
        logging.error(f"处理推文 {source_tweet_id_for_log} 的 URL 消息时出错: {body.decode('utf-8', errors='ignore')}. 错误: {e}", exc_info=True)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        logging.warning(f"因处理错误已 Nack 推文 {source_tweet_id_for_log} 的 URL 消息。")


def main():
    connection = get_rabbitmq_connection()
    if not connection: return

    channel = create_channel(connection)
    if not channel:
        if connection.is_open: connection.close()
        return

    # 声明必要的队列
    logging.info("正在声明队列...")
    declare_queue(channel, URL_QUEUE)
    declare_queue(channel, WEB_CONTENT_QUEUE)
    logging.info("队列声明完成。")

    # 设置服务质量 (QoS)
    channel.basic_qos(prefetch_count=1)
    logging.info("QoS prefetch count 设置为 1。")

    # 开始从 URL_QUEUE 消费
    consumer_tag = channel.basic_consume(queue=URL_QUEUE, on_message_callback=callback)
    logging.info(f"消费者标签: {consumer_tag}")

    logging.info(f"[*] 正在等待 '{URL_QUEUE}' 上的 URL 消息。按 CTRL+C 退出")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logging.info("用户中断。正在停止消费者...")
        # 不需要检查 is_consuming，直接停止
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