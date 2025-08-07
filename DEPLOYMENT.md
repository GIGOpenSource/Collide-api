# Collide User Service 部署指南

本文档提供了 Collide User Service 微服务的详细部署指南，涵盖本地开发、测试环境和生产环境。

## 📋 部署前准备

### 1. 环境要求

- **Python**: 3.11+
- **MySQL**: 8.0+
- **Nacos**: 2.2.3+
- **内存**: 最少 512MB
- **磁盘**: 最少 1GB

### 2. 配置文件准备

```bash
# 复制配置文件模板
cp config.example.env .env

# 编辑配置文件
vim .env
```

### 3. 必要的配置项

```env
# 数据库连接（必须）
DATABASE_URL=mysql+pymysql://用户名:密码@主机:端口/数据库名

# Nacos服务器（必须）
NACOS_SERVER=127.0.0.1:8848

# 服务名称（必须）
SERVICE_NAME=collide-user-service
```

## 🚀 部署方式

### 方式一：本地开发部署

#### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2. 数据库初始化

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE collide CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 执行SQL脚本
mysql -u root -p collide < sql/users-simple.sql
```

#### 3. 启动服务

```bash
# 启动Nacos（可选）
# 下载并启动Nacos Server

# 启动用户服务
python start.py
```

#### 4. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# API文档
open http://localhost:8000/docs
```

### 方式二：Docker部署

#### 1. 使用Docker Compose（推荐）

```bash
# 启动完整环境（包含MySQL、Nacos）
docker-compose -f docker-compose.example.yml up -d

# 查看服务状态
docker-compose -f docker-compose.example.yml ps

# 查看日志
docker-compose -f docker-compose.example.yml logs -f collide-user-service
```

#### 2. 单独Docker容器

```bash
# 构建镜像
docker build -t collide-user-service:latest .

# 运行容器
docker run -d \
  --name collide-user-service \
  -p 8000:8000 \
  -e DATABASE_URL="mysql+pymysql://root:password@host.docker.internal:3306/collide" \
  -e NACOS_SERVER="host.docker.internal:8848" \
  collide-user-service:latest
```

### 方式三：生产环境部署

#### 1. 系统服务部署

```bash
# 创建系统用户
sudo useradd -r -s /bin/false collide

# 创建目录
sudo mkdir -p /opt/collide-user-service
sudo chown collide:collide /opt/collide-user-service

# 部署代码
sudo cp -r . /opt/collide-user-service/
sudo chown -R collide:collide /opt/collide-user-service

# 创建systemd服务文件
sudo tee /etc/systemd/system/collide-user-service.service > /dev/null <<EOF
[Unit]
Description=Collide User Service
After=network.target mysql.service

[Service]
Type=simple
User=collide
WorkingDirectory=/opt/collide-user-service
Environment=PYTHONPATH=/opt/collide-user-service
ExecStart=/opt/collide-user-service/venv/bin/python start.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable collide-user-service
sudo systemctl start collide-user-service
```

#### 2. Kubernetes部署

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: collide-user-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: collide-user-service
  template:
    metadata:
      labels:
        app: collide-user-service
    spec:
      containers:
      - name: collide-user-service
        image: collide-user-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: collide-secrets
              key: database-url
        - name: NACOS_SERVER
          value: "nacos.default.svc.cluster.local:8848"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: collide-user-service
spec:
  selector:
    app: collide-user-service
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

## 🔧 配置优化

### 1. 数据库连接池配置

```python
# app/database/connection.py
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=20,          # 连接池大小
    max_overflow=40,       # 最大溢出连接
    pool_pre_ping=True,    # 连接前ping
    pool_recycle=300,      # 连接回收时间
    echo=settings.debug
)
```

### 2. Nacos配置优化

```env
# 生产环境建议配置
NACOS_SERVER=nacos1:8848,nacos2:8848,nacos3:8848  # 集群地址
NACOS_NAMESPACE=prod                               # 生产命名空间
SERVICE_WEIGHT=1.0                                 # 权重配置
SERVICE_EPHEMERAL=false                            # 持久化实例
```

### 3. 日志配置

```python
# 生产环境日志配置
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/collide-user-service.log'),
        logging.StreamHandler()
    ]
)
```

## 🔍 监控和运维

### 1. 健康检查端点

- **基础健康检查**: `GET /health`
- **详细健康检查**: `GET /actuator/health`
- **服务信息**: `GET /`

### 2. 监控指标

```bash
# 服务状态监控
curl -s http://localhost:8000/health | jq

# Nacos服务列表
curl -s "http://nacos:8848/nacos/v1/ns/instance/list?serviceName=collide-user-service" | jq

# 数据库连接检查
mysql -h localhost -u root -p -e "SHOW PROCESSLIST;"
```

### 3. 日志监控

```bash
# 查看应用日志
tail -f /var/log/collide-user-service.log

# 查看错误日志
grep "ERROR" /var/log/collide-user-service.log

# 查看访问统计
grep "GET\|POST" /var/log/collide-user-service.log | wc -l
```

## 🚨 故障排除

### 1. 常见问题

#### 服务启动失败
```bash
# 检查端口占用
netstat -tlnp | grep 8000

# 检查配置文件
python -c "from app.common.config import settings; print(settings.dict())"
```

#### 数据库连接失败
```bash
# 测试数据库连接
mysql -h localhost -u root -p collide -e "SELECT 1;"

# 检查数据库用户权限
mysql -u root -p -e "SHOW GRANTS FOR 'root'@'%';"
```

#### Nacos注册失败
```bash
# 检查Nacos服务状态
curl -f http://localhost:8848/nacos/v1/console/health

# 查看服务注册列表
curl "http://localhost:8848/nacos/v1/ns/service/list?pageNo=1&pageSize=10"
```

### 2. 性能调优

#### 数据库优化
```sql
-- 添加索引
ALTER TABLE t_user ADD INDEX idx_username_status (username, status);
ALTER TABLE t_user_wallet ADD INDEX idx_user_coin (user_id, coin_balance);

-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';
```

#### 应用优化
```python
# 连接池调优
pool_size = 20 + (并发用户数 / 10)
max_overflow = pool_size * 2

# 缓存配置
REDIS_URL = "redis://localhost:6379/0"
CACHE_TTL = 300  # 5分钟缓存
```

## 📈 扩容指南

### 1. 水平扩容

```bash
# Docker扩容
docker-compose -f docker-compose.example.yml up -d --scale collide-user-service=3

# Kubernetes扩容
kubectl scale deployment collide-user-service --replicas=5
```

### 2. 垂直扩容

```yaml
# 增加资源限制
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## 📞 技术支持

如遇到部署问题，请按以下步骤排查：

1. 检查配置文件是否正确
2. 验证网络连接和端口状态
3. 查看应用日志和错误信息
4. 确认依赖服务（MySQL、Nacos）状态
5. 联系技术支持团队

---

*本部署指南会持续更新，请关注最新版本。*