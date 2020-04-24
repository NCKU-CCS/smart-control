from endpoints.rekognition.resource import RekognitionResource
from endpoints.aircon.resource import AirconResource
from endpoints.light_control.resource import LightControlResource

RESOURCES = {
    "rekognition": RekognitionResource,
    "aircon": AirconResource,
    "light_control": LightControlResource,
}
