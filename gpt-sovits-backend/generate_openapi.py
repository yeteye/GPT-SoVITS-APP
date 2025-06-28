import os
import sys
import json
import re
import importlib
import inspect
import ast
from typing import Dict, List, Any, Optional
from flask import Flask

# --- 配置区 ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_FACTORY_IMPORT_PATH = "app.create_app"
OUTPUT_FILE = "gpt_sovits_api_complete.json"
API_INFO = {
    "title": "GPT-SoVITS Backend API",
    "description": "GPT-SoVITS 语音克隆和语音合成 API 完整文档",
    "version": "1.0.0",
    "contact": {"name": "API Support", "email": "support@example.com"},
}

# --- 增强的静态代码分析器 ---


class EnhancedApiAnalyzer(ast.NodeVisitor):
    """增强的 AST 分析器，能够提取更多 API 信息"""

    def __init__(self):
        self.query_params = []
        self.json_body_fields = []
        self.path_params = []
        self.form_fields = []
        self.file_uploads = []
        self.decorators = []
        self.docstring = ""
        self._json_variable_name = None
        self._form_data_detected = False
        self._multipart_detected = False

    def visit_FunctionDef(self, node):
        """分析函数定义，提取装饰器和文档字符串"""
        # 提取文档字符串
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, (ast.Str, ast.Constant))
        ):
            self.docstring = (
                node.body[0].value.s
                if hasattr(node.body[0].value, "s")
                else str(node.body[0].value.value)
            )

        # 分析装饰器
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    self.decorators.append(decorator.func.id)
                elif isinstance(decorator.func, ast.Attribute):
                    self.decorators.append(decorator.func.attr)
            elif isinstance(decorator, ast.Name):
                self.decorators.append(decorator.id)

        self.generic_visit(node)

    def visit_Assign(self, node):
        """捕获各种赋值语句"""
        if isinstance(node.value, ast.Call):
            call_node = node.value

            # 捕获 request.get_json()
            if (
                isinstance(call_node.func, ast.Attribute)
                and isinstance(call_node.func.value, ast.Name)
                and call_node.func.value.id == "request"
                and call_node.func.attr == "get_json"
            ):
                if isinstance(node.targets[0], ast.Name):
                    self._json_variable_name = node.targets[0].id

            # 捕获 request.form
            elif (
                isinstance(call_node.func, ast.Attribute)
                and isinstance(call_node.func.value, ast.Name)
                and call_node.func.value.id == "request"
                and call_node.func.attr == "form"
            ):
                self._form_data_detected = True

        self.generic_visit(node)

    def visit_Call(self, node):
        """分析函数调用，提取参数信息"""
        if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            arg_name = None
            default_value = None
            param_type = "string"

            # 提取参数名
            if node.args and isinstance(node.args[0], (ast.Constant, ast.Str)):
                arg_name = (
                    node.args[0].value
                    if hasattr(node.args[0], "value")
                    else node.args[0].s
                )

            # 提取默认值
            if len(node.args) > 1:
                if isinstance(node.args[1], (ast.Constant, ast.Str, ast.Num)):
                    default_value = (
                        node.args[1].value
                        if hasattr(node.args[1], "value")
                        else (
                            node.args[1].s
                            if hasattr(node.args[1], "s")
                            else node.args[1].n
                        )
                    )

            # 检查类型参数
            for kw in node.keywords:
                if kw.arg == "type":
                    if isinstance(kw.value, ast.Name):
                        if kw.value.id == "int":
                            param_type = "integer"
                        elif kw.value.id == "float":
                            param_type = "number"
                        elif kw.value.id == "bool":
                            param_type = "boolean"

            if arg_name:
                # request.args.get() - 查询参数
                if (
                    isinstance(node.func.value, ast.Attribute)
                    and isinstance(node.func.value.value, ast.Name)
                    and node.func.value.value.id == "request"
                    and node.func.value.attr == "args"
                ):

                    param = {
                        "name": arg_name,
                        "in": "query",
                        "required": default_value is None,
                        "description": f"查询参数: {arg_name}",
                        "schema": {"type": param_type},
                    }
                    if default_value is not None:
                        param["schema"]["default"] = default_value

                    if not any(p["name"] == arg_name for p in self.query_params):
                        self.query_params.append(param)

                # request.form.get() - 表单数据
                elif (
                    isinstance(node.func.value, ast.Attribute)
                    and isinstance(node.func.value.value, ast.Name)
                    and node.func.value.value.id == "request"
                    and node.func.value.attr == "form"
                ):

                    field = {
                        "name": arg_name,
                        "type": param_type,
                        "required": default_value is None,
                        "description": f"表单字段: {arg_name}",
                    }
                    if default_value is not None:
                        field["default"] = default_value

                    if not any(f["name"] == arg_name for f in self.form_fields):
                        self.form_fields.append(field)

                # data.get() - JSON 数据
                elif (
                    self._json_variable_name
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == self._json_variable_name
                ):

                    field = {
                        "name": arg_name,
                        "type": param_type,
                        "required": default_value is None,
                        "description": f"JSON 字段: {arg_name}",
                    }
                    if default_value is not None:
                        field["default"] = default_value

                    if not any(f["name"] == arg_name for f in self.json_body_fields):
                        self.json_body_fields.append(field)

        # 检测文件上传
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "request"
            and node.func.attr == "files"
        ):
            self._multipart_detected = True

        self.generic_visit(node)


# --- API 模板定义 ---

API_TEMPLATES = {
    # 认证相关
    "auth": {
        "register": {
            "summary": "用户注册",
            "description": "创建新的用户账户",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["username", "email", "password"],
                            "properties": {
                                "username": {
                                    "type": "string",
                                    "description": "用户名",
                                    "minLength": 3,
                                    "maxLength": 50,
                                },
                                "email": {
                                    "type": "string",
                                    "format": "email",
                                    "description": "邮箱地址",
                                },
                                "password": {
                                    "type": "string",
                                    "description": "密码",
                                    "minLength": 8,
                                },
                            },
                        }
                    }
                },
            },
            "responses": {
                "201": {
                    "description": "注册成功",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/AuthResponse"}
                        }
                    },
                },
                "409": {"description": "用户名或邮箱已存在"},
                "422": {"description": "参数验证失败"},
            },
        },
        "login": {
            "summary": "用户登录",
            "description": "用户身份验证",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["identifier", "password"],
                            "properties": {
                                "identifier": {
                                    "type": "string",
                                    "description": "用户名或邮箱",
                                },
                                "password": {"type": "string", "description": "密码"},
                            },
                        }
                    }
                },
            },
        },
    },
    # TTS 相关
    "tts": {
        "generate": {
            "summary": "生成语音",
            "description": "根据文本生成语音",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["text", "model_id"],
                            "properties": {
                                "text": {
                                    "type": "string",
                                    "description": "要合成的文本",
                                    "maxLength": 200,
                                },
                                "model_id": {
                                    "type": "string",
                                    "description": "语音模型ID",
                                },
                                "emotion": {
                                    "type": "string",
                                    "enum": ["neutral", "happy", "sad", "angry"],
                                    "default": "neutral",
                                },
                                "speed": {
                                    "type": "number",
                                    "minimum": 0.5,
                                    "maximum": 2.0,
                                    "default": 1.0,
                                },
                            },
                        }
                    }
                },
            },
        }
    },
    # 语音克隆相关
    "voice_clone": {
        "upload_sample": {
            "summary": "上传音频样本",
            "description": "上传音频文件用于语音克隆",
            "requestBody": {
                "required": True,
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "required": ["audio_file"],
                            "properties": {
                                "audio_file": {
                                    "type": "string",
                                    "format": "binary",
                                    "description": "音频文件 (WAV, MP3, FLAC)",
                                }
                            },
                        }
                    }
                },
            },
        },
        "start_training": {
            "summary": "开始训练",
            "description": "使用上传的音频样本开始语音克隆训练",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["model_name", "sample_ids"],
                            "properties": {
                                "model_name": {
                                    "type": "string",
                                    "description": "模型名称",
                                },
                                "sample_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 3,
                                    "description": "音频样本ID列表",
                                },
                            },
                        }
                    }
                },
            },
        },
    },
    # 水印相关
    "watermark": {
        "embed": {
            "summary": "嵌入水印",
            "description": "为音频文件嵌入数字水印",
            "requestBody": {
                "required": True,
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "required": ["audio_file"],
                            "properties": {
                                "audio_file": {
                                    "type": "string",
                                    "format": "binary",
                                    "description": "音频文件",
                                },
                                "code_length": {
                                    "type": "string",
                                    "enum": ["8", "16", "32"],
                                    "default": "16",
                                    "description": "水印码长度",
                                },
                                "description": {
                                    "type": "string",
                                    "description": "水印描述",
                                },
                            },
                        }
                    }
                },
            },
        },
        "verify": {
            "summary": "验证水印",
            "description": "验证音频文件中的数字水印",
            "requestBody": {
                "required": True,
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "required": ["audio_file"],
                            "properties": {
                                "audio_file": {
                                    "type": "string",
                                    "format": "binary",
                                    "description": "待验证的音频文件",
                                }
                            },
                        }
                    }
                },
            },
        },
    },
}

# --- 通用响应模式 ---
COMMON_SCHEMAS = {
    "AuthResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "data": {
                "type": "object",
                "properties": {
                    "access_token": {"type": "string"},
                    "refresh_token": {"type": "string"},
                    "user": {"$ref": "#/components/schemas/User"},
                },
            },
        },
    },
    "User": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "username": {"type": "string"},
            "email": {"type": "string"},
            "role": {"type": "integer"},
            "created_at": {"type": "string", "format": "date-time"},
        },
    },
    "TaskResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "data": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["pending", "processing", "completed", "failed"],
                    },
                    "progress": {"type": "integer", "minimum": 0, "maximum": 100},
                },
            },
        },
    },
    "ErrorResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "message": {"type": "string"},
            "error_code": {"type": "string"},
        },
    },
    "PaginationResponse": {
        "type": "object",
        "properties": {
            "page": {"type": "integer"},
            "per_page": {"type": "integer"},
            "total": {"type": "integer"},
            "pages": {"type": "integer"},
            "has_prev": {"type": "boolean"},
            "has_next": {"type": "boolean"},
        },
    },
}


def enhance_operation_with_template(
    operation: Dict, endpoint: str, method: str
) -> Dict:
    """使用模板增强操作信息"""
    # 提取蓝图和操作名
    blueprint = endpoint.split(".")[0] if "." in endpoint else "default"
    operation_name = endpoint.split(".")[-1] if "." in endpoint else endpoint

    # 查找匹配的模板
    if blueprint in API_TEMPLATES and operation_name in API_TEMPLATES[blueprint]:
        template = API_TEMPLATES[blueprint][operation_name]

        # 合并模板信息
        if "summary" in template:
            operation["summary"] = template["summary"]
        if "description" in template:
            operation["description"] = template["description"]
        if "requestBody" in template:
            operation["requestBody"] = template["requestBody"]
        if "responses" in template:
            operation["responses"] = {
                **operation.get("responses", {}),
                **template["responses"],
            }

    return operation


def analyze_view_function_enhanced(view_func):
    """增强的视图函数分析"""
    try:
        source_code = inspect.getsource(view_func)
        tree = ast.parse(source_code)
        analyzer = EnhancedApiAnalyzer()
        analyzer.visit(tree)
        return analyzer
    except (TypeError, OSError):
        return EnhancedApiAnalyzer()  # 返回空分析器


def generate_enhanced_openapi_spec(app: Flask) -> Dict[str, Any]:
    """生成增强的 OpenAPI 规范"""
    spec = {
        "openapi": "3.0.3",
        "info": API_INFO,
        "servers": [
            {"url": "http://localhost:5000", "description": "开发服务器"},
            {"url": "https://api.example.com", "description": "生产服务器"},
        ],
        "paths": {},
        "components": {
            "schemas": COMMON_SCHEMAS,
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT 访问令牌",
                }
            },
        },
        "security": [{"BearerAuth": []}],
    }

    paths = spec["paths"]
    rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)

    for rule in rules:
        if rule.endpoint == "static" or not rule.methods:
            continue

        methods = sorted([m for m in rule.methods if m not in ("OPTIONS", "HEAD")])
        if not methods:
            continue

        path_url = re.sub(r"<(\w+:)?(\w+)>", r"{\2}", rule.rule)
        if path_url not in paths:
            paths[path_url] = {}

        view_func = app.view_functions.get(rule.endpoint)
        if not view_func:
            continue

        # 增强分析
        analyzer = analyze_view_function_enhanced(view_func)

        # 提取路径参数
        path_params = []
        for name in re.findall(r"<(?:\w+:)?(\w+)>", rule.rule):
            path_params.append(
                {
                    "name": name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                    "description": f"路径参数: {name}",
                }
            )

        for method in methods:
            method_lower = method.lower()

            # 基础操作信息
            operation = {
                "summary": (
                    analyzer.docstring.split("\n")[0]
                    if analyzer.docstring
                    else view_func.__name__.replace("_", " ").title()
                ),
                "description": (
                    analyzer.docstring if analyzer.docstring else f"{method} {path_url}"
                ),
                "tags": [
                    rule.endpoint.split(".")[0] if "." in rule.endpoint else "default"
                ],
                "operationId": f"{method_lower}_{rule.endpoint.replace('.', '_')}",
                "parameters": path_params + analyzer.query_params,
                "responses": {
                    "200": {"description": "操作成功"},
                    "401": {
                        "description": "未授权",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        },
                    },
                    "500": {
                        "description": "服务器错误",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        },
                    },
                },
            }

            # 处理请求体
            if analyzer.json_body_fields:
                properties = {}
                required = []
                for field in analyzer.json_body_fields:
                    properties[field["name"]] = {
                        "type": field["type"],
                        "description": field["description"],
                    }
                    if field.get("required", False):
                        required.append(field["name"])
                    if "default" in field:
                        properties[field["name"]]["default"] = field["default"]

                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": properties,
                                "required": required if required else None,
                            }
                        }
                    },
                }

            elif analyzer.form_fields or analyzer._multipart_detected:
                properties = {}
                required = []

                # 处理表单字段
                for field in analyzer.form_fields:
                    properties[field["name"]] = {
                        "type": field["type"],
                        "description": field["description"],
                    }
                    if field.get("required", False):
                        required.append(field["name"])

                # 如果检测到文件上传
                if analyzer._multipart_detected:
                    if "audio_file" not in properties:
                        properties["audio_file"] = {
                            "type": "string",
                            "format": "binary",
                            "description": "上传的文件",
                        }
                        required.append("audio_file")

                content_type = (
                    "multipart/form-data"
                    if analyzer._multipart_detected
                    else "application/x-www-form-urlencoded"
                )
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        content_type: {
                            "schema": {
                                "type": "object",
                                "properties": properties,
                                "required": required if required else None,
                            }
                        }
                    },
                }

            # 使用模板增强
            operation = enhance_operation_with_template(
                operation, rule.endpoint, method
            )

            # 添加安全要求（除了公开端点）
            if not any(
                decorator in analyzer.decorators for decorator in ["public", "no_auth"]
            ):
                operation["security"] = [{"BearerAuth": []}]

            paths[path_url][method_lower] = operation

    return spec


def main():
    """主执行函数"""
    print("🚀 开始生成完整的 GPT-SoVITS API 文档...")

    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    print(f"📦 正在从 '{APP_FACTORY_IMPORT_PATH}' 加载 Flask app...")
    create_app = importlib.import_module("app").create_app

    try:
        app = create_app("testing")
        print("✅ Flask App 加载成功")
    except Exception as e:
        print(f"❌ 错误: 调用 create_app() 失败。详细错误: {e}")
        sys.exit(1)

    print("🔍 开始扫描路由并分析代码...")
    with app.app_context():
        openapi_spec = generate_enhanced_openapi_spec(app)

    # 统计信息
    total_paths = len(openapi_spec["paths"])
    total_operations = sum(len(methods) for methods in openapi_spec["paths"].values())

    output_path = os.path.join(PROJECT_ROOT, OUTPUT_FILE)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(openapi_spec, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 60)
        print("🎉 完整 API 文档生成成功!")
        print(f"📄 文件路径: {output_path}")
        print(f"📊 统计信息:")
        print(f"   - 路径数量: {total_paths}")
        print(f"   - 操作数量: {total_operations}")
        print(f"   - 组件模式: {len(openapi_spec['components']['schemas'])}")
        print("\n📋 导入到 Apifox 的步骤:")
        print("   1. 打开 Apifox")
        print("   2. 创建新项目或选择现有项目")
        print("   3. 点击 '导入' -> '导入 OpenAPI'")
        print(f"   4. 选择生成的文件: {OUTPUT_FILE}")
        print("   5. 确认导入设置并开始导入")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误：写入文件 {output_path} 失败: {e}")


if __name__ == "__main__":
    main()
