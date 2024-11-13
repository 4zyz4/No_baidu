import os
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import logging

# 将sys.stderr重定向到os.devnull，隐藏所有错误输出
sys.stderr = open(os.devnull, 'w')

# 设置Selenium日志级别为ERROR
logging.getLogger('selenium.webdriver').setLevel(logging.ERROR)

def initialize_driver():
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.headless = True
    driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
    return driver

def search_baidu(driver, query):
    search_url = f"https://www.baidu.com/s?wd={query}"
    driver.get(search_url)

    # 检查页面是否包含“抱歉，未找到相关结果”等文本
    has_results = "抱歉，未找到相关结果" in driver.page_source or "没有找到该URL" in driver.page_source
    return not has_results

def search_bing(driver, query):
    search_url = f"https://www.bing.com/search?q={query}"
    driver.get(search_url)
    bing_results = []

    # 等待搜索结果加载
    driver.implicitly_wait(10)

    links = driver.find_elements(By.CSS_SELECTOR, 'a')
    for link in links:
        try:
            url = link.get_attribute('href')
            if url and url.startswith('http'):
                bing_results.append(url)  # 存储完整URL
        except Exception as e:
            print(f"Error extracting Bing link: {e}")
            continue
    return list(set(bing_results))  # 去重并返回

def crawl_and_display_results(query):
    driver = initialize_driver()
    bing_results = search_bing(driver, query)   
    
    # 存储每个在百度没有结果的链接
    no_results = []

    for url in bing_results:
        if not any(domain in url for domain in ["bing", "microsoft","gov"]):  # 排除链接
            if not search_baidu(driver, url):  # 如果在百度没有找到结果
                no_results.append(url)  # 添加到结果列表中

    driver.quit()  # 关闭浏览器
    os.system("cls")  # 清屏
    print("结果：")
    # 打印没有在百度找到结果的链接
    for url in no_results:
        print(url)

if __name__ == "__main__":
    query = input("请输入搜索关键词：")
    crawl_and_display_results(query)
