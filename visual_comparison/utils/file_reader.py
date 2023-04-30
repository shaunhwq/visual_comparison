import os

import cv2
import numpy as np

__all__ = ["read_media_file", "ImageCapture"]


def read_media_file(file_path):
    ext = os.path.splitext(os.path.basename(file_path))[-1].lower()
    if ext in {".png", ".jpg", ".tif"}:
        capture_obj = ImageCapture(file_path)
    elif ext in {".mp4", ".avi"}:
        capture_obj = cv2.VideoCapture(file_path)
    else:
        raise NotImplementedError(f"Unsupported ext for loading image thumbnail: {ext}")
    return capture_obj


class ImageCapture:
    """
    TODO: Handle HDR Reading too later?
    """
    def __init__(self, image_path):
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        max_img_val = np.iinfo(image.dtype).max
        if max_img_val != 255:
            image = (image.astype(np.float32) / max_img_val * 255.0).clip(0, 255).astype(np.uint8)

        self.image = image

    def read(self):
        if self.image is None:
            return False, None

        return True, self.image.copy()

    def release(self):
        pass
