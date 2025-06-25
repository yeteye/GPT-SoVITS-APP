<template>
  <div class="help-center">
    <h2 class="title">🆘 帮助中心 / 用户手册</h2>
    <p class="subtitle">欢迎使用 GPT-SoVITS 在线语音平台，以下是常见问题与功能指引。</p>

    <!-- 目录导航 -->
    <el-anchor affix>
      <el-anchor-link href="#tts" title="文本转语音" />
      <el-anchor-link href="#clone" title="音色克隆" />
      <el-anchor-link href="#creator" title="创作者中心" />
      <el-anchor-link href="#faq" title="常见问题 FAQ" />
    </el-anchor>

    <!-- 各部分内容 -->
    <div class="section" id="tts">
      <h3>🗣️ 文本转语音</h3>
      <p>输入文本后，可选择不同音色合成语音。支持语速调节、情绪选择等高级参数。</p>
    </div>

    <div class="section" id="clone">
      <h3>🧬 音色克隆</h3>
      <p>上传你的音频样本（10~30秒），系统会自动训练模型生成对应音色。支持进度查看与结果试听。</p>
    </div>

    <div class="section" id="creator">
      <h3>🎧 创作者中心</h3>
      <p>创作者可上传自定义模型、管理音色、设置公开与私有状态，并查看模型数据分析。</p>
    </div>

    <div class="section" id="faq">
      <h3>📌 常见问题 FAQ</h3>
      <el-collapse accordion>
        <el-collapse-item title="1. 上传音频格式要求？" name="1">
          <p>建议使用 wav / mp3 / m4a 格式，采样率16kHz 或 48kHz，时长 ≥10秒。</p>
        </el-collapse-item>
        <el-collapse-item title="2. 训练时间多久？" name="2">
          <p>根据排队情况和服务器负载，通常在 2-10 分钟内完成。</p>
        </el-collapse-item>
        <el-collapse-item title="3. 如何公开自己的音色？" name="3">
          <p>在创作者中心 > 我的音色 中，点击「公开」按钮，即可分享至音色库。</p>
        </el-collapse-item>
        <el-collapse-item title="4. 我的数据会被保存吗？" name="4">
          <p>系统仅用于模型训练，默认保留模型 30 天，您可以随时删除。</p>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup></script>

<style scoped>
.help-center {
  max-width: 960px;
  margin: 40px auto;
  padding: 24px;
}
.title {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 12px;
}
.subtitle {
  font-size: 16px;
  color: #666;
  margin-bottom: 24px;
}
.section {
  margin-bottom: 40px;
}
.section h3 {
  font-size: 22px;
  color: #333;
  margin-bottom: 8px;
}
</style>
