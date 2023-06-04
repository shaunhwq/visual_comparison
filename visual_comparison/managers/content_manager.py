import os
import glob
from typing import List
from concurrent.futures import ThreadPoolExecutor

import cv2
from tqdm import tqdm

from ..utils import file_utils
from ..utils import file_reader


__all__ = ["ContentManager"]


class ContentManager:
    def __init__(self, root, src_folder_name):
        self.root = root
        self.src_folder_name = src_folder_name

        self.methods = file_utils.get_folders(root, src_folder_name)
        self.files = file_utils.get_filenames(root, self.methods)

        self.content_loaders = None
        self.video_indices = []

        self.current_index = 0
        self.current_methods = list(self.methods)
        self.current_files = list(self.files)

        # Could use pandas but don't want to introduce dependency
        self.data = []
        self.thumbnails = []
        self.data_titles = ["S/N", "File Path", "Height", "Width", "Frame Count", "FPS"]
        # Collect and store file information. Time vs memory trade off. Reduce wait for many files.
        self.get_data()

    def get_data(self):
        if not (len(self.methods) > 0 and len(self.files) > 0):
            return

        # Load images for preview window. Multi thread for faster reading.
        file_paths = file_utils.complete_paths(self.root, self.src_folder_name, self.files)

        with ThreadPoolExecutor() as executor:
            return_values = tqdm(iterable=executor.map(self.load_file_info, file_paths),
                                 desc="Loading file info...",
                                 total=len(file_paths))

        for idx, (thumbnail, data) in enumerate(return_values):
            self.thumbnails.append(thumbnail)
            self.data.append([idx] + data)

    @staticmethod
    def load_file_info(file_path, max_height=75):
        cap = file_reader.read_media_file(file_path)
        ret, img = cap.read()

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, _ = img.shape
        scale = max_height / h
        thumbnail = cv2.resize(img, (int(w * scale), int(h * scale)))

        data = [os.path.splitext(os.path.basename(file_path))[0], h, w]
        if isinstance(cap, cv2.VideoCapture):
            data.append(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            data.append(round(cap.get(cv2.CAP_PROP_FPS), 2))

        cap.release()
        return thumbnail, data

    def get_paths(self) -> List[str]:
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

    def load_files(self, paths):
        self.content_loaders = []
        self.video_indices = []
        for file_idx, file in enumerate(paths):
            cap = file_reader.read_media_file(file)
            self.content_loaders.append(cap)
            if isinstance(cap, cv2.VideoCapture):
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
        content_paths = self.get_paths()

        def seek_video(vid_idx, no_frames, in_future):
            if not in_future:
                self.content_loaders[vid_idx] = file_reader.read_media_file(content_paths[vid_idx])
            for i in range(no_frames):
                self.content_loaders[vid_idx].grab()

        if not self.has_video():
            return

        first_cap = self.content_loaders[self.video_indices[0]]
        current_position = int(first_cap.get(cv2.CAP_PROP_POS_FRAMES))

        is_in_future = current_position < frame_no
        number_frames = frame_no - current_position if is_in_future else frame_no

        # TODO: Might not be best solution, need to check if we can use threads to speed up this IO task
        for video_idx in self.video_indices:
            seek_video(video_idx, number_frames, is_in_future)

    def get_video_position(self):
        if not self.has_video():
            return 0

        cap = self.content_loaders[self.video_indices[0]]
        video_position = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        video_length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        return video_position, video_length, video_fps

    def read_frames(self):
        outputs = [cap.read() for cap in self.content_loaders]
        # todo: assess performance for this
        # for cap in self.content_loaders:
        #     cap.get()
        # outputs = [cap.retrieve() for cap in self.content_loaders]
        rets = [out[0] for out in outputs]
        frames = [out[1] for out in outputs]
        return all(rets), frames
