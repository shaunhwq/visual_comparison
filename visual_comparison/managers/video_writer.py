import cv2
import os


__all__ = ["VideoWriter"]


class VideoWriter:
    def __init__(self, output_path, width, height, fps):
        # TODO: Add support for lossless, fourcc: FFV1, video_ext: avi
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        self.width = width
        self.height = height

    def write_image(self, image):
        h, w = image.shape[:2]

        if not (h == self.height and w == self.width):
            self.release()
            return False

        self.writer.write(image)
        return True

    def release(self):
        self.writer.release()
