from endpoints.rekognition.resource import RekognitionResource
from endpoints.aircon.resource import AirconResource, AirconScheduleResource

RESOURCES = {
    "rekognition": RekognitionResource,
    "aircon": AirconResource,
    "schedule": AirconScheduleResource,
}
