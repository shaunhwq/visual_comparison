import os
import glob
from typing import List
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat

import cv2
from tqdm import tqdm

from ..utils import file_utils
from ..utils import file_reader
from ..utils import VideoCapture, get_video_information


__all__ = ["ContentManager"]


class ContentManager:
    def __init__(self, root: str, preview_folder: str, require_color_conversion: bool):
        """
        :param require_color_conversion: If True, we need to extract metadata information (so we know whether to do correction or change color spaces)
        """
        self.root = root
        self.preview_folder = preview_folder
        self.require_color_conversion = require_color_conversion

        self.methods = file_utils.get_folders(root, preview_folder)
        self.files = file_utils.get_filenames(root, self.methods)

        self.content_loaders = None
        self.video_indices = []

        self.current_index = 0
        self.current_methods = list(self.methods)
        self.current_files = list(self.files)

        self.metadata = dict()
        if require_color_conversion:
            self._init_get_metadata()
        self.current_metadata = dict(self.metadata)

        # Could use pandas but don't want to introduce dependency
        self.data = []
        self.thumbnails = []
        self.data_titles = ["S/N", "File Path", "Height", "Width", "Frame Count", "FPS"]

        # For fast image reading
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Collect and store file information. Time vs memory trade off. Reduce wait for many files.
        self._init_get_data()


    def __exit__(self, exc_type, exc_val, exc_tb):
        self.executor.shutdown(wait=False)

    def _init_get_metadata(self):
        """
        Called during initialization.
        Retrieves metadata for all files to compare.
        """
        for method in self.methods:
            method_files = file_utils.complete_paths(self.root, method, self.files)
            with ThreadPoolExecutor() as executor:
                self.metadata[method] = list(tqdm(executor.map(get_video_information, method_files), total=len(method_files), desc=f"Loading metadata for {method}..."))

    def _init_get_data(self):
        """
        Called during initialization.
        Retrieves info needed for preview like file information and in self.data_titles info.
        """
        if not (len(self.methods) > 0 and len(self.files) > 0):
            return

        # Load images for preview window. Multi thread for faster reading.
        file_paths = file_utils.complete_paths(self.root, self.preview_folder, self.files)
        metadata = self.metadata[self.preview_folder] if self.require_color_conversion else [None] * len(file_paths)

        return_values = tqdm(
            iterable=self.executor.map(self._init_load_file_info, file_paths, metadata),
            desc="Loading file info...",
            total=len(file_paths)
        )

        for idx, (thumbnail, data) in enumerate(return_values):
            self.thumbnails.append(thumbnail)
            self.data.append([idx] + data)

    @staticmethod
    def _init_load_file_info(file_path, metadata, max_height=75):
        cap = file_reader.read_media_file(file_path, metadata)
        ret, img = cap.read()

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, _ = img.shape
        scale = max_height / h
        thumbnail = cv2.resize(img, (int(w * scale), int(h * scale)))

        data = [os.path.splitext(os.path.basename(file_path))[0], h, w]
        if isinstance(cap, VideoCapture):
            data.append(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            data.append(round(cap.get(cv2.CAP_PROP_FPS), 2))

        cap.release()
        return thumbnail, data

    def _get_current_paths(self) -> List[str]:
        """
        Get path to files for currently selected methods and files
        :return: List of paths
        """
        output_paths = []
        # TODO: Optimize. I think this is a O(n^2) method, if we use dict to map could reduce to O(n)
        for method in self.current_methods:
            incomplete_path = os.path.join(self.root, method, self.current_files[self.current_index])
            completed_paths = glob.glob(incomplete_path + ".*")
            assert len(completed_paths) == 1, completed_paths
            output_paths.append(completed_paths[0])

        return output_paths

    def _get_current_metadata(self) -> List[dict]:
        metadata = []
        for method in self.current_methods:
            value = None if not self.require_color_conversion else self.current_metadata[method][self.current_index]
            metadata.append(value)
        return metadata

    def set_current_files(self, indices: List[int]):
        self.current_files = [self.files[i] for i in indices]

        self.current_metadata = {}
        for method in self.methods:
            self.current_metadata[method] = list([self.metadata[method][i] for i in indices])

    def on_prev(self):
        self.current_index = max(0, self.current_index - 1)

    def on_next(self):
        self.current_index = min(len(self.current_files) - 1, self.current_index + 1)

    def on_specify_index(self, value):
        if value is None:
            return False
        if not (0 <= value < len(self.current_files)):
            return False

        self.current_index = value
        return True

    def get_title(self):
        return f"[{self.current_index}/{len(self.current_files) - 1}] {self.current_files[self.current_index]}"

    def load_single_file(self):
        """
        :returns: VideoCapture or ImageCapture object
        """
        current_paths = self._get_current_paths()
        current_metadata = self._get_current_metadata()
        return file_reader.read_media_file(current_paths[0], current_metadata[0])

    def load_files(self):
        self.content_loaders = []
        self.video_indices = []

        current_paths = self._get_current_paths()
        current_metadata = self._get_current_metadata()
        for file_idx, (file, metadata) in enumerate(zip(current_paths, current_metadata)):
            cap = file_reader.read_media_file(file, metadata)
            self.content_loaders.append(cap)
            if isinstance(cap, VideoCapture):
                self.video_indices.append(file_idx)

    def has_video(self):
        return len(self.video_indices) != 0

    def set_video_position(self, frame_no):
        """
        # https://github.com/opencv/opencv/issues/9053
        cap.grab() mentioned to be the solution for now.

        Will be slow when want to adjust frames to position before current idx.
        E.g. current = frame 50, desired = frame 10
        """
        content_paths = self._get_current_paths()
        content_metadata = self._get_current_metadata()

        def seek_video(vid_idx, no_frames, in_future):
            if not in_future:
                self.content_loaders[vid_idx] = file_reader.read_media_file(content_paths[vid_idx], content_metadata[vid_idx])
            for i in range(no_frames):
                self.content_loaders[vid_idx].grab()

        if not self.has_video():
            return

        first_cap = self.content_loaders[self.video_indices[0]]
        current_position = int(first_cap.get(cv2.CAP_PROP_POS_FRAMES))

        is_in_future = current_position <= frame_no
        number_frames = frame_no - current_position if is_in_future else frame_no

        # TODO: Might not be best solution, need to check if we can use threads to speed up this IO task
        for video_idx in self.video_indices:
            seek_video(video_idx, number_frames, is_in_future)

    def get_video_position(self):
        if not self.has_video():
            raise RuntimeError("Should not be calling this when there are no videos")

        cap = self.content_loaders[self.video_indices[0]]
        video_position = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        return video_position, video_length, video_fps

    def read_frames(self):
        outputs = list(self.executor.map(lambda cap: cap.read(), self.content_loaders))
        rets = [out[0] for out in outputs]
        frames = [out[1] for out in outputs]
        return all(rets), frames
