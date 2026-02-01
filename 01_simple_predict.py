from ultralytics import YOLO

# 스크래치 모델
# model = YOLO("yolov26n.yaml")

# 사전학습 모델(pretraind)
model = YOLO("yolo26n.pt")

results = model.train(data="coco8.yaml", epochs=3)
results = model.val()
results = model("https://ultralytics.com/images/bus.jpg")

success = model.export(format="onnx")