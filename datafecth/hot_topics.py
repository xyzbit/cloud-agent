from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import csv
from datetime import datetime
import os
import time
import random
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
import logging
from fake_useragent import UserAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hot_topics.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HotTopicsCrawler:
    def __init__(self):
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.ua = UserAgent()
        self.setup_driver()

    def setup_driver(self):
        """设置浏览器驱动"""
        self.options.add_argument(f'user-agent={self.ua.random}')
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        self.wait = WebDriverWait(self.driver, 15)
        self.driver.set_window_size(1920, 1080)

    def random_sleep(self, min_seconds=1, max_seconds=3):
        """随机等待一段时间"""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def get_weibo_hot(self):
        """获取微博热搜榜"""
        try:
            self.driver.get('https://s.weibo.com/top/summary')
            self.random_sleep()
            topics = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.td-02 a'))
            )
            return [{'rank': i+1, 'title': topic.text, 'platform': 'weibo'} 
                   for i, topic in enumerate(topics[:50])]
        except Exception as e:
            logger.error(f"获取微博热搜失败: {str(e)}")
            return []

    def get_zhihu_hot(self):
        """获取知乎热榜"""
        try:
            self.driver.get('https://www.zhihu.com/hot')
            self.random_sleep()
            # 等待页面加载完成
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.HotList-list'))
            )
            # 滚动页面以加载更多内容
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self.random_sleep()
            topics = self.driver.find_elements(By.CSS_SELECTOR, '.HotList-item .HotItem-title')
            return [{'rank': i+1, 'title': topic.text, 'platform': 'zhihu'} 
                   for i, topic in enumerate(topics[:50])]
        except Exception as e:
            logger.error(f"获取知乎热榜失败: {str(e)}")
            return []

    def get_baidu_hot(self):
        """获取百度热搜"""
        try:
            self.driver.get('https://top.baidu.com/board?tab=realtime')
            self.random_sleep()
            topics = self.wait.until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.c-single-text-ellipsis'))
            )
            return [{'rank': i+1, 'title': topic.text, 'platform': 'baidu'} 
                   for i, topic in enumerate(topics[:50])]
        except Exception as e:
            logger.error(f"获取百度热搜失败: {str(e)}")
            return []

    def get_toutiao_hot(self):
        """获取今日头条热榜"""
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Referer': 'https://www.toutiao.com/'
            }
            url = 'https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc'
            response = requests.get(url, headers=headers)
            data = response.json()
            topics = []
            if 'data' in data:
                for i, item in enumerate(data['data'][:50]):
                    topics.append({
                        'rank': i + 1,
                        'title': item.get('Title', ''),
                        'platform': 'toutiao'
                    })
            return topics
        except Exception as e:
            logger.error(f"获取今日头条热榜失败: {str(e)}")
            return []

    def get_36kr_hot(self):
        """获取36氪热榜"""
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'application/json',
                'Referer': 'https://36kr.com/'
            }
            url = 'https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot'
            response = requests.post(url, headers=headers)
            data = response.json()
            topics = []
            if 'data' in data:
                for i, item in enumerate(data['data']['hotRankList'][:50]):
                    topics.append({
                        'rank': i + 1,
                        'title': item.get('templateMaterial', {}).get('widgetTitle', ''),
                        'platform': '36kr'
                    })
            return topics
        except Exception as e:
            logger.error(f"获取36氪热榜失败: {str(e)}")
            return []

    def get_bilibili_hot(self):
        """获取B站热门榜单"""
        try:
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'application/json',
                'Referer': 'https://www.bilibili.com/'
            }
            url = 'https://api.bilibili.com/x/web-interface/ranking/v2'
            response = requests.get(url, headers=headers)
            data = response.json()
            topics = []
            if 'data' in data and 'list' in data['data']:
                for i, item in enumerate(data['data']['list'][:50]):
                    topics.append({
                        'rank': i + 1,
                        'title': item.get('title', ''),
                        'platform': 'bilibili'
                    })
            return topics
        except Exception as e:
            logger.error(f"获取B站热门榜单失败: {str(e)}")
            return []

    def save_results(self, results, format='json'):
        """保存结果到文件"""
        timestamp = datetime.now()
        date_str = timestamp.strftime('%Y-%m-%d')
        time_str = timestamp.strftime('%H:%M:%S')
        
        # 确保输出目录存在
        os.makedirs('output', exist_ok=True)
        
        if format == 'json':
            filename = f'hot_topics_{date_str}_{time_str}.json'
            filepath = os.path.join('output', filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        else:  # CSV格式
            filename = f'{date_str}_{time_str}.csv'
            filepath = os.path.join('output', filename)
            
            # 将所有平台的数据合并到一个列表中
            all_topics = []
            for platform, topics in results.items():
                if platform != 'timestamp':
                    all_topics.extend(topics)
            
            # 按平台和排名排序
            all_topics.sort(key=lambda x: (x['platform'], x['rank']))
            
            # 写入CSV文件
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['platform', 'rank', 'title'])
                writer.writeheader()
                writer.writerows(all_topics)
        
        logger.info(f"结果已保存到: {filepath}")
        return filepath

    def crawl_all(self):
        """抓取所有平台的热点"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'weibo': self.get_weibo_hot(),
            'zhihu': self.get_zhihu_hot(),
            'baidu': self.get_baidu_hot(),
            'toutiao': self.get_toutiao_hot(),
            '36kr': self.get_36kr_hot(),
            'bilibili': self.get_bilibili_hot()
        }
        
        # 保存为JSON和CSV两种格式
        self.save_results(results, 'json')
        self.save_results(results, 'csv')
        return results

    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

def crawl_task():
    """定时任务执行的爬虫任务"""
    try:
        crawler = HotTopicsCrawler()
        results = crawler.crawl_all()
        logger.info("所有平台热点数据获取完成！")
        
        # 打印每个平台的热点数量
        for platform, topics in results.items():
            if platform != 'timestamp':
                logger.info(f"{platform}: 获取到 {len(topics)} 条热点")
    except Exception as e:
        logger.error(f"运行过程中发生错误: {str(e)}")
    finally:
        if 'crawler' in locals():
            del crawler

def main():
    """主函数：设置定时任务"""
    scheduler = BlockingScheduler()
    
    # 添加早上的定时任务（8:00-10:00之间随机时间）
    morning_hour = random.randint(8, 9)
    morning_minute = random.randint(0, 59)
    scheduler.add_job(crawl_task, 'cron', hour=morning_hour, minute=morning_minute)
    logger.info(f"已设置早上定时任务，将在每天 {morning_hour:02d}:{morning_minute:02d} 执行")
    
    # 添加中午的定时任务（12:00-14:00之间随机时间）
    noon_hour = random.randint(12, 13)
    noon_minute = random.randint(0, 59)
    scheduler.add_job(crawl_task, 'cron', hour=noon_hour, minute=noon_minute)
    logger.info(f"已设置中午定时任务，将在每天 {noon_hour:02d}:{noon_minute:02d} 执行")
    
    # 立即执行一次
    logger.info("开始执行首次爬取...")
    crawl_task()
    
    # 启动调度器
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("程序已终止")

if __name__ == "__main__":
    main() 