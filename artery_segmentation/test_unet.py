
import torch

from unet_model import UNet


def main():
    model = UNet()
    dummy_input = torch.randn(2, 1, 512, 512)

    with torch.no_grad():
        output = model(dummy_input)

    print("Input shape:", dummy_input.shape)
    print("Output shape:", output.shape)
    print(
        "Total parameters:",
        sum(p.numel() for p in model.parameters())
    )

    assert output.shape == (2, 1, 512, 512)
    print("U-Net architecture test passed!")


if __name__ == "__main__":
    main()
