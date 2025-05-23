import argparse
from ipv6_pool import IPv6Pool
from http_proxy import HTTPProxy
from socks5_proxy import SOCKS5Server

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IPv6 Proxy Pool')
    parser.add_argument('--port', type=int, default=8080, help='HTTP proxy port')
    parser.add_argument('--cidr', type=str, default=None, help='IPv6 CIDR filter')
    parser.add_argument('--socks5-user', type=str, default=None, help='SOCKS5 username')
    parser.add_argument('--socks5-pass', type=str, default=None, help='SOCKS5 password')
    args = parser.parse_args()

    ipv6_pool = IPv6Pool(args.cidr)
    print(f'IPv6 pool: {ipv6_pool.get_all()}')

    # 启动 HTTP 代理
    http_proxy = HTTPProxy('0.0.0.0', args.port, ipv6_pool)
    # 启动 SOCKS5 代理
    socks5_proxy = SOCKS5Server('0.0.0.0', args.port + 1, ipv6_pool, args.socks5_user, args.socks5_pass)

    import threading
    threading.Thread(target=http_proxy.run, daemon=True).start()
    socks5_proxy.run()
