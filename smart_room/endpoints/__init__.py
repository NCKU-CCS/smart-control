from endpoints.rekognition.resource import RekognitionResource
from endpoints.aircon.resource import AirconResource
from endpoints.schedule.resource import ScheduleResource

RESOURCES = {
    "rekognition": RekognitionResource,
    "aircon": AirconResource,
    "schedule": ScheduleResource,
}
