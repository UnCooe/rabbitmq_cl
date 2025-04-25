# 后端 1: 模拟获取推文数据
import time
import json
import logging
# 确保 common 目录在 Python 路径中
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.rabbitmq_utils import get_rabbitmq_connection, create_channel, declare_queue, publish_message

# 为此模块配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - 后端 1 - %(levelname)s - %(message)s')

TWEET_QUEUE = 'tweet_queue' # 定义推文队列名称

def get_mock_tweets():
    """生成一个模拟推文数据列表。"""
    return [
        {"id": "tweet_1", "text": "看看新的 $XYZ 代币，它要涨到月球上去了！信息：https://example.com/xyz"},
        {"id": "tweet_2", "text": "刚读了一篇关于 web3 的有趣文章。链接：https://anothersite.org/web3"},
        {"id": "tweet_3", "text": "关于 $ABC 币合作关系的传闻。更多详情：https://news.com/abc-partner"},
        {"id": "tweet_4", "text": "我对当前市场趋势的看法。访问 https://myblog.com/market"},
        {"id": "tweet_5", "text": "$DEF 是下一个大事件吗？在此处阅读分析：https://cryptoanalysis.io/def"}
    ]

def main():
    connection = get_rabbitmq_connection()
    if not connection:
        return # 如果连接失败则退出

    channel = create_channel(connection)
    if not channel:
        if connection.is_open:
            connection.close()
        return # 如果创建信道失败则退出

    # 声明队列（确保它存在）
    declare_queue(channel, TWEET_QUEUE)

    mock_tweets = get_mock_tweets()

    logging.info(f"开始向 '{TWEET_QUEUE}' 发布 {len(mock_tweets)} 条模拟推文...")

    for tweet in mock_tweets:
        # 将推文字典转换为 JSON 字符串以便发送
        try:
            message = json.dumps(tweet, ensure_ascii=False) # ensure_ascii=False 保证中文正常显示
            publish_message(channel, TWEET_QUEUE, message)
            time.sleep(0.5) # 模拟消息之间的发送延迟
        except TypeError as e:
            logging.error(f"无法将推文序列化为 JSON: {tweet}. 错误: {e}")
        except Exception as e:
            logging.error(f"发布推文时发生错误: {tweet}. 错误: {e}")
            # 决定是中断还是继续
            break

    logging.info("模拟推文发布完成。")

    # 关闭连接
    if connection.is_open:
        try:
            connection.close()
            logging.info("RabbitMQ 连接已关闭。")
        except Exception as e:
            logging.error(f"关闭 RabbitMQ 连接时出错: {e}")

if __name__ == '__main__':
    main() 