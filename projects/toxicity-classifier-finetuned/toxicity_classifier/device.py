from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass
class DeviceConfig:
    device: torch.device
    # True only on CUDA; MPS bf16 support is inconsistent across transformers versions
    use_bf16: bool


def get_device() -> DeviceConfig:
    if torch.backends.mps.is_available():
        return DeviceConfig(device=torch.device("mps"), use_bf16=False)
    if torch.cuda.is_available():
        return DeviceConfig(device=torch.device("cuda"), use_bf16=True)
    return DeviceConfig(device=torch.device("cpu"), use_bf16=False)
