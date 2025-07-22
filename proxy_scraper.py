import requests
import concurrent.futures
import socket
import socks
import time
import os
from bs4 import BeautifulSoup

# 设置请求头
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

# 从网站获取代理列表
def get_proxies():
    url = 'https://www.proxy-list.download/SOCKS5'
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        proxies = []
        table = soup.find('table', {'id': 'tabli'})
        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:  # 跳过表头
                cols = row.find_all('td')
                if len(cols) >= 2:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    proxy = f"{ip}:{port}"
                    proxies.append(proxy)
        
        print(f"获取到 {len(proxies)} 个代理")
        return proxies
    except Exception as e:
        print(f"获取代理列表时出错: {e}")
        return []

# 测试代理是否可用
def test_proxy(proxy):
    ip, port = proxy.split(':')
    port = int(port)
    
    # 设置超时时间
    socket.setdefaulttimeout(5)
    
    try:
        # 创建一个SOCKS5代理连接
        sock = socks.socksocket()
        sock.set_proxy(socks.SOCKS5, ip, port)
        
        # 尝试连接到Google
        sock.connect(('www.google.com', 80))
        sock.close()
        
        print(f"代理 {proxy} 可用")
        return proxy
    except Exception as e:
        print(f"代理 {proxy} 不可用: {e}")
        return None

# 主函数
def main():
    # 获取代理列表
    proxies = get_proxies()
    
    # 如果没有获取到代理，退出程序
    if not proxies:
        print("未获取到代理，程序退出")
        return
    
    # 使用线程池测试代理
    working_proxies = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}
        for future in concurrent.futures.as_completed(future_to_proxy):
            result = future.result()
            if result:
                working_proxies.append(result)
    
    print(f"测试完成，共有 {len(working_proxies)} 个可用代理")
    
    # 将可用代理写入SOCKS5.txt
    with open('SOCKS5.txt', 'w') as f:
        for proxy in working_proxies:
            f.write(f"{proxy}\n")
    
    # 读取现有的SOCKS5_all.txt文件（如果存在）
    existing_proxies = set()
    if os.path.exists('SOCKS5_all.txt'):
        with open('SOCKS5_all.txt', 'r') as f:
            existing_proxies = set(line.strip() for line in f if line.strip())
    
    # 添加新的代理并去重
    all_proxies = existing_proxies.union(set(working_proxies))
    
    # 将所有代理写入SOCKS5_all.txt
    with open('SOCKS5_all.txt', 'w') as f:
        for proxy in all_proxies:
            f.write(f"{proxy}\n")
    
    print(f"已将 {len(working_proxies)} 个可用代理写入 SOCKS5.txt")
    print(f"已将 {len(all_proxies)} 个代理写入 SOCKS5_all.txt")

if __name__ == "__main__":
    main()