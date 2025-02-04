import logging
import os
import sys
import time
import urllib.parse
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup

# 禁用错误输出
sys.stderr = open(os.devnull, 'w')
logging.getLogger('selenium.webdriver').setLevel(logging.ERROR)

class BrowserManager:
    _instance = None
    
    def __new__(cls):
        if not cls._instance:
            options = Options()
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--ignore-ssl-errors')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.headless = True
            service = Service(EdgeChromiumDriverManager().install())
            cls._instance = webdriver.Edge(service=service, options=options)
            cls._instance.set_page_load_timeout(30)
        return cls._instance

def smart_wait(driver, timeout=10):
    """智能等待页面加载完成"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
    except:
        pass

def handle_baidu_captcha(driver):
    """处理百度安全验证"""
    captcha_element = "wappass.baidu.com" in str(driver.current_url)
    if captcha_element:
        print("检测到百度安全验证，请手动完成验证...")
    while True:
        captcha_element = "wappass.baidu.com" in str(driver.current_url)
        if not captcha_element:
            break
        time.sleep(1)       
    # 等待页面变化
    smart_wait(driver) # 给页面一些时间加载
    print("验证完成，继续执行...")
    return True
    

def extract_paragraphs(driver, url: str) -> List[str]:
    """使用浏览器实例提取段落"""
    try:
        driver.get(url)
        smart_wait(driver)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        for tag in ['script', 'style', 'nav', 'footer', 'header', 'meta', 'link']:
            for element in soup(tag):
                element.decompose()
        
        return [p.get_text(separator=' ', strip=True) 
                for p in soup.find_all('p') 
                if p.get_text(strip=True)]
    except Exception as e:
        print(f"提取段落失败：{url}，错误：{e}")
        return []

def basic_filter(paragraphs: List[str]) -> List[str]:
    """基础段落过滤"""
    filtered = []
    for p in paragraphs:
        if len(p) < 20:
            continue
        if any(keyword in p for keyword in ["验证码", "手机号", "客户端", "二维码", "免责", "©","提现","举报","版权","微信"]):
            continue
        if "http" in p or "https" in p:
            continue
        filtered.append(p)
    return filtered

def check_baidu_link(driver, url: str) -> bool:
    """检查链接是否未被百度收录"""
    try:
        encoded_url = urllib.parse.quote(url)
        driver.get(f"https://www.baidu.com/s?wd={encoded_url}")
        smart_wait(driver)
        
        # 处理百度验证码
        if not handle_baidu_captcha(driver):
            return False
        
        # 使用特征class判断无结果
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        return soup.find('div', class_='nors') is not None
    except Exception as e:
        print(f"百度链接检查异常：{e}")
        return False

def check_baidu_content(driver, query_part: str, content_part: str) -> bool:
    """优化版百度内容检查"""
    try:
        encoded_query = urllib.parse.quote(query_part)
        driver.get(f"https://www.baidu.com/s?wd={encoded_query}")
        smart_wait(driver)
        
        # 处理百度验证码
        if not handle_baidu_captcha(driver):
            return False
        
        return content_part in driver.page_source
    except Exception as e:
        print(f"百度搜索异常：{e}")
        return False

def process_paragraphs(driver, paragraphs: List[str]) -> List[str]:
    """处理已被收录链接的段落"""
    valid_paragraphs = []
    for p in paragraphs:
        split_pos = max(len(p)//2, 20)
        first_half = p[split_pos-9:split_pos].strip()
        second_half = p[split_pos:split_pos+5].strip()
        
        if not first_half or not second_half:
            valid_paragraphs.append(p)
            continue
            
        if check_baidu_content(driver, first_half, second_half):
            continue
            
        valid_paragraphs.append(p)
    return valid_paragraphs

def bing_search(driver, query: str) -> List[str]:
    """增强版Bing搜索"""
    try:
        driver.get(f"https://www.bing.com/search?q={urllib.parse.quote(query)}")
        smart_wait(driver)
        
        results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ol#b_results li h2 a"))
        )
        
        return list({
            link.get_attribute('href')
            for link in results
            if not any(d in link.get_attribute('href') for d in ["bing.com", "microsoft.com", ".gov"])
        })
    except Exception as e:
        print(f"Bing搜索失败：{e}")
        return []

def main_workflow(query: str):
    """主工作流程"""
    driver = BrowserManager()
    
    try:
        print("正在执行Bing搜索...")
        search_results = bing_search(driver, query)
        print(f"找到 {len(search_results)} 个有效结果")
        
        final_content = []
        for idx, url in enumerate(search_results, 1):
            try:
                print(f"\n处理链接 {idx}/{len(search_results)}: {url}")
                
                # 先进行百度链接收录检查
                if check_baidu_link(driver, url):
                    print("链接未被百度收录，直接提取段落")
                    paragraphs = extract_paragraphs(driver, url)
                    valid_paragraphs = basic_filter(paragraphs)
                    final_content.extend(valid_paragraphs)
                else:
                    print("链接已被百度收录，进行详细检查")
                    paragraphs = extract_paragraphs(driver, url)
                    filtered = basic_filter(paragraphs)
                    valid_paragraphs = process_paragraphs(driver, filtered)
                    final_content.extend(valid_paragraphs)
                
                time.sleep(0.2)
                
            except Exception as e:
                print(f"处理链接失败：{url}，错误：{e}")
        
        os.system('cls')
        print("\n最终结果：")
        print("-"*60)
        for i, p in enumerate(final_content, 1):
            print(f"段落 {i}:")
            print(p)
            print("-"*60)
            
    finally:
        driver.quit()

if __name__ == "__main__":
    query = input("请输入搜索关键词：")
    main_workflow(query)
