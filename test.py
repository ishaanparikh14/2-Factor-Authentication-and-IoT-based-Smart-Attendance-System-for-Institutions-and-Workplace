import onnxruntime as ort

session = ort.InferenceSession(
    "models/arcface.onnx"
)

print(session.get_inputs()[0].shape)
