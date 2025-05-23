import socket
import asyncio
import random
from aiohttp import web
from ipv6_pool import IPv6Pool
from utils import resolve_host

class HTTPProxy:
    def __init__(self, listen_host, listen_port, ipv6_pool: IPv6Pool):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.ipv6_pool = ipv6_pool

    async def handle_connect(self, request):
        # HTTP CONNECT 隧道
        dest_host, dest_port = request.match_info['dest'].split(':')
        dest_port = int(dest_port)
        ip, family = await resolve_host(dest_host)
        if not ip:
            return web.Response(status=502, text='DNS error')
        if family == socket.AF_INET6:
            local_addr = (self.ipv6_pool.get_random(), 0, 0, 0)
        else:
            local_addr = None
        try:
            remote = socket.socket(family, socket.SOCK_STREAM)
            if local_addr:
                remote.bind(local_addr)
            await asyncio.get_event_loop().sock_connect(remote, (ip, dest_port))
        except Exception as e:
            return web.Response(status=502, text=f'Connect error: {e}')
        resp = web.StreamResponse(status=200, reason='Connection Established')
        await resp.prepare(request)
        loop = asyncio.get_event_loop()
        async def relay(reader, writer):
            try:
                while True:
                    data = await loop.run_in_executor(None, reader.read, 4096)
                    if not data:
                        break
                    await loop.run_in_executor(None, writer.write, data)
            except Exception:
                pass
        await asyncio.gather(
            relay(request.transport, remote),
            relay(remote, request.transport)
        )
        return resp

    async def handle_request(self, request):
        # 普通HTTP代理
        try:
            dest_host = request.host
            ip, family = await resolve_host(dest_host)
            if not ip:
                return web.Response(status=502, text='DNS error')
            if family == socket.AF_INET6:
                local_addr = (self.ipv6_pool.get_random(), 0, 0, 0)
            else:
                local_addr = None
            remote = socket.socket(family, socket.SOCK_STREAM)
            if local_addr:
                remote.bind(local_addr)
            await asyncio.get_event_loop().sock_connect(remote, (ip, 80))
            # 组装原始HTTP请求
            req_line = f"{request.method} {request.path_qs} HTTP/1.1\r\n"
            # 过滤掉 hop-by-hop headers
            hop_headers = {b'proxy-connection', b'connection', b'keep-alive', b'te', b'trailers', b'transfer-encoding', b'upgrade'}
            headers = ''.join(f"{k.decode() if isinstance(k, bytes) else k}: {v.decode() if isinstance(v, bytes) else v}\r\n" for k, v in request.raw_headers if k.lower() not in hop_headers)
            # 强制关闭长连接
            headers += "Connection: close\r\n"
            body = await request.read()
            raw = (req_line + headers + "\r\n").encode() + body
            remote.sendall(raw)
            # 逐块转发响应
            async def stream_response():
                while True:
                    chunk = await asyncio.get_event_loop().sock_recv(remote, 4096)
                    if not chunk:
                        break
                    yield chunk
                remote.close()
            return web.Response(body=stream_response())
        except Exception as e:
            return web.Response(status=502, text=f'Proxy error: {e}')

    def run(self):
        app = web.Application()
        app.router.add_route('CONNECT', '/{dest:.*}', self.handle_connect)
        app.router.add_route('*', '/{path:.*}', self.handle_request)
        web.run_app(app, host=self.listen_host, port=self.listen_port)
