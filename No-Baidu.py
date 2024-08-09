import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def search_baidu(query):
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.headless = True  
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    search_url = f"https://www.baidu.com/s?wd={query}"
    driver.get(search_url)
    results = set()
    links = driver.find_elements(By.CSS_SELECTOR, 'h3.t a')
    for link in links:
        try:
            url = link.get_attribute('href')
            if url and url.startswith('http'):
                results.add(url)
        except:
            continue
    driver.quit()
    return results



def search_bing(query):
    options = Options()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.headless = True
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    search_url = f"https://www.bing.com/search?q={query}"
    driver.get(search_url)
    results = set()
    links = driver.find_elements(By.CSS_SELECTOR, 'a')
    for link in links:
        try:
            url = link.get_attribute('href')
            if url and url.startswith('http'):
                results.add(url)
        except:
            continue
    driver.quit()
    return results



def display_unique_bing_results(baidu_results, bing_results):
    unique_bing_results = bing_results - baidu_results
    for url in unique_bing_results:
        if "bing" not in url and "baidu" not in url and "go.microsoft" not in url:
            print(url)




if __name__ == "__main__":
    query = input("请输入搜索关键词：")
    baidu_results = search_baidu(query)
    bing_results = search_bing(query)
    os.system("cls")
    display_unique_bing_results(baidu_results, bing_results)
