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
        
        # 打印响应状态和内容长度，用于调试
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容长度: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 保存HTML内容到文件，用于调试
        with open('debug_html.txt', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        proxies = []
        
        # 尝试多种选择器来定位表格
        # 1. 尝试原始的id选择器
        table = soup.find('table', {'id': 'tabli'})
        
        # 2. 如果没找到，尝试查找所有表格
        if not table:
            print("未找到id为tabli的表格，尝试查找所有表格...")
            tables = soup.find_all('table')
            print(f"找到 {len(tables)} 个表格")
            
            # 如果有表格，使用第一个
            if tables:
                table = tables[0]
                print(f"使用第一个表格，该表格有 {len(table.find_all('tr'))} 行")
        
        # 3. 如果仍然没找到，尝试使用class选择器
        if not table:
            print("尝试使用class选择器查找表格...")
            table = soup.find('table', {'class': 'table'})
            # 尝试其他可能的class
            if not table:
                table = soup.find('table', {'class': 'table-striped'})
            if not table:
                table = soup.find('table', {'class': 'table-hover'})
        
        if table:
            rows = table.find_all('tr')
            print(f"表格中找到 {len(rows)} 行")
            
            for row in rows[1:]:  # 跳过表头
                cols = row.find_all('td')
                print(f"行中找到 {len(cols)} 列")
                
                if len(cols) >= 2:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    proxy = f"{ip}:{port}"
                    proxies.append(proxy)
                    print(f"添加代理: {proxy}")
        else:
            print("未找到任何表格")
            
            # 尝试直接查找IP和端口元素
            ip_elements = soup.select('.ip')
            port_elements = soup.select('.port')
            
            if ip_elements and port_elements and len(ip_elements) == len(port_elements):
                print(f"直接找到 {len(ip_elements)} 个IP和端口元素")
                for i in range(len(ip_elements)):
                    ip = ip_elements[i].text.strip()
                    port = port_elements[i].text.strip()
                    proxy = f"{ip}:{port}"
                    proxies.append(proxy)
                    print(f"添加代理: {proxy}")
        
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
    
    # 尝试多个目标网站
    test_sites = [
        ('www.google.com', 80),
        ('www.bing.com', 80),
        ('www.baidu.com', 80),
        ('www.yahoo.com', 80)
    ]
    
    # 最大重试次数
    max_retries = 2
    
    for site, port_num in test_sites:
        for attempt in range(max_retries):
            try:
                # 创建一个SOCKS5代理连接
                sock = socks.socksocket()
                sock.set_proxy(socks.SOCKS5, ip, port)
                
                # 尝试连接到目标网站
                sock.connect((site, port_num))
                
                # 尝试发送HTTP请求
                sock.send(f"GET / HTTP/1.1\r\nHost: {site}\r\n\r\n".encode())
                
                # 接收响应
                response = sock.recv(1024)
                sock.close()
                
                if response:
                    print(f"代理 {proxy} 可用 (通过 {site})")
                    return proxy
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"代理 {proxy} 连接 {site} 失败，尝试重试: {e}")
                    time.sleep(1)  # 重试前等待1秒
                else:
                    print(f"代理 {proxy} 连接 {site} 失败: {e}")
    
    print(f"代理 {proxy} 不可用: 所有测试站点均连接失败")
    return None

# 从备用来源获取代理列表
def get_proxies_from_backup_sources():
    backup_sources = [
        'https://www.socks-proxy.net/',
        'https://www.proxy-list.download/api/v1/get?type=socks5',
        'https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all'
    ]
    
    all_proxies = []
    
    for url in backup_sources:
        try:
            print(f"尝试从备用源获取代理: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            if 'text/html' in response.headers.get('Content-Type', ''):
                # HTML格式，需要解析
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找所有表格
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # 跳过表头
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            try:
                                ip = cols[0].text.strip()
                                port = cols[1].text.strip()
                                if ip and port and port.isdigit():
                                    proxy = f"{ip}:{port}"
                                    all_proxies.append(proxy)
                                    print(f"从备用源添加代理: {proxy}")
                            except Exception as e:
                                print(f"解析代理时出错: {e}")
            else:
                # 纯文本格式，直接按行分割
                lines = response.text.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if ':' in line:
                        parts = line.split(':')  
                        if len(parts) == 2 and parts[1].isdigit():
                            all_proxies.append(line)
                            print(f"从备用源添加代理: {line}")
        
        except Exception as e:
            print(f"从备用源 {url} 获取代理时出错: {e}")
    
    # 去重
    unique_proxies = list(set(all_proxies))
    print(f"从备用源获取到 {len(unique_proxies)} 个代理")
    return unique_proxies

# 主函数
def main():
    # 获取代理列表
    proxies = get_proxies()
    
    # 如果没有获取到代理，尝试从备用源获取
    if not proxies:
        print("从主要源未获取到代理，尝试从备用源获取...")
        proxies = get_proxies_from_backup_sources()
    
    # 如果仍然没有获取到代理，退出程序
    if not proxies:
        print("未从任何源获取到代理，程序退出")
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
