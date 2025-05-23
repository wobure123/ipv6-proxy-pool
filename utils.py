import socket
import asyncio
import ipaddress
import random
import dns.resolver

async def resolve_host(host):
    # 优先解析AAAA，再降级A
    try:
        answers = dns.resolver.resolve(host, 'AAAA')
        for r in answers:
            return str(r), socket.AF_INET6
    except Exception:
        pass
    try:
        answers = dns.resolver.resolve(host, 'A')
        for r in answers:
            return str(r), socket.AF_INET
    except Exception:
        pass
    # 直接是IP
    try:
        ip_obj = ipaddress.ip_address(host)
        if ip_obj.version == 6:
            return host, socket.AF_INET6
        else:
            return host, socket.AF_INET
    except Exception:
        pass
    return None, None
