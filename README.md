# smart-control

智慧化環境控制後端，在樹莓派上執行。

## API

透過 Bearer Token 進行身份認證。

### GET /rekognition

將觸發執行 AWS Rekognition，並記錄照片中的人數。

### POST /aircon

控制冷氣溫度和開關機

+ 參數

    + `action`：動作設定

        + 設定溫度：`<temperature>c`
        接受範圍：16 ~ 30 度

        + 關機：`off`

### /schedule

包含完整 CRUD 功能，可以查看、設定、編輯和刪除冷氣排程。

#### GET

取得冷氣排程資料

#### POST

設定冷氣排程

+ 參數

    + `time`：時間設定

        + 格式：`%Y-%m-%d %H:%M:%S`

    + `action`：動作設定

        + 設定溫度：`<temperature>c`
        接受範圍：16 ~ 30 度

        + 關機：`off`

+ Response

    + `schedule_id`：該排程之 ID

#### PUT

修改冷氣排程，動作和時間皆可修改

+ 參數

    + `schedule_id`：該排程之 ID

    + `time`：時間設定

        + 格式：`%Y-%m-%d %H:%M:%S`

    + `action`：動作設定

        + 設定溫度：`<temperature>c`
        接受範圍：16 ~ 30 度

        + 關機：`off`

#### DELETE

刪除冷氣排程

+ 參數

    + `schedule_id`：該排程之 ID

## Scripts

### [sensor.py](./smart_room/scripts/sensor.py)

透過 motion sensor 感測有人時呼叫 `/rekognition` API 以進行人數計算。

### [capture.sh](./smart_room/scripts/capture.sh)

透過 crontab 定時執行，拍照以及儲存壓縮後的照片
