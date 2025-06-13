from datetime import datetime
from app.extensions import db
import uuid
import json


class VoiceCloneTask(db.Model):
    """音色克隆任务模型"""

    __tablename__ = "voice_clone_tasks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    # 任务信息
    task_name = db.Column(db.String(100), nullable=False)
    status = db.Column(
        db.String(20), default="pending", nullable=False
    )  # pending, processing, completed, failed, cancelled
    progress = db.Column(db.Integer, default=0)  # 0-100

    # 音频样本信息
    audio_samples = db.Column(db.Text)  # JSON格式存储样本文件路径列表
    total_duration = db.Column(db.Float)  # 总时长(秒)
    sample_count = db.Column(db.Integer, default=0)

    # 模型信息
    model_name = db.Column(db.String(100))
    model_path = db.Column(db.String(255))

    # 任务配置
    config = db.Column(db.Text)  # JSON格式存储训练配置

    # 结果信息
    result_model_id = db.Column(db.String(36), db.ForeignKey("voice_models.id"))
    error_message = db.Column(db.Text)

    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    estimated_completion = db.Column(db.DateTime)

    # Celery任务ID
    celery_task_id = db.Column(db.String(255))

    # 关联关系
    result_model = db.relationship(
        "VoiceModel", foreign_keys=[result_model_id], backref="clone_task"
    )

    def set_audio_samples(self, samples):
        """设置音频样本列表"""
        self.audio_samples = json.dumps(samples)

    def get_audio_samples(self):
        """获取音频样本列表"""
        if self.audio_samples:
            return json.loads(self.audio_samples)
        return []

    def set_config(self, config):
        """设置任务配置"""
        self.config = json.dumps(config)

    def get_config(self):
        """获取任务配置"""
        if self.config:
            return json.loads(self.config)
        return {}

    def update_status(self, status, progress=None, error_message=None):
        """更新任务状态"""
        self.status = status
        if progress is not None:
            self.progress = progress
        if error_message:
            self.error_message = error_message

        if status == "processing" and not self.started_at:
            self.started_at = datetime.utcnow()
        elif status in ["completed", "failed", "cancelled"]:
            self.completed_at = datetime.utcnow()

        db.session.commit()

    def get_duration(self):
        """获取任务执行时长"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return 0

    def is_active(self):
        """检查任务是否为活跃状态"""
        return self.status in ["pending", "processing"]

    def can_be_cancelled(self):
        """检查任务是否可以被取消"""
        return self.status in ["pending", "processing"]

    def can_be_retried(self):
        """检查任务是否可以重试"""
        return self.status == "failed"

    def to_dict(self, include_config=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "task_name": self.task_name,
            "status": self.status,
            "progress": self.progress,
            "sample_count": self.sample_count,
            "total_duration": self.total_duration,
            "model_name": self.model_name,
            "model_path": self.model_path,
            "result_model_id": self.result_model_id,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "estimated_completion": (
                self.estimated_completion.isoformat()
                if self.estimated_completion
                else None
            ),
            "duration_seconds": self.get_duration(),
            "is_active": self.is_active(),
            "can_be_cancelled": self.can_be_cancelled(),
            "can_be_retried": self.can_be_retried(),
        }

        if include_config:
            data["config"] = self.get_config()
            data["audio_samples"] = self.get_audio_samples()

        return data

    def __repr__(self):
        return f"<VoiceCloneTask {self.task_name}>"


class TTSTask(db.Model):
    """文本转语音任务模型"""

    __tablename__ = "tts_tasks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    # 任务信息
    status = db.Column(
        db.String(20), default="pending", nullable=False
    )  # pending, processing, completed, failed, cancelled

    # 输入信息
    text = db.Column(db.Text, nullable=False)
    model_id = db.Column(
        db.String(36), db.ForeignKey("voice_models.id"), nullable=False
    )
    emotion = db.Column(
        db.String(20), default="neutral"
    )  # 情感: neutral, happy, sad, angry, etc.
    speed = db.Column(db.Float, default=1.0)  # 语速倍率

    # 高级参数
    pitch = db.Column(db.Float, default=1.0)  # 音调倍率
    volume = db.Column(db.Float, default=1.0)  # 音量倍率

    # 输出信息
    audio_url = db.Column(db.String(255))
    audio_path = db.Column(db.String(255))
    audio_duration = db.Column(db.Float)  # 音频时长(秒)
    audio_size = db.Column(db.Integer)  # 文件大小(字节)

    # 质量信息
    quality_score = db.Column(db.Float)  # 生成质量评分

    # 错误信息
    error_message = db.Column(db.Text)

    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    # Celery任务ID
    celery_task_id = db.Column(db.String(255))

    # 统计信息
    download_count = db.Column(db.Integer, default=0)  # 下载次数

    # 关联关系
    model = db.relationship("VoiceModel", backref="tts_tasks")

    def update_status(self, status, error_message=None):
        """更新任务状态"""
        self.status = status
        if error_message:
            self.error_message = error_message

        if status == "processing" and not self.started_at:
            self.started_at = datetime.utcnow()
        elif status in ["completed", "failed", "cancelled"]:
            self.completed_at = datetime.utcnow()

        db.session.commit()

    def set_result(self, audio_path, audio_url, duration, file_size=None):
        """设置生成结果"""
        self.audio_path = audio_path
        self.audio_url = audio_url
        self.audio_duration = duration

        if file_size:
            self.audio_size = file_size
        elif audio_path:
            try:
                import os

                self.audio_size = os.path.getsize(audio_path)
            except:
                pass

        self.update_status("completed")

    def get_duration(self):
        """获取任务执行时长"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return 0

    def is_active(self):
        """检查任务是否为活跃状态"""
        return self.status in ["pending", "processing"]

    def can_be_cancelled(self):
        """检查任务是否可以被取消"""
        return self.status in ["pending", "processing"]

    def can_be_retried(self):
        """检查任务是否可以重试"""
        return self.status == "failed"

    def increment_download(self):
        """增加下载次数"""
        self.download_count += 1
        db.session.commit()

    def get_text_length(self):
        """获取文本长度"""
        return len(self.text) if self.text else 0

    def get_estimated_audio_duration(self):
        """估算音频时长（基于文本长度和语速）"""
        if not self.text:
            return 0

        # 简单估算：中文每字符约0.15秒，英文每字符约0.1秒
        char_count = len(self.text)
        chinese_chars = len([c for c in self.text if "\u4e00" <= c <= "\u9fff"])
        english_chars = char_count - chinese_chars

        estimated_duration = (chinese_chars * 0.15 + english_chars * 0.1) / self.speed
        return round(estimated_duration, 2)

    def to_dict(self, include_full_text=True):
        """转换为字典"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "text": (
                self.text
                if include_full_text
                else (self.text[:50] + "..." if len(self.text) > 50 else self.text)
            ),
            "text_length": self.get_text_length(),
            "model_id": self.model_id,
            "emotion": self.emotion,
            "speed": self.speed,
            "pitch": self.pitch,
            "volume": self.volume,
            "status": self.status,
            "audio_url": self.audio_url,
            "audio_duration": self.audio_duration,
            "audio_size": self.audio_size,
            "quality_score": self.quality_score,
            "download_count": self.download_count,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "duration_seconds": self.get_duration(),
            "estimated_audio_duration": self.get_estimated_audio_duration(),
            "is_active": self.is_active(),
            "can_be_cancelled": self.can_be_cancelled(),
            "can_be_retried": self.can_be_retried(),
        }

        # 添加模型信息（如果已加载）
        if hasattr(self, "model") and self.model:
            data["model_name"] = self.model.name
            data["model_type"] = self.model.model_type

        return data

    def __repr__(self):
        return f"<TTSTask {self.id}>"


class TaskQueue(db.Model):
    """任务队列模型（用于优先级调度）"""

    __tablename__ = "task_queue"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 任务信息
    task_type = db.Column(db.String(20), nullable=False)  # voice_clone, tts
    task_id = db.Column(db.String(36), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)

    # 调度信息
    priority = db.Column(db.Integer, default=0)  # 优先级，数值越高优先级越高
    status = db.Column(
        db.String(20), default="pending"
    )  # pending, processing, completed, failed

    # 资源需求
    estimated_duration = db.Column(db.Integer)  # 预估执行时间(秒)
    resource_requirements = db.Column(db.Text)  # JSON格式存储资源需求

    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    scheduled_at = db.Column(db.DateTime)  # 调度时间
    started_at = db.Column(db.DateTime)  # 开始执行时间
    completed_at = db.Column(db.DateTime)  # 完成时间

    # 重试信息
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)

    def set_resource_requirements(self, requirements):
        """设置资源需求"""
        self.resource_requirements = json.dumps(requirements)

    def get_resource_requirements(self):
        """获取资源需求"""
        if self.resource_requirements:
            return json.loads(self.resource_requirements)
        return {}

    def can_retry(self):
        """检查是否可以重试"""
        return self.retry_count < self.max_retries and self.status == "failed"

    def increment_retry(self):
        """增加重试次数"""
        self.retry_count += 1
        db.session.commit()

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "task_type": self.task_type,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "priority": self.priority,
            "status": self.status,
            "estimated_duration": self.estimated_duration,
            "resource_requirements": self.get_resource_requirements(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "can_retry": self.can_retry(),
            "created_at": self.created_at.isoformat(),
            "scheduled_at": (
                self.scheduled_at.isoformat() if self.scheduled_at else None
            ),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }

    def __repr__(self):
        return f"<TaskQueue {self.task_type}:{self.task_id}>"


class TaskDependency(db.Model):
    """任务依赖关系模型"""

    __tablename__ = "task_dependencies"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 任务关系
    parent_task_type = db.Column(db.String(20), nullable=False)
    parent_task_id = db.Column(db.String(36), nullable=False)
    child_task_type = db.Column(db.String(20), nullable=False)
    child_task_id = db.Column(db.String(36), nullable=False)

    # 依赖类型
    dependency_type = db.Column(
        db.String(20), default="sequential"
    )  # sequential, conditional, resource

    # 状态
    is_satisfied = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    satisfied_at = db.Column(db.DateTime)

    def mark_satisfied(self):
        """标记依赖已满足"""
        self.is_satisfied = True
        self.satisfied_at = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "parent_task_type": self.parent_task_type,
            "parent_task_id": self.parent_task_id,
            "child_task_type": self.child_task_type,
            "child_task_id": self.child_task_id,
            "dependency_type": self.dependency_type,
            "is_satisfied": self.is_satisfied,
            "created_at": self.created_at.isoformat(),
            "satisfied_at": (
                self.satisfied_at.isoformat() if self.satisfied_at else None
            ),
        }

    def __repr__(self):
        return f"<TaskDependency {self.parent_task_type}:{self.parent_task_id} -> {self.child_task_type}:{self.child_task_id}>"
