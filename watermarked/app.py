import os
import tempfile
import logging
from datetime import datetime

from flask import Flask, request, jsonify, send_file, after_this_request
from werkzeug.utils import secure_filename

from config import Config
from audio_processor import AudioWatermarkProcessor

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask 应用
app = Flask(__name__)
app.config.from_object(Config)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# 允许格式
ALLOWED_EXTENSIONS = {'wav'}

# 实例化处理器，传入 app.config 以读取 MySQL 配置
processor = AudioWatermarkProcessor(db_config=app.config)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'audio_watermark_api',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/watermark/embed', methods=['POST'])
def embed_watermark_api():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未提供音频文件'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': '只支持 WAV 格式文件'}), 400

        username = request.form.get('username')
        if not username:
            return jsonify({'error': '用户名不能为空'}), 400

        try:
            code_length = int(request.form.get('code_length', 16))
        except ValueError:
            return jsonify({'error': '识别码长度必须是整数'}), 400
        if code_length not in [8, 16, 32]:
            return jsonify({'error': '识别码长度必须是 8, 16, 或 32'}), 400
        description = request.form.get('description', '')

        # 保存上传的临时文件, 关闭句柄后再写入避免 Windows 文件锁
        filename = secure_filename(file.filename)
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_input_path = temp_input.name
        temp_input.close()
        file.save(temp_input_path)

        # 验证 WAV 文件头
        import wave
        try:
            with wave.open(temp_input_path, 'rb') as wav:
                # 试读头部无异常
                pass
        except wave.Error as we:
            os.unlink(temp_input_path)
            logger.error(f"无效的 WAV 文件: {we}")
            return jsonify({'error': '无效的 WAV 文件'}), 400

        # 生成输出临时文件路径，关闭句柄后在 embed 中写入
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_output_path = temp_output.name
        temp_output.close()

        # 清理上传文件
        # 处理完成后删除，在 after_this_request
        @after_this_request
        def cleanup_files(response):
            try:
                if os.path.exists(temp_input_path):
                    os.unlink(temp_input_path)
                # 输出在 send_file 之后删除
                if response.status_code == 200 and os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
            return response

        # 嵌入
        model_id = request.form.get('model_id')

        result = processor.embed_watermark(
            temp_input_path, temp_output_path, username, model_id, code_length, description
        )

        if result.get('success'):
            # 返回带水印的文件
            return send_file(
                temp_output_path,
                as_attachment=True,
                download_name=f"watermarked_{filename}",
                mimetype='audio/wav'
            )
        else:
            # 删除输出
            if os.path.exists(temp_output_path):
                os.unlink(temp_output_path)
            return jsonify({
                'error': '水印嵌入失败',
                'details': result.get('error', '未知错误')
            }), 500
    except Exception as e:
        logger.error(f"嵌入水印API错误: {e}", exc_info=True)
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/watermark/verify', methods=['POST'])
def verify_watermark_api():
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未提供音频文件'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': '只支持 WAV 格式文件'}), 400

        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.environ.get('HTTP_USER_AGENT', '')

        filename = secure_filename(file.filename)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_path = temp_file.name
        temp_file.close()
        file.save(temp_path)

        # 验证 WAV 文件
        import wave
        try:
            with wave.open(temp_path, 'rb') as wav:
                pass
        except wave.Error as we:
            os.unlink(temp_path)
            logger.error(f"无效的 WAV 文件: {we}")
            return jsonify({'error': '无效的 WAV 文件'}), 400

        # 处理完成后删除
        @after_this_request
        def cleanup_verify(response):
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {e}")
            return response

        result = processor.extract_watermark(
            temp_path, filename, ip_address, user_agent
        )

        if result is None:
            return jsonify({'success': False, 'error': '提取水印失败，未返回结果'}), 500

        if result.get('success'):
            data = {
                'username': result.get('username'),
                'watermark_code': result.get('watermark_code'),
                'code_length': result.get('code_length'),
                'accuracy': result.get('accuracy'),
                'confidence': result.get('confidence'),
                'created_at': result.get('created_at'),
                'usage_count': result.get('usage_count'),
                'description': result.get('description')
            }
            return jsonify({
                'status': 'success',
                'verification': result.get('verification'),
                'data': data,
                'message': result.get('message', '验证成功')
            })
        else:
            return jsonify({
                'status': 'failed',
                'verification': result.get('verification', 'failed'),
                'message': result.get('message', '验证失败'),
                'error': result.get('error')
            })
    except Exception as e:
        logger.error(f"验证水印API错误: {e}", exc_info=True)
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/watermark/info/<watermark_code>', methods=['GET'])
def get_watermark_info(watermark_code):
    try:
        user_info = processor.db.get_user_by_watermark(watermark_code)
        if user_info:
            return jsonify({
                'status': 'found',
                'data': user_info
            })
        else:
            return jsonify({
                'status': 'not_found',
                'message': '未找到对应的水印记录'
            }), 404
    except Exception as e:
        logger.error(f"查询水印信息错误: {e}", exc_info=True)
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/user/<username>/watermarks', methods=['GET'])
def get_user_watermarks(username):
    try:
        watermarks = processor.db.get_user_watermarks(username)
        return jsonify({
            'status': 'success',
            'username': username,
            'watermarks': watermarks,
            'count': len(watermarks)
        })
    except Exception as e:
        logger.error(f"查询用户水印错误: {e}", exc_info=True)
        return jsonify({'error': '服务器内部错误'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': '文件太大，最大支持 %d 字节' % Config.MAX_CONTENT_LENGTH}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'API端点不存在'}), 404

if __name__ == '__main__':
    # 启动服务
    host = Config.HOST
    port = Config.PORT
    debug = Config.DEBUG
    logger.info(f"启动音频水印API服务，监听 {host}:{port}")
    app.run(debug=debug, host=host, port=port)