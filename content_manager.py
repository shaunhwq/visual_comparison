import cv2
import os


def get_methods(root, src_folder_name):
    # Contains method name (folder name)
    methods = [folder for folder in os.listdir(root) if folder[0] != "."]
    if src_folder_name in methods:
        methods.insert(0, methods.pop(methods.index(src_folder_name)))
    assert len(methods) > 1, "Need more than 1 folder for comparison"
    return methods


def get_filenames(root, folders):
    # Finding common files for comparison, should have the same filename (without extension)
    common_files = None
    for folder in folders:
        folder_path = os.path.join(root, folder)
        file_paths = [os.path.splitext(file_path)[0] for file_path in os.listdir(folder_path) if file_path[0] != "."]
        common_files = set(file_paths) if common_files is None else common_files.intersection(set(file_paths))

    # Contains files with same names across all sub-directories for comparison
    assert common_files, "No files in common"
    common_files = list(common_files)
    common_files.sort()

    return common_files


class ImageCapture:
    """
    TODO: Handle HDR Reading too later?
    """
    def __init__(self, image_path):
        self.image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

    def read(self):
        if self.image is None:
            return False, None
        return True, self.image.copy()


class ContentManager:
    def __init__(self, root, src_folder_name):
        self.methods = get_methods(root, src_folder_name)
        self.files = get_filenames(root, self.methods)

        self.content_loaders = None
        self.video_indices = []

    def load_files(self, paths):
        self.content_loaders = []
        self.video_indices = []
        for file_idx, file in enumerate(paths):
            extension = os.path.splitext(file)[-1].lower()
            if extension in {".jpg", ".png", ".hdr"}:
                self.content_loaders.append(ImageCapture(file))
            elif extension in {".mp4"}:
                self.content_loaders.append(cv2.VideoCapture(file))
                self.video_indices.append(file_idx)
            else:
                raise NotImplementedError(f"Ext not supported: {extension} for file {file}")

    def has_video(self):
        return len(self.video_indices) != 0

    def set_video_position(self, value):
        if not self.has_video():
            return

        first_cap = self.content_loaders[self.video_indices[0]]
        video_position = int(value / 100 * first_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        for video_idx in self.video_indices:
            cap = self.content_loaders[video_idx]
            cap.set(cv2.CAP_PROP_POS_FRAMES, video_position)

    def get_video_position(self):
        if not self.has_video():
            return 0

        cap = self.content_loaders[self.video_indices[0]]
        video_position = cap.get(cv2.CAP_PROP_POS_FRAMES)
        video_length = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        return video_position / video_length * 100

    def read_frames(self):
        outputs = [cap.read() for cap in self.content_loaders]
        rets = [out[0] for out in outputs]
        frames = [out[1] for out in outputs]
        return all(rets), frames
