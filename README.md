# IPv6 Proxy Pool

## 项目简介

本项目是一个支持多出口 IPv6 的高性能代理池，支持 HTTP 和 SOCKS5 协议，适用于爬虫、测试、网络研究等多场景。每次代理请求可随机使用本机不同的全局 IPv6 地址作为出口，支持用户名/密码认证。

---

## 功能特性

- **双协议支持**：HTTP 代理、SOCKS5 代理（二选一启动）
- **IPv6 池管理**：自动检测本机所有全局 IPv6 地址，随机选取作为出口
- **智能路由**：访问 IPv4 目标时用默认出口，访问 IPv6 目标时用随机 IPv6 出口
- **认证机制**：SOCKS5 支持用户名/密码认证
- **DNS 策略**：优先解析 AAAA 记录，无则降级 A 记录
- **高并发**：基于 asyncio 实现，支持大量并发连接
- **日志简洁**：仅保留关键操作和异常日志

---

## 安装与依赖

建议使用 [uv](https://github.com/astral-sh/uv) 或 pip 安装依赖：

```bash
uv pip install -r requirements.txt
# 或
pip install -r requirements.txt
```

依赖主要包括：aiohttp、PySocks、dnspython、netifaces、requests、socks

---

## 启动方式

### 启动 SOCKS5 代理（默认，支持认证）

```bash
python3 main.py --mode socks5 --port 43222 --socks5-user <用户名> --socks5-pass <密码>
# 例如
python3 main.py --mode socks5 --port 43222 --socks5-user ubuntu --socks5-pass wobure
```

### 启动 HTTP 代理

```bash
python3 main.py --mode http --port 43222
```

### 后台运行

```bash
nohup python3 main.py --mode socks5 --port 43222 > proxy.log 2>&1 &
```

---

## 代理使用示例

### curl 测试 SOCKS5 代理

```bash
curl -x socks5h://<用户名>:<密码>@127.0.0.1:43222 http://6.ipw.cn/
```

### curl 测试 HTTP 代理

```bash
curl -x http://127.0.0.1:43222 http://6.ipw.cn/
```

### Python 脚本测试

```bash
python3 test_proxy.py http://127.0.0.1:43222 socks5h://<用户名>:<密码>@127.0.0.1:43222
```

---

## 参数说明

| 参数            | 说明                       | 默认值      |
|-----------------|----------------------------|-------------|
| --mode          | 启动模式 http/socks5        | socks5      |
| --port          | 监听端口                   | 43222       |
| --cidr          | IPv6 CIDR 过滤             | 无          |
| --socks5-user   | SOCKS5 认证用户名          | 无          |
| --socks5-pass   | SOCKS5 认证密码            | 无          |

---

## IPv6 池随机选取规则

- 启动时自动检测本机所有全局 IPv6 地址，组成池子
- 每次访问 IPv6 目标时，**随机选取**一个 IPv6 地址作为出口
- 目标为 IPv4 时，使用系统默认出口

---

## 常见问题

- **IPv6 pool 为空？**
  - 请确保本机网卡已分配全局 IPv6 地址（非 fe80::/link-local，非 ::1/回环）
  - 可用 `ip -6 addr` 检查
- **curl 返回空？**
  - 代理链路通但目标站点无响应，或出口 IPv6 被限流/封禁
  - 检查日志，确认出口 IPv6 是否被正确选取
- **认证失败？**
  - 检查用户名/密码参数是否正确

---

## 适用场景

- 多 IP 代理出口、爬虫防封、IPv6 兼容性测试、网络研究等

---

## 许可证

MIT License