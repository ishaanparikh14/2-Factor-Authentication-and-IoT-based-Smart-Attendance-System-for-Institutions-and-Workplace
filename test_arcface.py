import onnxruntime as ort

session = ort.InferenceSession(
    "models/arcface.onnx",
    providers=["CPUExecutionProvider"]
)

print("ArcFace Loaded Successfully")

print("Input:", session.get_inputs()[0].name)

print("Output:", session.get_outputs()[0].name)
