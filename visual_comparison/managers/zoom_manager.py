from typing import Tuple, List, Optional

import tkinter
import cv2
import numpy as np

from ..utils import image_utils


__all__ = ["ZoomManager"]


class ZoomManager:
    def __init__(self, display_widget):
        """
        :param display_widget: For binding keys to the widget and getting mouse position
        """
        # Key binding
        display_widget.image_label.bind("<Button-1>", self.on_l_mouse_click)
        display_widget.image_label.bind("<Button-2>", self.reset)
        display_widget.image_label.bind("<Motion>", self.on_mouse_move)
        self.display_widget = display_widget

        self.zoom_bbox_pts = []
        self.zoom_box_frozen = False
        self.error_message = ""

    def on_mouse_move(self, event: tkinter.Event) -> None:
        """
        Handle movement of bbox when cursor is moved
        """

        # Don't move zoom selection if frozen
        if self.zoom_box_frozen:
            return

        # No box to move if lesser than 2 points
        if len(self.zoom_bbox_pts) < 2:
            return

        x1, y1 = self.zoom_bbox_pts[0]
        x2, y2 = self.zoom_bbox_pts[1]
        dx, dy = x2 - x1, y2 - y1
        other_new_pt = self.display_widget.mouse_position[0] - dx, self.display_widget.mouse_position[1] - dy
        self.zoom_bbox_pts = [other_new_pt, self.display_widget.mouse_position]

    def reset(self, event: Optional[tkinter.Event] = None) -> None:
        """
        Reset zooming state by setting relevant internal variables.
        """
        self.zoom_bbox_pts = []
        self.zoom_box_frozen = False
        self.error_message = ""

    def on_l_mouse_click(self, event: tkinter.Event) -> None:
        """
        Add points for zoom region. Crop will be between the two selected points.
        If already have 2 points, clicking will toggle whether the bbox is frozen (for cursor movement)
        """
        if len(self.zoom_bbox_pts) == 2:
            self.zoom_box_frozen = not self.zoom_box_frozen
        else:
            self.zoom_bbox_pts.append(self.display_widget.mouse_position)

    def _get_crop_region(self, image_size: np.shape) -> Tuple[int, int, int, int]:
        """
        Gets the slicing safe bbox coordinates in (x, y, w, h), where x and y correspond to
        values in horizontal and vertical axis of the top left corner
        :param image_size: to check if bbox exceeds image
        :return: (x, y, w, h)
        """
        # X = horizontal, Y = Vertical, (0, 0) top left corner
        h, w, c = image_size
        pt1_x, pt1_y = self.zoom_bbox_pts[0]
        pt2_x, pt2_y = self.zoom_bbox_pts[1]
        start_x, start_y = min(pt1_x, pt2_x), min(pt1_y, pt2_y)
        start_x, start_y = max(0, start_x), max(0, start_y)  # Handle < 0 case
        width, height = abs(pt1_x - pt2_x), abs(pt1_y - pt2_y)

        # Handle bbox exceed image
        if start_x + width > w:
            start_x = w - width
        if start_y + height > h:
            start_y = h - height

        return start_x, start_y, width, height

    def draw_regions(self, image: np.array, num_images: int = 1, color: Tuple[int, int, int] = (123, 80, 36)) -> np.array:
        """
        Draw bboxes and write error messages if any
        :param image: Image to draw on
        :param num_images: Number of images to consider (>1 for concat mode)
        :param color: Bbox color
        :return: Annotated image
        """
        # For restricting movement of bbox and crop. Cropping for concat should be done on first image.
        image_shape = image.shape if num_images == 1 else [image.shape[0], image.shape[1] // num_images, image.shape[2]]

        # Marker so they can estimate box size
        if len(self.zoom_bbox_pts) == 1:
            cv2.circle(image, self.zoom_bbox_pts[0], 3, color, -1)

        # Draw rect
        if len(self.zoom_bbox_pts) == 2:
            # Draw on first image
            x, y, w, h = self._get_crop_region(image_shape)

            for i in range(num_images):
                color = color if i == 0 else (128, 255, 128)
                offset_x, offset_y = i * image_shape[1], 0
                pt1, pt2 = (x + i + offset_x, y + offset_y), (x + offset_x + w, y + offset_y + h)
                cv2.rectangle(image, pt1, pt2, color, 2)
                if self.zoom_box_frozen:
                    cv2.rectangle(image, pt1, pt2, (0, 0, 0), 1)

        # Write error message
        if self.error_message != "":
            image_utils.put_text(image, self.error_message, fg_color=(0, 0, 255), background=25)

        return image

    def crop_regions(self, images: List[np.array]) -> np.array:
        """
        Crops the input image(s) and resizes width to match the final image width to stack one on the other
        :param images: Images to crop
        :return: Cropped and resized image
        """
        if len(self.zoom_bbox_pts) != 2:
            return None

        # Crop selected region from the images
        cropped_regions = []
        for image in images:
            start_x, start_y, width, height = self._get_crop_region(image.shape)
            cropped = image[start_y: start_y + height, start_x: start_x + width, :]
            cropped_regions.append(cropped)
        stacked_crops = np.hstack(cropped_regions)

        # Handle invalid crop
        fh, fw, fc = stacked_crops.shape
        if min(fh, fw) == 0:
            self.error_message = "Height or Width == 0"
            return None
        if fh / fw > 2.5:
            self.error_message = f"H / W > 2.5. Curr: {round(fh / fw , 1)}"
            return None

        total_length = sum(image.shape[1] for image in images)
        scale = total_length / stacked_crops.shape[1]
        return image_utils.resize_scale(stacked_crops, scale=scale, interpolation=cv2.INTER_NEAREST)
