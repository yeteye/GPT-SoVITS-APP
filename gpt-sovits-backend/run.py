#!/usr/bin/env python3

import os
import sys
import click
from flask.cli import with_appcontext
from app import create_app
from app.extensions import db
from app.models import (
    User,
    VoiceModel,
    VoiceCloneTask,
    TTSTask,
    AuditLog,
    UserUpload,
    Tag,
    AuthToken,
)

# 创建应用实例
app = create_app()


@app.shell_context_processor
def make_shell_context():
    """为shell命令提供上下文"""
    return {
        "db": db,
        "User": User,
        "VoiceModel": VoiceModel,
        "VoiceCloneTask": VoiceCloneTask,
        "TTSTask": TTSTask,
        "AuditLog": AuditLog,
        "UserUpload": UserUpload,
        "Tag": Tag,
        "AuthToken": AuthToken,
    }


@app.cli.command()
@click.option("--drop", is_flag=True, help="Drop all tables before creating")
def init_db(drop):
    """初始化数据库"""
    if drop:
        click.echo("Dropping all tables...")
        db.drop_all()

    click.echo("Creating database tables...")
    db.create_all()

    # 创建上传目录
    upload_dirs = [
        "audio_samples",
        "models/official",
        "models/user_trained",
        "generated",
        "temp",
        "images",
        "documents",
    ]

    for dir_name in upload_dirs:
        dir_path = os.path.join(app.config["UPLOAD_FOLDER"], dir_name)
        os.makedirs(dir_path, exist_ok=True)
        click.echo(f"Created directory: {dir_path}")

    click.echo("Database initialized successfully.")


@app.cli.command()
def create_admin():
    """创建管理员用户"""
    click.echo("Creating admin user...")

    username = click.prompt("Admin username", default="admin")
    email = click.prompt("Admin email")
    password = click.prompt("Admin password", hide_input=True, confirmation_prompt=True)

    # 检查用户是否已存在
    if User.query.filter_by(username=username).first():
        click.echo(f'Error: Username "{username}" already exists.')
        return

    if User.query.filter_by(email=email).first():
        click.echo(f'Error: Email "{email}" already exists.')
        return

    # 创建管理员用户
    admin = User(
        username=username,
        email=email,
        role=2,  # 管理员角色
        is_active=True,
        is_verified=True,
    )
    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()

    click.echo(f'Admin user "{username}" created successfully.')


@app.cli.command()
def create_sample_models():
    """创建示例模型"""
    click.echo("Creating sample models and tags...")

    # 创建标签
    sample_tags = [
        {"name": "女声", "description": "女性声音", "color": "#ff69b4"},
        {"name": "男声", "description": "男性声音", "color": "#4169e1"},
        {"name": "青年", "description": "年轻声音", "color": "#32cd32"},
        {"name": "中年", "description": "中年声音", "color": "#ffa500"},
        {"name": "老年", "description": "年长声音", "color": "#8b4513"},
        {"name": "温柔", "description": "温柔的声音", "color": "#ffc0cb"},
        {"name": "磁性", "description": "磁性的声音", "color": "#8b4513"},
        {"name": "甜美", "description": "甜美的声音", "color": "#ffb6c1"},
        {"name": "沉稳", "description": "沉稳的声音", "color": "#696969"},
        {"name": "活力", "description": "充满活力的声音", "color": "#ff6347"},
        {"name": "专业", "description": "专业播音声音", "color": "#4682b4"},
        {"name": "官方", "description": "官方提供的模型", "color": "#gold"},
    ]

    created_tags = {}
    for tag_data in sample_tags:
        existing_tag = Tag.query.filter_by(name=tag_data["name"]).first()
        if not existing_tag:
            tag = Tag(
                name=tag_data["name"],
                description=tag_data["description"],
                color=tag_data["color"],
            )
            db.session.add(tag)
            created_tags[tag_data["name"]] = tag
            click.echo(f'Created tag: {tag_data["name"]}')
        else:
            created_tags[tag_data["name"]] = existing_tag

    db.session.commit()

    # 创建示例模型
    sample_models = [
        {
            "name": "甜美女声",
            "description": "清甜温柔的女性声音，适合有声书朗读、客服语音等场景",
            "model_type": "official",
            "voice_characteristics": "音色清亮，语调温和，富有亲和力",
            "tags": ["女声", "青年", "温柔", "甜美", "官方"],
            "quality_score": 9.2,
        },
        {
            "name": "磁性男声",
            "description": "低沉磁性的男性声音，适合广告配音、纪录片解说",
            "model_type": "official",
            "voice_characteristics": "声音浑厚，富有磁性，极具感染力",
            "tags": ["男声", "中年", "磁性", "专业", "官方"],
            "quality_score": 9.0,
        },
        {
            "name": "活力青年",
            "description": "充满活力的青年声音，适合教育内容、产品介绍",
            "model_type": "official",
            "voice_characteristics": "声音明亮，节奏感强，充满朝气",
            "tags": ["男声", "青年", "活力", "专业", "官方"],
            "quality_score": 8.8,
        },
        {
            "name": "知性女声",
            "description": "知性优雅的女性声音，适合新闻播报、学术讲解",
            "model_type": "official",
            "voice_characteristics": "发音标准，语调沉稳，具有权威感",
            "tags": ["女声", "中年", "专业", "沉稳", "官方"],
            "quality_score": 9.1,
        },
        {
            "name": "温暖长者",
            "description": "温暖慈祥的长者声音，适合故事讲述、人文内容",
            "model_type": "official",
            "voice_characteristics": "声音温和，富有人生阅历，令人安心",
            "tags": ["男声", "老年", "温柔", "专业", "官方"],
            "quality_score": 8.9,
        },
    ]

    for model_data in sample_models:
        existing_model = VoiceModel.query.filter_by(name=model_data["name"]).first()
        if not existing_model:
            # 创建模型文件路径（实际应用中应该是真实的模型文件）
            model_dir = os.path.join(
                app.config["UPLOAD_FOLDER"],
                "models",
                "official",
                model_data["name"].lower().replace(" ", "_"),
            )
            os.makedirs(model_dir, exist_ok=True)

            model_path = os.path.join(
                model_dir, f'{model_data["name"].lower().replace(" ", "_")}.pth'
            )
            config_path = os.path.join(
                model_dir, f'{model_data["name"].lower().replace(" ", "_")}_config.json'
            )

            # 创建模拟文件
            with open(model_path, "w") as f:
                f.write(f'# Simulated model file for {model_data["name"]}\n')
            with open(config_path, "w") as f:
                f.write(f'{{"model_name": "{model_data["name"]}", "version": "1.0"}}\n')

            model = VoiceModel(
                name=model_data["name"],
                description=model_data["description"],
                model_type=model_data["model_type"],
                model_path=model_path,
                config_path=config_path,
                voice_characteristics=model_data["voice_characteristics"],
                quality_score=model_data["quality_score"],
                status="active",
                is_public=True,
                is_featured=True,
                review_status="approved",
            )

            model.set_supported_emotions(["neutral", "happy", "sad", "calm", "excited"])
            model.set_supported_languages(["zh-CN", "en-US"])

            # 添加标签
            for tag_name in model_data["tags"]:
                if tag_name in created_tags:
                    model.tags.append(created_tags[tag_name])
                    created_tags[tag_name].increment_usage()

            db.session.add(model)
            click.echo(f'Created model: {model_data["name"]}')

    db.session.commit()
    click.echo("Sample models and tags created successfully.")


@app.cli.command()
@click.option("--hours", default=24, help="Age threshold in hours")
def cleanup_temp_files(hours):
    """清理临时文件"""
    from app.utils.helpers import clean_temp_files

    click.echo(f"Cleaning temporary files older than {hours} hours...")
    clean_temp_files(max_age_hours=hours)
    click.echo("Temporary files cleaned.")


@app.cli.command()
def cleanup_expired_tokens():
    """清理过期令牌"""
    from app.auth.utils import clean_expired_tokens

    click.echo("Cleaning expired tokens...")
    count = clean_expired_tokens()
    click.echo(f"Cleaned {count} expired tokens.")


@app.cli.command()
@click.option("--days", default=30, help="Age threshold in days")
@click.option(
    "--keep-completed", is_flag=True, default=True, help="Keep completed tasks"
)
def cleanup_old_tasks(days, keep_completed):
    """清理旧任务"""
    from app.services.task_service import TaskService

    click.echo(f"Cleaning tasks older than {days} days...")
    try:
        result = TaskService.cleanup_old_tasks(
            days_threshold=days, keep_completed=keep_completed
        )
        click.echo(f'Cleaned {result["voice_clone_deleted"]} voice clone tasks')
        click.echo(f'Cleaned {result["tts_deleted"]} TTS tasks')
        click.echo(f'Total cleaned: {result["total_deleted"]} tasks')
    except Exception as e:
        click.echo(f"Error cleaning tasks: {e}", err=True)


@app.cli.command()
def cleanup_orphaned_files():
    """清理孤立文件"""
    from app.services.file_service import cleanup_orphaned_files

    click.echo("Cleaning orphaned files...")
    try:
        count = cleanup_orphaned_files()
        click.echo(f"Cleaned {count} orphaned files.")
    except Exception as e:
        click.echo(f"Error cleaning files: {e}", err=True)


@app.cli.command()
@click.option("--user-id", help="User ID to show stats for")
@click.option("--days", default=30, help="Time period in days")
def show_stats(user_id, days):
    """显示系统统计信息"""
    from app.services.task_service import TaskService

    click.echo(f"System Statistics (Last {days} days)")
    click.echo("=" * 50)

    try:
        stats = TaskService.get_task_statistics(user_id=user_id, time_period_days=days)

        click.echo("Voice Clone Tasks:")
        vc_stats = stats["voice_clone"]
        click.echo(f'  Total: {vc_stats["total"]}')
        click.echo(f'  Completed: {vc_stats["completed"]}')
        click.echo(f'  Failed: {vc_stats["failed"]}')
        click.echo(f'  Processing: {vc_stats["processing"]}')
        click.echo(f'  Success Rate: {vc_stats["success_rate"]}%')
        click.echo(f'  Avg Processing Time: {vc_stats["avg_processing_time_seconds"]}s')

        click.echo("\nTTS Tasks:")
        tts_stats = stats["tts"]
        click.echo(f'  Total: {tts_stats["total"]}')
        click.echo(f'  Completed: {tts_stats["completed"]}')
        click.echo(f'  Failed: {tts_stats["failed"]}')
        click.echo(f'  Processing: {tts_stats["processing"]}')
        click.echo(f'  Success Rate: {tts_stats["success_rate"]}%')
        click.echo(
            f'  Avg Processing Time: {tts_stats["avg_processing_time_seconds"]}s'
        )

        click.echo(f'\nTotal Tasks: {stats["total_tasks"]}')

    except Exception as e:
        click.echo(f"Error getting statistics: {e}", err=True)


@app.cli.command()
def check_system():
    """检查系统状态"""
    click.echo("System Health Check")
    click.echo("=" * 30)

    # 检查数据库连接
    try:
        db.session.execute("SELECT 1")
        click.echo("✓ Database: Connected")
    except Exception as e:
        click.echo(f"✗ Database: Error - {e}")

    # 检查Redis连接
    try:
        from app.extensions import redis_client

        redis_client.ping()
        click.echo("✓ Redis: Connected")
    except Exception as e:
        click.echo(f"✗ Redis: Error - {e}")

    # 检查Celery
    try:
        from app.extensions import celery

        inspect = celery.control.inspect()
        active = inspect.active()
        if active:
            click.echo("✓ Celery: Workers available")
        else:
            click.echo("? Celery: No active workers")
    except Exception as e:
        click.echo(f"✗ Celery: Error - {e}")

    # 检查上传目录
    upload_dir = app.config["UPLOAD_FOLDER"]
    if os.path.exists(upload_dir) and os.access(upload_dir, os.W_OK):
        click.echo("✓ Upload Directory: Accessible")
    else:
        click.echo(f"✗ Upload Directory: Not accessible - {upload_dir}")

    # 检查模型目录
    model_paths = [
        app.config.get("SOVITS_MODEL_PATH"),
        app.config.get("GPT_MODEL_PATH"),
    ]

    for i, path in enumerate(model_paths):
        model_type = ["SoVITS", "GPT"][i]
        if path and os.path.exists(path):
            click.echo(f"✓ {model_type} Models: Found at {path}")
        else:
            click.echo(f"? {model_type} Models: Path not set or not found")


@app.cli.command()
@click.argument("username")
def reset_password(username):
    """重置用户密码"""
    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(f'User "{username}" not found.')
        return

    new_password = click.prompt(
        "New password", hide_input=True, confirmation_prompt=True
    )
    user.set_password(new_password)
    db.session.commit()

    click.echo(f'Password reset for user "{username}".')


@app.cli.command()
@click.argument("username")
@click.argument("role", type=int)
def set_user_role(username, role):
    """设置用户角色 (0=用户, 1=审核员, 2=管理员)"""
    if role not in [0, 1, 2]:
        click.echo("Invalid role. Use 0 (user), 1 (auditor), or 2 (admin).")
        return

    user = User.query.filter_by(username=username).first()
    if not user:
        click.echo(f'User "{username}" not found.')
        return

    old_role = user.role
    user.role = role
    db.session.commit()

    role_names = {0: "User", 1: "Auditor", 2: "Admin"}
    click.echo(
        f'Changed "{username}" role from {role_names[old_role]} to {role_names[role]}.'
    )


@app.cli.command()
def list_users():
    """列出所有用户"""
    users = User.query.order_by(User.created_at.desc()).all()

    click.echo("Users:")
    click.echo("-" * 80)
    click.echo(
        f'{"Username":<20} {"Email":<30} {"Role":<10} {"Status":<10} {"Created":<20}'
    )
    click.echo("-" * 80)

    role_names = {0: "User", 1: "Auditor", 2: "Admin"}

    for user in users:
        status = "Active" if user.is_active else "Inactive"
        created = user.created_at.strftime("%Y-%m-%d %H:%M")
        click.echo(
            f"{user.username:<20} {user.email:<30} {role_names[user.role]:<10} {status:<10} {created:<20}"
        )


if __name__ == "__main__":
    # 如果直接运行此文件，启动开发服务器
    if len(sys.argv) == 1:
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        # 否则执行CLI命令
        app.cli()
