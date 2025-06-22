import os
import sys
import json
import re
import importlib
import inspect
import ast
from flask import Flask

# --- 配置区 ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_FACTORY_IMPORT_PATH = "app.create_app"  # 根据你的项目结构调整
OUTPUT_FILE = "apifox_openapi_auto.json"
API_INFO = {
    "title": "My Flask Project API (Auto-generated)",
    "description": "通过静态代码分析自动生成的 API 文档，可导入 Apifox",
    "version": "1.0.0",
}

# --- 静态代码分析器 ---


class ApiAnalyzer(ast.NodeVisitor):
    """
    一个 AST 节点访问者，用于从视图函数代码中提取 API 信息。
    """

    def __init__(self):
        self.query_params = []
        self.json_body_fields = []
        self._json_variable_name = None

    def visit_Assign(self, node):
        """捕获 'data = request.get_json()' 这样的赋值语句"""
        # 检查是否是函数调用赋值
        if isinstance(node.value, ast.Call):
            call_node = node.value
            # 检查是否是 request.get_json()
            if (
                isinstance(call_node.func, ast.Attribute)
                and isinstance(call_node.func.value, ast.Name)
                and call_node.func.value.id == "request"
                and call_node.func.attr == "get_json"
            ):
                # 记录被赋值的变量名
                if isinstance(node.targets[0], ast.Name):
                    self._json_variable_name = node.targets[0].id
        self.generic_visit(node)

    def visit_Call(self, node):
        """捕获 request.args.get() 和 data.get() 这样的函数调用"""
        # 检查是否是 .get() 方法调用
        if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
            arg_name = None
            # 提取参数名 (通常是第一个参数)
            if node.args and isinstance(
                node.args[0], (ast.Constant, ast.Str)
            ):  # Python 3.8+ uses Constant
                arg_name = node.args[0].value

            if arg_name:
                # 检查是否是 request.args.get()
                if (
                    isinstance(node.func.value, ast.Attribute)
                    and isinstance(node.func.value.value, ast.Name)
                    and node.func.value.value.id == "request"
                    and node.func.value.attr == "args"
                ):

                    param = {
                        "name": arg_name,
                        "in": "query",
                        "required": False,
                        "description": f"查询参数: {arg_name}",
                    }

                    # 尝试推断类型
                    param_type = "string"
                    for kw in node.keywords:
                        if kw.arg == "type":
                            if isinstance(kw.value, ast.Name) and kw.value.id == "int":
                                param_type = "integer"
                            elif (
                                isinstance(kw.value, ast.Name)
                                and kw.value.id == "float"
                            ):
                                param_type = "number"
                            elif (
                                isinstance(kw.value, ast.Name) and kw.value.id == "bool"
                            ):
                                param_type = "boolean"

                    param["schema"] = {"type": param_type}
                    if arg_name not in [p["name"] for p in self.query_params]:
                        self.query_params.append(param)

                # 检查是否是之前捕获到的 JSON 变量的 .get()
                elif (
                    self._json_variable_name
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == self._json_variable_name
                ):

                    field = {
                        "name": arg_name,
                        "type": "string",
                        "description": f"请求体字段: {arg_name}",
                    }
                    if arg_name not in [f["name"] for f in self.json_body_fields]:
                        self.json_body_fields.append(field)

        self.generic_visit(node)


# --- 脚本核心代码 ---


def import_app_factory(import_path: str):
    """动态导入 app 工厂函数"""
    try:
        module_path, func_name = import_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, func_name)
    except (ImportError, AttributeError) as e:
        print(f"错误：无法导入 app 工厂函数 '{import_path}'. 详细错误: {e}")
        sys.exit(1)


def analyze_view_function(view_func):
    """分析视图函数源代码"""
    try:
        source_code = inspect.getsource(view_func)
        tree = ast.parse(source_code)
        analyzer = ApiAnalyzer()
        analyzer.visit(tree)
        return analyzer.query_params, analyzer.json_body_fields
    except (TypeError, OSError):
        # 无法获取源代码 (例如，C实现的内置函数)
        return [], []


def generate_openapi_spec(app: Flask):
    """遍历 Flask app 的路由规则并生成 OpenAPI 规范"""
    spec = {
        "openapi": "3.0.3",
        "info": API_INFO,
        "servers": [{"url": "/", "description": "本地服务器"}],
        "paths": {},
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

        view_func = app.view_functions[rule.endpoint]

        # 通过静态分析获取参数和请求体
        query_params, json_fields = analyze_view_function(view_func)

        # 从路由规则中提取路径参数
        path_params = [
            {
                "name": name,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": f"路径参数: {name}",
            }
            for name in re.findall(r"<(?:\w+:)?(\w+)>", rule.rule)
        ]

        for method in methods:
            method_lower = method.lower()

            # 从函数名生成摘要
            op_summary = view_func.__name__.replace("_", " ").title()
            # 从蓝图名生成标签
            tag = rule.endpoint.split(".")[0] if "." in rule.endpoint else "default"

            operation = {
                "summary": op_summary,
                "tags": [tag],
                "operationId": f"{method.lower()}_{rule.endpoint}",
                "parameters": path_params + query_params,
                "responses": {"200": {"description": "操作成功"}},
            }

            # 如果分析出 JSON 字段，则构建 requestBody
            if json_fields:
                properties = {
                    field["name"]: {
                        "type": field["type"],
                        "description": field["description"],
                    }
                    for field in json_fields
                }
                operation["requestBody"] = {
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "properties": properties}
                        }
                    }
                }

            paths[path_url][method_lower] = operation
    return spec


def main():
    """主执行函数"""
    print("开始通过静态代码分析生成 API 文档...")
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

    print(f"正在从 '{APP_FACTORY_IMPORT_PATH}' 加载 Flask app...")
    create_app = import_app_factory(APP_FACTORY_IMPORT_PATH)

    try:
        app = create_app("testing")
    except TypeError:
        try:
            app = create_app()
        except Exception as e:
            print(f"错误: 调用 create_app() 失败。详细错误: {e}")
            sys.exit(1)

    print("Flask App 加载成功，开始扫描路由并分析代码...")
    with app.app_context():
        openapi_spec = generate_openapi_spec(app)

    output_path = os.path.join(PROJECT_ROOT, OUTPUT_FILE)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(openapi_spec, f, ensure_ascii=False, indent=2)
        print("\n" + "=" * 50)
        print(f"🎉 全自动 API 文档生成成功!")
        print(f"   文件已保存至: {output_path}")
        print("   注意：此文件基于代码推断，可能信息不全。")
        print("=" * 50)
    except Exception as e:
        print(f"\n错误：写入文件 {output_path} 失败: {e}")


if __name__ == "__main__":
    main()
