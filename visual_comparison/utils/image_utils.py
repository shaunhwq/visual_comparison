import os
import enum
import platform
import subprocess
from io import BytesIO
from typing import Optional

import cv2
import numpy as np
from PIL import Image
from typing import Tuple, List


__all__ = [
    "TextPosition",
    "put_text",
    "merge_crop",
    "merge_multiple_images",
    "resize_scale"
]


class TextPosition(enum.Enum):
    TOP_LEFT = enum.auto()
    TOP_CENTER = enum.auto()
    TOP_RIGHT = enum.auto()
    BTM_LEFT = enum.auto()
    BTM_CENTER = enum.auto()
    BTM_RIGHT = enum.auto()


def put_text(
    img: np.array,
    text: str,
    position: TextPosition = TextPosition.TOP_LEFT,
    buffer=5,
    font=cv2.FONT_HERSHEY_DUPLEX,
    scale=1,
    thickness=1,
    bg_color: Tuple[int, int, int] = (0, 0, 0),
    fg_color: Tuple[int, int, int] = (255, 255, 255),
    background: Optional[int] = None,
    ) -> np.array:
    """
    Writes text in image according to the specified position
    :param img: Image to write on
    :param text: Text you wish to place onto the image
    :param position: TextPosition enum
    :param buffer: Buffer from the sides of the image
    :param font: font required by cv2.putText
    :param scale: scale required by cv2.putText
    :param thickness: thickness required by cv2.putText
    :param bg_color: background text color in BGR [0, 255]
    :param fg_color: foreground text color in BGR [0, 255]
    :param background: sets background for text to value
    :return: Output image containing the text.
    """

    # Calculates actual scale required to set text size the same for imgs of different sizes
    font_scale = {
        cv2.FONT_HERSHEY_SIMPLEX: 1.0969,
        cv2.FONT_HERSHEY_PLAIN: 2.1608,
        cv2.FONT_HERSHEY_DUPLEX: 1.0914,
        cv2.FONT_HERSHEY_COMPLEX: 1,
        cv2.FONT_HERSHEY_TRIPLEX: 1.0094,
        cv2.FONT_HERSHEY_COMPLEX_SMALL: 1.2952,
        cv2.FONT_HERSHEY_SCRIPT_SIMPLEX: 1.1622,
        cv2.FONT_HERSHEY_SCRIPT_COMPLEX: 1.1169,
    }.get(font)
    # 0.4 = Scale needed for fitting 40 hershey complex characters in 360 pixel width img
    num_chars_scalar = 0.40 / (max(len(text), 40) / 40.0)
    width_scale = (img.shape[1] / 360.0)
    actual_scale = scale * num_chars_scalar * width_scale * font_scale

    (text_width, text_height), _ = cv2.getTextSize(text, font, actual_scale, thickness)
    img_height, img_width, _ = img.shape

    if position == TextPosition.TOP_LEFT:
        text_position = (buffer, buffer + text_height)
    elif position == TextPosition.TOP_CENTER:
        text_position = (img_width // 2 - text_width // 2, buffer + text_height)
    elif position == TextPosition.TOP_RIGHT:
        text_position = (img_width - text_width - buffer, buffer + text_height)
    elif position == TextPosition.BTM_LEFT:
        text_position = (buffer, img_height - text_height - buffer)
    elif position == TextPosition.BTM_CENTER:
        text_position = (img_width // 2 - text_width // 2, img_height - text_height - buffer)
    else:
        text_position = (img_width - text_width - buffer, img_height - text_height - buffer)

    if background is not None:
        # text position = bottom right corner of bbox to put text in
        start_x = text_position[0] - buffer
        end_x = start_x + text_width + buffer * 2
        end_y = text_position[1] + buffer
        start_y = end_y - text_height - buffer * 2
        img[start_y: end_y, start_x: end_x, :] = background

    # Foreground text overlaid onto background for highlight effect
    cv2.putText(img, text, text_position, font, actual_scale, bg_color, thickness + 1)
    cv2.putText(img, text, text_position, font, actual_scale, fg_color, thickness)


def merge_crop(img1: np.array, img2: np.array, position: Tuple[int, int], direction: str) -> np.array:
    """
    Merge two images based on provided position
    :param img1: First image. Placed on the left
    :param img2: Second image. Placed on the right
    :param position: Position at which to partition the images and merge.
    :param direction: {"x", "y"}, x is horizontal axis, y is vertical axis
    :return: np.array
    """

    # Check shape
    h1, w1, c1 = img1.shape
    h2, w2, c2 = img2.shape
    assert h1 == h2 and w1 == w2 and c1 == c2, f"Images not of the same shape. Img1: {img1.shape} Img2: {img2.shape}"

    # Check position within bounds
    x, y = position
    assert x < w1 and y < h1, "Provided postion out of bounds"

    output_img = np.zeros_like(img1)
    if direction == "x":
        output_img[:, :x, :] = img1[:, :x, :]
        output_img[:, x:, :] = img2[:, x:, :]
    else:
        output_img[:y, :, :] = img1[:y, :, :]
        output_img[y:, :, :] = img2[y:, :, :]

    return output_img


def merge_multiple_images(image_list: List[np.array], position: Tuple[int, int]) -> np.array:
    """
    Merges up to 4 images. Order of images determines position in final image.

    idx 0, 1, 2, 3 -> Top Left, Top Right, Btm Left, Btm Right
    :param image_list: List of images to merge
    :param position: Position at which to partition the images and merge.
    :return: Merged image.
    """
    if len(image_list) == 1:
        output_image = image_list[0]
    elif len(image_list) == 2:
        output_image = merge_crop(image_list[0].copy(), image_list[1].copy(), position, "x")
    elif len(image_list) == 3:
        merge01 = merge_crop(image_list[0].copy(), image_list[1].copy(), position, "x")
        output_image = merge_crop(merge01, image_list[2].copy(), position, "y")
    elif len(image_list) == 4:
        merge01 = merge_crop(image_list[0].copy(), image_list[1].copy(), position, "x")
        merge23 = merge_crop(image_list[2].copy(), image_list[3].copy(), position, "x")
        output_image = merge_crop(merge01, merge23, position, "y")
    else:
        raise ValueError(f"Only able to merge up to 4 images. len(image_list) = {len(image_list)}")

    return output_image


def resize_scale(image, scale, interpolation=cv2.INTER_LINEAR):
    """
    Scale resize an image
    :param image: Image to resize
    :param scale: Scale for resizing.
    :param interpolation: Interpolation method for resize operation.
    :return: Resized image
    """
    h, w, _ = image.shape
    new_shape = (int(round(w * scale)), int(round(h * scale)))
    image = cv2.resize(image, new_shape, interpolation=interpolation)
    return image


def image_to_clipboard(image):
    operating_system = platform.system()

    if operating_system == "Darwin":
        _image_to_clipboard_macos(image)
    elif operating_system == "Windows":
        _image_to_clipboard_windows(image)
    elif operating_system == "Linux":
        _image_to_clipboard_linux(image)
    else:
        raise NotImplementedError(f"Clipboard feature not supported for os '{operating_system}'")


def _image_to_clipboard_windows(image: np.array):
    # https://stackoverflow.com/questions/34322132/copy-image-to-clipboard
    try:
        import win32clipboard
    except ImportError as err:
        print(f"win32clipboard is required for clipboard operations. Run 'pip3 install pywin32'. Err: {err}")
        return

    rgb_copy = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_copy)
    # Save the image as binary data
    with BytesIO() as buffer:
        pil_img.save(buffer, format="BMP")
        data = buffer.getvalue()[14:]

    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()


def _image_to_clipboard_macos(image: np.array):
    # Using applescript to read an image, send it to clipboard and then delete it.
    file_name = "vc_clipboard_img.png"
    cv2.imwrite(file_name, image)
    subprocess.run(["osascript", "-e", f'set the clipboard to (read (POSIX file "{file_name}") as «class PNGf»)'])
    os.remove(file_name)


def _image_to_clipboard_linux(image: np.array):
    # https://stackoverflow.com/questions/56618983/how-do-i-copy-a-pil-picture-to-clipboard
    try:
        import klembord
    except ImportError as err:
        print(f"Klembord is required for clipboard operations. Run 'pip3 install klembord. Err: {err}")
        return

    rgb_copy = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_copy)
    # Save the image as binary data
    with BytesIO() as buffer:
        pil_img.save(buffer, format="BMP")
        klembord.set({"image/png": buffer.getvalue()})
