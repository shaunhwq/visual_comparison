import numpy as np
from typing import Tuple, List
import enum
import cv2


class TextPosition(enum.Enum):
    TOP_LEFT = enum.auto()
    TOP_RIGHT = enum.auto()
    BTM_LEFT = enum.auto()
    BTM_RIGHT = enum.auto()


def put_text(
    img: np.array,
    text: str,
    position: TextPosition = TextPosition.TOP_LEFT,
    buffer=5,
    font=cv2.FONT_HERSHEY_DUPLEX,
    scale=0.5,
    thickness=1,
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
    :return: Output image containing the text.
    """

    (text_width, text_height), _ = cv2.getTextSize(text, font, scale, thickness)
    img_height, img_width, _ = img.shape

    if position == TextPosition.TOP_LEFT:
        text_position = (buffer, buffer + text_height)
    elif position == TextPosition.TOP_RIGHT:
        text_position = (img_width - text_width - buffer, buffer + text_height)
    elif position == TextPosition.BTM_LEFT:
        text_position = (buffer, img_height - text_height - buffer)
    else:
        text_position = (img_width - text_width - buffer, img_height - text_height - buffer)

    # black outline on white text
    cv2.putText(img, text, text_position, font, scale, (0, 0, 0), thickness + 1)
    cv2.putText(img, text, text_position, font, scale, (255, 255, 255), thickness)


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
