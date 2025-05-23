# 用于测试 HTTP 和 SOCKS5 代理的脚本
import requests
import sys
import socks
import socket
from urllib.parse import urlparse

def test_http_proxy(proxy_url):
    try:
        r = requests.get('http://6.ipw.cn/', proxies={'http': proxy_url, 'https': proxy_url}, timeout=10)
        print('HTTP代理测试成功:', r.text[:100])
    except Exception as e:
        print('HTTP代理测试失败:', e)

def test_socks5_proxy(proxy_url):
    # 支持 PySocks 底层测试
    try:
        u = urlparse(proxy_url)
        host = u.hostname
        port = u.port
        username = u.username
        password = u.password
        s = socks.socksocket()
        s.set_proxy(socks.SOCKS5, host, port, True, username, password)
        s.settimeout(10)
        s.connect(('6.ipw.cn', 80))
        s.sendall(b'GET / HTTP/1.1\r\nHost: 6.ipw.cn\r\nConnection: close\r\n\r\n')
        data = b''
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        print('SOCKS5代理测试成功:', data[:300])
        s.close()
    except Exception as e:
        print('SOCKS5代理测试失败:', e)

if __name__ == '__main__':
    # 用法: python test_proxy.py <http_proxy_url> <socks5_proxy_url>
    if len(sys.argv) < 3:
        print('用法: python test_proxy.py <http_proxy_url> <socks5_proxy_url>')
        sys.exit(1)
    test_http_proxy(sys.argv[1])
    test_socks5_proxy(sys.argv[2])
