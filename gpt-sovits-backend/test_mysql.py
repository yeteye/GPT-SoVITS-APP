import os
import sys
from dotenv import load_dotenv
import pymysql

# 加载环境变量
load_dotenv()

# 获取数据库URL
database_url = os.getenv("DATABASE_URL")
print(f"数据库URL: {database_url}")

# 解析连接参数
if database_url and database_url.startswith("mysql+pymysql://"):
    # 移除 mysql+pymysql:// 前缀
    url = database_url.replace("mysql+pymysql://", "")

    # 分离用户信息和主机信息
    if "@" in url:
        user_info, host_info = url.split("@", 1)

        # 解析用户名和密码
        if ":" in user_info:
            username, password = user_info.split(":", 1)
        else:
            username = user_info
            password = ""

        # 解析主机、端口和数据库
        if "/" in host_info:
            host_port, db_info = host_info.split("/", 1)
            database = db_info.split("?")[0]  # 移除查询参数
        else:
            host_port = host_info
            database = ""

        if ":" in host_port:
            host, port = host_port.split(":", 1)
            port = int(port)
        else:
            host = host_port
            port = 3306

        print(f"解析结果:")
        print(f"  用户名: {username}")
        print(f"  密码: {'*' * len(password)}")
        print(f"  主机: {host}")
        print(f"  端口: {port}")
        print(f"  数据库: {database}")

        # 测试连接
        try:
            print("\n正在测试数据库连接...")
            connection = pymysql.connect(
                host=host,
                user=username,
                password=password,
                port=port,
                charset="utf8mb4",
            )
            print("✓ MySQL服务器连接成功！")

            # 测试数据库
            if database:
                cursor = connection.cursor()
                try:
                    cursor.execute(f"USE {database}")
                    print(f"✓ 数据库 {database} 连接成功！")
                except pymysql.err.ProgrammingError as e:
                    if "Unknown database" in str(e):
                        print(f"✗ 数据库 {database} 不存在，正在创建...")
                        cursor.execute(
                            f"CREATE DATABASE {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                        )
                        print(f"✓ 数据库 {database} 创建成功！")
                    else:
                        print(f"✗ 数据库错误: {e}")
                finally:
                    cursor.close()

            connection.close()
            print("✓ 所有测试通过！")

        except Exception as e:
            print(f"✗ 连接失败: {e}")
            print(f"错误类型: {type(e).__name__}")

            # 提供具体的解决建议
            if "Access denied" in str(e):
                print("\n建议:")
                print("1. 检查用户名和密码是否正确")
                print("2. 检查.env文件中是否有特殊字符需要编码")
                print("3. 尝试在MySQL中创建专门的用户")
            elif "Unknown database" in str(e):
                print("\n建议:")
                print("1. 先手动创建数据库")
                print("2. 或者修改代码先连接MySQL服务器再创建数据库")
    else:
        print("✗ 无法解析数据库URL格式")
else:
    print("✗ 未找到有效的数据库URL配置")
