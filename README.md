# smart-control

智慧化環境控制後端，在樹莓派上執行。

## API

透過 Bearer Token 進行身份認證。

### GET /rekognition

將觸發執行 AWS Rekognition，並記錄照片中的人數。

## Scripts

### [sensor.py](./smart_room/scripts/sensor.py)

透過 motion sensor 感測有人時呼叫 `/rekognition` API 以進行人數計算。

### [capture.sh](./smart_room/scripts/capture.sh)

透過 crontab 定時執行，拍照以及儲存壓縮後的照片
