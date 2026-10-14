"""Find microphones by name/API rather than saving changeable device numbers."""


def input_devices():
    import sounddevice as audio

    apis = audio.query_hostapis()
    result = []
    for index, device in enumerate(audio.query_devices()):
        if device["max_input_channels"] > 0:
            result.append({"id": index, "name": device["name"], "api": apis[device["hostapi"]]["name"]})
    return result


def resolve_input(name, api):
    import sounddevice as audio

    if not name:
        index = audio.default.device[0]
        if index < 0:
            raise ValueError("No default microphone. Select one in Settings → Microphone.")
        return index
    for device in input_devices():
        if device["name"] == name and device["api"] == api:
            return device["id"]
    raise ValueError("The saved microphone is disconnected. Select another in Settings → Microphone.")
