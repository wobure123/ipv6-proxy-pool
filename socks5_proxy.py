import socket
import struct
import asyncio
import random
from ipv6_pool import IPv6Pool
from utils import resolve_host

class SOCKS5Server:
    def __init__(self, listen_host, listen_port, ipv6_pool: IPv6Pool, username=None, password=None):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.ipv6_pool = ipv6_pool
        self.username = username
        self.password = password

    async def handle_client(self, reader, writer):
        # 握手
        data = await reader.read(2)
        if not data or data[0] != 0x05:
            writer.close()
            return
        n_methods = data[1]
        methods = await reader.read(n_methods)
        # 认证协商
        if self.username and self.password:
            if 2 not in methods and b'\x02' not in methods:
                writer.write(b'\x05\xff')
                await writer.drain()
                writer.close()
                return
            writer.write(b'\x05\x02')  # 需要用户名密码
            await writer.drain()
            # 用户名密码认证
            ver = await reader.read(1)
            ulen = await reader.read(1)
            uname = await reader.read(ord(ulen))
            plen = await reader.read(1)
            passwd = await reader.read(ord(plen))
            if uname.decode() != self.username or passwd.decode() != self.password:
                writer.write(b'\x01\x01')
                await writer.drain()
                writer.close()
                print(f"[SOCKS5] 认证失败: 用户名={uname.decode()} 密码={passwd.decode()}")
                return
            writer.write(b'\x01\x00')
            await writer.drain()
        else:
            if 0 not in methods and b'\x00' not in methods:
                writer.write(b'\x05\xff')
                await writer.drain()
                writer.close()
                return
            writer.write(b'\x05\x00')  # 无需认证
            await writer.drain()
        # 请求
        data = await reader.read(4)
        if not data or data[1] != 0x01:
            writer.close()
            return
        atyp = data[3]
        if atyp == 1:  # IPv4
            addr = await reader.read(4)
            dest_addr = socket.inet_ntoa(addr)
        elif atyp == 3:  # 域名
            length = await reader.read(1)
            addr = await reader.read(ord(length))
            dest_addr = addr.decode()
        elif atyp == 4:  # IPv6
            addr = await reader.read(16)
            dest_addr = socket.inet_ntop(socket.AF_INET6, addr)
        else:
            writer.close()
            return
        dest_port = int.from_bytes(await reader.read(2), 'big')
        ip, family = await resolve_host(dest_addr)
        if not ip:
            print(f"[SOCKS5] DNS解析失败: {dest_addr}")
            writer.close()
            return
        # 选择出口
        if family == socket.AF_INET6:
            local_ipv6 = self.ipv6_pool.get_random()
            local_addr = (local_ipv6, 0, 0, 0)
            print(f"[SOCKS5] 选择IPv6出口: {local_ipv6}")
        else:
            local_addr = None
            print(f"[SOCKS5] 选择IPv4出口")
        try:
            # 用asyncio.open_connection建立到目标的流连接
            remote_reader, remote_writer = await asyncio.open_connection(ip, dest_port, family=family, local_addr=local_addr)
            # 回复成功
            writer.write(b'\x05\x00\x00\x01' + socket.inet_aton('0.0.0.0') + (0).to_bytes(2, 'big'))
            await writer.drain()
            # 转发
            async def relay(reader, writer, tag):
                try:
                    while True:
                        data = await reader.read(4096)
                        if not data:
                            break
                        writer.write(data)
                        await writer.drain()
                except Exception as e:
                    pass
            await asyncio.gather(
                relay(reader, remote_writer, '客户端->目标'),
                relay(remote_reader, writer, '目标->客户端')
            )
        except Exception as e:
            print(f"[SOCKS5] 连接目标失败: {dest_addr}:{dest_port} 错误: {e}")
            writer.close()
            return

    def run(self):
        async def main():
            server = await asyncio.start_server(self.handle_client, self.listen_host, self.listen_port)
            async with server:
                await server.serve_forever()
        asyncio.run(main())
