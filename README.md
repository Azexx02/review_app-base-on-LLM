# review_app-base-on-LLM
这是一个基于llm的复习webapp，部署到服务器，配置好环境就可以从浏览器访问了
## Docker Compose 配置

以下是运行本项目的Docker Compose配置：

```yaml
version: '3'
services:
  web:
    build: .
    ports:
      - "5000:5000"  # 服务器5000端口映射到容器
    environment:
      - SECRET_KEY=你的随机密钥（生产环境务必更换）
      - DEBUG=False
      - MYSQL_USER=MySQL用户名
      - MYSQL_PASSWORD=你的MySQL密码
      - MYSQL_HOST=MySQL主机IP/域名
      - MYSQL_PORT=3306  # 端口（默认3306可省略）
      - MYSQL_DB=review_app 
      - LLM_API_KEY=你的deepseek apikey
    restart: always
    volumes:
      - ./static:/app/static  # 挂载静态文件目录
      - ./tmp:/tmp  # 挂载临时目录（存放PDF）
