"""Download the small offline English model once, separately on PC and Pi."""
from pathlib import Path
import shutil
import sys
from urllib.request import urlopen
import uuid
import zipfile


MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
REQUIRED_FILES = ("am/final.mdl", "conf/model.conf", "graph/HCLr.fst")


def model_ready(path):
    return all((Path(path) / name).is_file() for name in REQUIRED_FILES)


def install_model():
    folder = Path(__file__).resolve().parent.parent / "speech_models"
    target = folder / MODEL_NAME
    if model_ready(target):
        print("Offline English speech model is ready.")
        return
    if target.exists():
        raise ValueError("The existing speech model is incomplete. Rename its folder and retry.")

    folder.mkdir(parents=True, exist_ok=True)
    temporary = (folder / ("download-" + uuid.uuid4().hex)).resolve()
    if temporary.parent != folder.resolve():
        raise ValueError("Unexpected model download folder")
    temporary.mkdir()
    try:
        archive = temporary / "model.zip"
        print("Downloading the offline English model (about 40 MB)...", flush=True)
        received = 0
        with urlopen(MODEL_URL, timeout=30) as response, archive.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                received += len(chunk)
                if received > 80 * 1024 * 1024:
                    raise ValueError("Speech model download exceeded its size limit.")
                output.write(chunk)

        with zipfile.ZipFile(archive) as zipped:
            if sum(item.file_size for item in zipped.infolist()) > 200 * 1024 * 1024:
                raise ValueError("Speech model archive exceeded its unpacked size limit.")
            for item in zipped.infolist():
                path = (temporary / item.filename).resolve()
                if not path.is_relative_to(temporary / MODEL_NAME):
                    raise ValueError("Unexpected path in speech model archive.")
            zipped.extractall(temporary)
        unpacked = temporary / MODEL_NAME
        if not model_ready(unpacked):
            raise ValueError("Downloaded archive did not contain a complete speech model.")
        unpacked.rename(target)
        print("Offline English speech model is ready.")
    finally:
        if temporary.parent == folder.resolve() and temporary.name.startswith("download-"):
            shutil.rmtree(temporary)


if __name__ == "__main__":
    try:
        install_model()
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"Speech setup failed: {error}", file=sys.stderr)
        sys.exit(1)
