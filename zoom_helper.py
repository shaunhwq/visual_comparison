import cv2
import numpy as np

import image_utils


class ZoomHelper:
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

    def on_mouse_move(self, event):
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

    def reset(self, event=None):
        self.zoom_bbox_pts = []
        self.zoom_box_frozen = False
        self.error_message = ""

    def on_l_mouse_click(self, event):
        if len(self.zoom_bbox_pts) == 2:
            self.zoom_box_frozen = not self.zoom_box_frozen
        else:
            self.zoom_bbox_pts.append(self.display_widget.mouse_position)

    def _get_crop_region(self, image_size):
        # X = horizontal, Y = Vertical, (0, 0) top left corner
        h, w, c = image_size
        pt1_x, pt1_y = self.zoom_bbox_pts[0]
        pt2_x, pt2_y = self.zoom_bbox_pts[1]
        start_x, start_y = min(pt1_x, pt2_x), min(pt1_y, pt2_y)
        start_x, start_y = max(0, start_x), max(0, start_y)  # Handle < 0 case
        width, height = abs(pt1_x - pt2_x), abs(pt1_y - pt2_y)

        if start_x + width > w:
            start_x = w - width
        if start_y + height > h:
            start_y = h - height

        return start_x, start_y, width, height

    def highlight_zoom_region(self, image, num_images=1, color=(123, 80, 36)):
        image_shape = image.shape if num_images == 1 else [image.shape[0], image.shape[1] // num_images, image.shape[2]]

        # Marker so they can estimate box size
        if len(self.zoom_bbox_pts) == 1:
            cv2.circle(image, self.zoom_bbox_pts[0], 3, color, -1)

        # Draw rect
        if len(self.zoom_bbox_pts) == 2:
            # Draw on first image
            x, y, w, h = self._get_crop_region(image_shape)
            pt1, pt2 = (x, y), (x + w, y + h)
            cv2.rectangle(image, pt1, pt2, color, 2)
            if self.zoom_box_frozen:
                cv2.rectangle(image, pt1, pt2, (255, 255, 255), 1)

            # Replicate on others
            for i in range(1, num_images):
                offset_x, offset_y = i * image_shape[1], 0
                pt1, pt2 = (x + i + offset_x, y + offset_y), (x + offset_x + w, y + offset_y + h)
                cv2.rectangle(image, pt1, pt2, (128, 255, 64), 2)

        return image

    def write_err_msgs(self, image, color=(0, 0, 255)):
        if self.error_message == "":
            return image

        image_utils.put_text(image, self.error_message, fg_color=color, background=25)
        return image

    def crop_selected_region(self, images):
        """
        :param images: Image to crop
        :param mode:
        :param num_images:
        :return:
        """
        if len(self.zoom_bbox_pts) != 2:
            return None

        # Crop selected region from the images
        cropped_regions = []
        for image in images:
            start_x, start_y, width, height = self._get_crop_region(image.shape)
            cropped = image[start_y: start_y + height, start_x: start_x + width, :]
            cropped_regions.append(cropped)
        final_image = np.hstack(cropped_regions)

        # Handle invalid crop
        fh, fw, fc = final_image.shape
        if min(fh, fw) == 0:
            self.error_message = "Height or Width == 0"
            return None
        if fh / fw > 2.5:
            self.error_message = f"H / W > 2.5. Curr: {round(fh / fw , 1)}"
            return None

        total_length = sum(image.shape[1] for image in images)
        resized = image_utils.resize_scale(final_image, total_length / final_image.shape[1], interpolation=cv2.INTER_NEAREST)

        return resized
