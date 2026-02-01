# https://docs.ultralytics.com/quickstart/#inspecting-settings
from ultralytics import YOLO, settings

print(settings)

# 사전학습 모델(pretraind)
model = YOLO("yolo26n.pt")

results = model.train(data="coco8.yaml", epochs=3)
results = model.val()
results = model("https://ultralytics.com/images/bus.jpg")

success = model.export(format="onnx")