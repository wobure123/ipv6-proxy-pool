import socket
import ipaddress
import random
from typing import List, Optional

try:
    import netifaces
except ImportError:
    netifaces = None

class IPv6Pool:
    def __init__(self, cidr: Optional[str] = None):
        self.cidr = ipaddress.IPv6Network(cidr) if cidr else None
        self.addresses = self._get_ipv6_addresses()

    def _get_ipv6_addresses(self) -> List[str]:
        addrs = []
        if netifaces:
            # 推荐方式：用netifaces遍历所有接口
            for iface in netifaces.interfaces():
                for link in netifaces.ifaddresses(iface).get(netifaces.AF_INET6, []):
                    ip = link['addr'].split('%')[0]  # 去掉zone id
                    if self._is_valid_ipv6(ip):
                        addrs.append(ip)
        else:
            # 兼容无netifaces环境，遍历getaddrinfo
            for iface in socket.if_nameindex():
                iface_name = iface[1]
                try:
                    infos = socket.getaddrinfo(None, 0, socket.AF_INET6, 0, 0, socket.AI_PASSIVE)
                    for entry in infos:
                        ip = entry[4][0]
                        if self._is_valid_ipv6(ip):
                            addrs.append(ip)
                except Exception:
                    continue
        addrs = list(set(addrs))
        # 过滤CIDR
        if self.cidr:
            addrs = [ip for ip in addrs if ipaddress.IPv6Address(ip) in self.cidr]
        return addrs

    def _is_valid_ipv6(self, ip: str) -> bool:
        # 排除回环、链路本地等
        if ip.startswith('fe80') or ip == '::1':
            return False
        try:
            ip_obj = ipaddress.IPv6Address(ip)
            return not ip_obj.is_loopback and not ip_obj.is_link_local and ip_obj.is_global
        except Exception:
            return False

    def get_random(self) -> Optional[str]:
        if not self.addresses:
            return None
        return random.choice(self.addresses)

    def get_all(self) -> List[str]:
        return self.addresses
