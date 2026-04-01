# clihub-web — 工程指南

## 定位

clihub.cc 网站 = Landing Page + Schema Registry API

## 架构

- FastAPI + Jinja2 + 静态 JSON 文件
- 端口: 18010 / nginx 反代 + SSL
- 服务器: 47.76.201.162

## 路由

| 路径 | 说明 |
|------|------|
| `GET /` | Landing page |
| `GET /api/providers` | Provider 列表 + 工具数 |
| `GET /api/schemas` | 全量 schema (cli-hub refresh 用) |
| `GET /api/schemas/{name}` | 单个 provider schema |
| `GET /api/version` | Schema 版本号 |
| `GET /health` | 健康检查 |

## 新增 Provider

1. 在 `schemas/` 下创建 `<name>.json`
2. 在 `schemas/providers.json` 中添加元数据
3. `bash deploy.sh` 部署

## 部署

```bash
bash deploy.sh          # 全量部署（rsync + uv sync + systemctl restart）
bash deploy.sh restart   # 仅重启
bash deploy.sh status    # 查看状态
bash deploy.sh logs      # 查看日志
bash deploy.sh nginx     # 配置 nginx（首次）
bash deploy.sh ssl       # 申请 SSL 证书（首次）
bash deploy.sh ssh       # SSH 登录服务器
```
