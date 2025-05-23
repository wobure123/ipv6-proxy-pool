import argparse
from ipv6_pool import IPv6Pool
from http_proxy import HTTPProxy
from socks5_proxy import SOCKS5Server

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IPv6 Proxy Pool')
    parser.add_argument('--mode', type=str, choices=['http', 'socks5'], default='socks5', help='启动模式: http 或 socks5')
    parser.add_argument('--port', type=int, default=43222, help='代理端口')
    parser.add_argument('--cidr', type=str, default=None, help='IPv6 CIDR filter')
    parser.add_argument('--socks5-user', type=str, default=None, help='SOCKS5 username')
    parser.add_argument('--socks5-pass', type=str, default=None, help='SOCKS5 password')
    args = parser.parse_args()

    ipv6_pool = IPv6Pool(args.cidr)
    print(f'IPv6 pool: {ipv6_pool.get_all()}')

    if args.mode == 'http':
        http_proxy = HTTPProxy('0.0.0.0', args.port, ipv6_pool)
        http_proxy.run()
    else:
        socks5_proxy = SOCKS5Server('0.0.0.0', args.port, ipv6_pool, args.socks5_user, args.socks5_pass)
        socks5_proxy.run()
