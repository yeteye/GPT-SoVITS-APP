import secrets
import os

ENV_FILE = '.env.key'
KEY_LENGTH = 32  # 32 bytes => 256 bits

def generate_secret():
    return secrets.token_hex(KEY_LENGTH)  # 64 hex chars

def update_env_file(secret_key, jwt_secret_key):
    lines = []
    # 如果 .env 存在，先读取其内容
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r') as f:
            lines = f.readlines()

    # 用于更新或添加 key
    def upsert_line(key, value):
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}\n")

    upsert_line('SECRET_KEY', secret_key)
    upsert_line('JWT_SECRET_KEY', jwt_secret_key)

    with open(ENV_FILE, 'w') as f:
        f.writelines(lines)

    print(f"✅ .env 文件已更新：\nSECRET_KEY={secret_key}\nJWT_SECRET_KEY={jwt_secret_key}")

def main():
    secret_key = generate_secret()
    jwt_secret_key = generate_secret()
    update_env_file(secret_key, jwt_secret_key)

if __name__ == '__main__':
    main()
