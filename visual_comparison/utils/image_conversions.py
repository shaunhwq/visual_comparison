import numpy as np


__all__ = ["rectify_h264_bt709_video"]


def rectify_h264_bt709_video(bgr_image: np.array) -> np.array:
    """
    Rectifies BT709 h264 videos (Issue with OpenCV)
    """
    out_img = np.zeros_like(bgr_image, dtype=np.float32)
    out_img[:, :, 2] = 1.086275 * bgr_image[:, :, 2] - 0.073168 * bgr_image[:, :, 1] - 0.013231 * bgr_image[:, :, 0]
    out_img[:, :, 1] = 0.096685 * bgr_image[:, :, 2] + 0.844783 * bgr_image[:, :, 1] + 0.058408 * bgr_image[:, :, 0]
    out_img[:, :, 0] = -0.013428 * bgr_image[:, :, 2] - 0.027936 * bgr_image[:, :, 1] + 1.04124 * bgr_image[:, :, 0]
    return np.clip(out_img, 0, 255).astype(np.uint8)
