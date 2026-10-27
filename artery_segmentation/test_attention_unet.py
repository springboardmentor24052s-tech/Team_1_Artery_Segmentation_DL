
import torch

from attention_unet import AttentionUNet


def main():
    model = AttentionUNet()
    dummy_input = torch.randn(1, 1, 512, 512)

    with torch.no_grad():
        output = model(dummy_input)

    print("Input shape:", dummy_input.shape)
    print("Output shape:", output.shape)
    print(
        "Total parameters:",
        sum(p.numel() for p in model.parameters())
    )

    assert output.shape == (1, 1, 512, 512)
    print("Attention U-Net architecture test passed!")


if __name__ == "__main__":
    main()
