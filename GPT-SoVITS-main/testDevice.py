import torch

# 是否有 GPU
print("CUDA 是否可用：", torch.cuda.is_available())

# 有多少个 GPU
print("可用 GPU 数量：", torch.cuda.device_count())

# 当前默认的 GPU
if torch.cuda.is_available():
    print("默认 GPU 设备编号：", torch.cuda.current_device())
    print("默认 GPU 名称：", torch.cuda.get_device_name(torch.cuda.current_device()))
else:
    print("未检测到可用 GPU。")
