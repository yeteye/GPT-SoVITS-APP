from datetime import datetime
from app.extensions import db
from app.models.model import VoiceModel

class Emotion(db.Model):
    """
    情感参考表

    DDL:
    CREATE TABLE `emotion` (
      `id` INT NOT NULL AUTO_INCREMENT,
      `model_id` VARCHAR(36) NOT NULL,
      `type` ENUM(
        'neutral',
        'happy',
        'sad',
        'angry',
        'calm',
        'surprise',
        'fear',
        'disgust'
      ) NOT NULL,
      `ref_path` VARCHAR(255) NOT NULL,
      `ref_lang` VARCHAR(10) NOT NULL,
      `ref_text` TEXT NOT NULL,
      `description` TEXT,
      PRIMARY KEY (`id`),
      INDEX `idx_emotion_model` (`model_id`),
      CONSTRAINT `fk_emotion_model`
        FOREIGN KEY (`model_id`) REFERENCES `voice_models` (`id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE
    ) ENGINE=InnoDB
      DEFAULT CHARSET=utf8mb4
      COLLATE=utf8mb4_0900_ai_ci;
    """

    __tablename__ = 'emotion'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model_id = db.Column(db.String(36), db.ForeignKey('voice_models.id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False, index=True)
    type = db.Column(db.Enum('neutral', 'happy', 'sad', 'angry', 'calm', 'surprise', 'fear', 'disgust', name='emotion_types'), nullable=False)
    ref_path = db.Column(db.String(255), nullable=False)
    ref_lang = db.Column(db.String(10), nullable=False)
    ref_text = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)

    # 关联主模型
    model = db.relationship('VoiceModel', backref=db.backref('emotions', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'model_id': self.model_id,
            'type': self.type,
            'ref_path': self.ref_path,
            'ref_lang': self.ref_lang,
            'ref_text': self.ref_text,
            'description': self.description,
        }

    def __repr__(self):
        return f"<Emotion {self.type} for model {self.model_id}>"
