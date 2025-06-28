# ./gpt-sovits-backend/tests/test_auth.py
import pytest
from app.models import User
from app.extensions import db


class TestAuth:
    """认证相关测试"""

    def test_user_registration(self, client):
        """测试用户注册"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "Password123!",
            },
        )

        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert "access_token" in data["data"]

        # 验证用户已创建
        user = User.query.filter_by(username="newuser").first()
        assert user is not None
        assert user.email == "newuser@example.com"

    def test_user_registration_duplicate_username(self, client, app, test_user):
        """测试重复用户名注册"""

        # 尝试用相同用户名注册
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "another@example.com",
                "password": "Password123!",
            },
        )

        assert response.status_code == 409
        data = response.get_json()
        assert data["success"] is False
        assert "already exists" in data["message"]

    def test_user_login_success(self, client, app, test_user):
        """测试成功登录"""
        with app.app_context():
            # 创建测试用户
            user = test_user

        response = client.post(
            "/api/auth/login",
            json={"identifier": user.username, "password": "testpassword123"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    def test_user_login_invalid_credentials(self, client):
        """测试无效凭据登录"""
        response = client.post(
            "/api/auth/login",
            json={"identifier": "nonexistent", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False

    def test_protected_route_without_token(self, client):
        """测试无token访问受保护路由"""
        response = client.get("/api/user/profile")
        assert response.status_code == 401

    def test_protected_route_with_token(self, client, app, test_user):
        """测试有token访问受保护路由"""
        with app.app_context():
            user = test_user

            # 登录获取token
            response = client.post(
                "/api/auth/login",
                json={"identifier": user.username, "password": "testpassword123"},
            )

            assert response.status_code == 200
            data = response.get_json()
            token = data["data"]["access_token"]

            # 使用token访问受保护路由
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/user/profile", headers=headers)
            assert response.status_code == 200

    def test_logout(self, client, app, test_user):
        """测试登出"""
        with app.app_context():
            user = test_user

            # 登录获取token
            response = client.post(
                "/api/auth/login",
                json={"identifier": user.username, "password": "testpassword123"},
            )

            assert response.status_code == 200
            data = response.get_json()
            token = data["data"]["access_token"]

            # 登出
            headers = {"Authorization": f"Bearer {token}"}
            response = client.post("/api/auth/logout", headers=headers)
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True

    def test_password_validation(self, client):
        """测试密码验证"""
        # 弱密码
        response = client.post(
            "/api/auth/register",
            json={
                "username": "weakuser",
                "email": "weak@example.com",
                "password": "123",
            },
        )

        assert response.status_code == 422

        # 没有大写字母
        response = client.post(
            "/api/auth/register",
            json={
                "username": "weakuser2",
                "email": "weak2@example.com",
                "password": "password123",
            },
        )

        assert response.status_code == 422

    def test_email_validation(self, client):
        """测试邮箱验证"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "Password123!",
            },
        )

        assert response.status_code == 422
        data = response.get_json()
        assert "email" in data["message"].lower()

    def test_change_password(self, client, app, test_user):
        """测试修改密码"""
        with app.app_context():
            user = test_user

            # 登录获取token
            response = client.post(
                "/api/auth/login",
                json={"identifier": user.username, "password": "testpassword123"},
            )

            assert response.status_code == 200
            data = response.get_json()
            token = data["data"]["access_token"]

            # 修改密码
            headers = {"Authorization": f"Bearer {token}"}
            response = client.post(
                "/api/auth/change-password",
                headers=headers,
                json={
                    "current_password": "testpassword123",
                    "new_password": "NewPassword123!",
                },
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
