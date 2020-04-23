# smart-control

智慧化環境控制後端，在樹莓派上執行。

## Getting Started

### Prerequisites

- python 3.6.8

### Running Project

1. update the .env file
2. install dependences
```
pipenv install
```
3. run with Python3
```
pipenv run python smart_room/app.py
```

## API

透過 Bearer Token 進行身份認證。

### GET /rekognition

將觸發執行 AWS Rekognition，並記錄照片中的人數。

### POST /aircon

控制冷氣溫度和開關機

+ 參數

    + `action_front`：動作設定

        + 設定溫度：`<temperature>c`
        接受範圍：16 ~ 30 度

        + 關機：`off`

    + `action_back`：動作設定

        + 設定溫度：`<temperature>c`
        接受範圍：16 ~ 30 度

        + 關機：`off`

## Scripts

### [sensor.py](./smart_room/scripts/sensor.py)

透過 motion sensor 感測有人時呼叫 `/rekognition` API 以進行人數計算。

### [capture.sh](./smart_room/scripts/capture.sh)

透過 crontab 定時執行，拍照以及儲存壓縮後的照片
