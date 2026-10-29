"""Triton 에 올릴 resnet18.onnx 생성 (model_repository/resnet18/1/model.onnx)"""
from pathlib import Path

import torch
import torchvision

OUT = Path(__file__).resolve().parent.parent / "model_repository" / "resnet18" / "1" / "model.onnx"

model = torchvision.models.resnet18(weights="DEFAULT").eval()
torch.onnx.export(
    model,
    torch.randn(1, 3, 224, 224),
    OUT,
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}},
    dynamo=False,
)
print(f"saved {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")
