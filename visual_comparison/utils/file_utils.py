import os
import cv2
import glob
from typing import List


__all__ = [
    "get_folders",
    "get_filenames",
    "complete_paths",
]


def get_folders(root, src_folder_name) -> List[str]:
    """
    :param root: Root folder with sub-folders containing images to compare
    :param src_folder_name: Name of source folder
    :return: List of folder names, with source folder as first item
    """
    # Contains method name (folder name)
    folders = [folder for folder in os.listdir(root) if folder[0] != "."]
    if src_folder_name in folders:
        folders.insert(0, folders.pop(folders.index(src_folder_name)))
    return folders


def get_filenames(root: str, folders: List[str]) -> List[str]:
    """
    Get common files from all sub folders in root folder.
    :param root: Root folder with sub-folders containing images to compare
    :param folders: List of folder names in root dir
    :return: A list of common files among all folders
    """
    # Finding common files for comparison, should have the same filename (without extension)
    common_files = None
    for folder in folders:
        folder_path = os.path.join(root, folder)
        file_paths = [os.path.splitext(file_path)[0] for file_path in os.listdir(folder_path) if file_path[0] != "."]
        common_files = set(file_paths) if common_files is None else common_files.intersection(set(file_paths))

    # Contains files with same names across all sub-directories for comparison
    common_files = list(common_files)
    common_files.sort()

    return common_files


def complete_paths(root, folder, common_names):
    paths = []
    for i in range(len(common_names)):
        uncomplete_path = os.path.join(os.path.join(root, folder), common_names[i]) + ".*"
        paths.append(glob.glob(uncomplete_path)[0])

    return paths
