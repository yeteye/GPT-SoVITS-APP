# watermark_database.py
import os
import pymysql
from typing import Optional, Dict, List
import logging
import sqlite3


logger = logging.getLogger(__name__)

class WatermarkDatabase:
    """使用 MySQL 的水印数据库管理"""
    def __init__(self, config: Dict = None):
        """
        config: Flask app.config 或包含 MySQL_* 的 dict，
        若为 None，则从环境变量读取。
        """
        if config:
            self.host = config.get('MYSQL_HOST', os.getenv('MYSQL_HOST', 'localhost'))
            self.port = int(config.get('MYSQL_PORT', os.getenv('MYSQL_PORT', 3306)))
            self.user = config.get('MYSQL_USER', os.getenv('MYSQL_USER', 'root'))
            self.password = config.get('MYSQL_PASSWORD', os.getenv('MYSQL_PASSWORD', ''))
            self.db_name = config.get('MYSQL_DATABASE', os.getenv('MYSQL_DATABASE', 'gpt_sovits_db'))
        else:
            self.host = os.getenv('MYSQL_HOST', 'localhost')
            self.port = int(os.getenv('MYSQL_PORT', 3306))
            self.user = os.getenv('MYSQL_USER', 'root')
            self.password = os.getenv('MYSQL_PASSWORD', '')
            self.db_name = os.getenv('MYSQL_DATABASE', 'gpt_sovits_db')

    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    def get_connection(self):
        """建立并返回 PyMySQL 连接，使用 DictCursor 方便返回字典"""
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False
        )

    def generate_watermark_code(self, length: int = 16) -> str:
        """生成水印识别码"""
        import secrets, string
        if length == 8:
            return ''.join(secrets.choice(string.digits) for _ in range(8))
        elif length == 16:
            chars = string.ascii_lowercase + string.digits
            return ''.join(secrets.choice(chars) for _ in range(16))
        elif length == 32:
            return secrets.token_hex(16)
        else:
            chars = string.ascii_lowercase + string.digits
            return ''.join(secrets.choice(chars) for _ in range(length))

    def get_all_watermarks(self) -> list[dict]:
        """获取数据库中所有水印记录，返回字段需包含 watermark_code 和 username"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT watermark_code, username, created_at, usage_count, description FROM watermark")
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    'code': row['watermark_code'],
                    'username': row['username'],
                    'created_at': row['created_at'],
                    'usage_count': row['usage_count'],
                    'description': row['description']
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"获取所有水印失败: {e}", exc_info=True)
            return []
    def find_closest_watermark(self, extracted_code: str) -> Optional[Dict]:
        """在数据库中查找与提取码最相似的一项"""

        def similarity(a, b):
            matches = sum(1 for x, y in zip(a, b) if x == y)
            return matches / len(b) if b else 0.0

        all_codes = self.get_all_watermarks()  # 返回列表，每项为 {'code': ..., 'username': ..., ...}
        best_match = None
        best_score = 0.0

        for item in all_codes:
            score = similarity(extracted_code, item['code'])
            if score > best_score:
                best_score = score
                best_match = item

        if best_score >= 0.5:  # 最低匹配阈值
            best_match['match_score'] = best_score
            return best_match
        return None

    def get_id_by_username(self, username: str) -> Optional[str]:
        """根据用户名获取用户ID，返回 int 或 None"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT id FROM users WHERE username = %s"
                cursor.execute(sql, (username,))
                result = cursor.fetchone()
                return result['id'] if result else None
        finally:
            conn.close()
    def add_watermark(self, username: str, user_id: str, model_id: str, code_length: int, description: str = "", file_info: str = "") -> str:
        """添加水印记录到 MySQL，返回生成的 watermark_code"""
        max_attempts = 10
        for _ in range(max_attempts):
            watermark_code = self.generate_watermark_code(code_length)
            conn = self.get_connection()
            try:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO watermark (username, user_id, model_id, watermark_code, code_length, description, file_info)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (username,user_id, model_id, watermark_code, code_length, description, file_info))
                conn.commit()
                return watermark_code
            except pymysql.err.IntegrityError:
                conn.rollback()
                # 重复 code，重试
                continue
            finally:
                conn.close()
        raise Exception("无法生成唯一的水印码")

    def get_user_by_watermark(self, watermark_code: str) -> Optional[Dict]:
        """根据水印码查找用户信息，返回 dict 或 None"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT username, watermark_code, code_length, created_at, usage_count, description
                    FROM watermark WHERE watermark_code = %s
                """
                cursor.execute(sql, (watermark_code,))
                result = cursor.fetchone()
                return result
        finally:
            conn.close()

    def update_usage(self, watermark_code: str):
        """更新使用统计"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE watermark
                    SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP
                    WHERE watermark_code = %s
                """
                cursor.execute(sql, (watermark_code,))
            conn.commit()
        finally:
            conn.close()

    def log_verification(self, watermark_code: str, filename: str, accuracy: float,
                         extracted_code: str, success: bool, ip_address: str = "",
                         user_agent: str = ""):
        """记录验证日志"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO verification_log 
                    (watermark_code, original_filename, extraction_accuracy, extracted_code, 
                     success, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (
                    watermark_code, filename, accuracy, extracted_code, success, ip_address, user_agent
                ))
            conn.commit()
        finally:
            conn.close()

    def get_user_watermarks(self, username: str) -> List[Dict]:
        """获取指定用户的所有水印记录"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT watermark_code, code_length, created_at, last_used, usage_count, description, file_info
                    FROM watermark
                    WHERE username = %s
                    ORDER BY created_at DESC
                """
                cursor.execute(sql, (username,))
                results = cursor.fetchall()
                return results
        finally:
            conn.close()
