import os
import requests

def download_model():
    # Official InsightFace/ArcFace model link
    url = "https://github.com/deepinsight/insightface/releases/download/v0.7/glintresnet50_arcface_v2.onnx"
    save_path = "models/arcface.onnx"
    
    if not os.path.exists("models"):
        os.makedirs("models")
        
    if not os.path.exists(save_path):
        print(f"Downloading ArcFace model to {save_path}...")
        response = requests.get(url, stream=True)
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete!")
    else:
        print("Model already exists.")

if __name__ == "__main__":
    download_model()
