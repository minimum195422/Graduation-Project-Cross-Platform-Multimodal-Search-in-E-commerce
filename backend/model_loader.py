import torch
import open_clip

device = "cuda" if torch.cuda.is_available() else "cpu"
print("🔍 Load mô hình OpenCLIP ViT-L-14-336...")
model, _, preprocess = open_clip.create_model_and_transforms(
    model_name="ViT-L-14-336", pretrained="openai", image_resolution=336
)
tokenizer = open_clip.get_tokenizer("ViT-L-14-336")
model.to(device)
model.eval()
