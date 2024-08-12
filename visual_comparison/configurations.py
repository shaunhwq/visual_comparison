"""
config_info[section][section_key] = {
    obj => Type of customtkinter object to create in settings widget. See widget_settings.py
    type  => parse type (conversion from string to int, etc.)
    values => [Optional] only for obj=='options' since we need to populate CtkOptionsMenu with values
    default => Default value for settings
"""
import cv2
import configparser


__all__ = ["config_info", "read_config", "write_config", "parse_config"]


# Only added the common interpolation types.
CV2_INTERPOLATION_TYPES = [
    "cv2.INTER_AREA",
    "cv2.INTER_LINEAR",
    "cv2.INTER_NEAREST",
    "cv2.INTER_CUBIC",
]
DISPLAY_INTERPOLATION_TYPES = CV2_INTERPOLATION_TYPES + ["None"]
ZOOM_INTERPOLATION_TYPES = CV2_INTERPOLATION_TYPES

# Contains information on config.ini file, e.g. how to parse, default values for each. Possible options.
config_info = dict(
    Appearance=dict(
        mode=dict(obj="options", type=str, values=["System", "Dark", "Light"], default="System"),
        theme=dict(obj="options", type=str, values=["blue", "green", "dark-blue"], default="dark-blue"),
    ),
    Display=dict(
        interpolation_type=dict(obj="options", type=eval, values=DISPLAY_INTERPOLATION_TYPES, default="cv2.INTER_LINEAR"),
        fast_loading_threshold_ms=dict(obj="entry", type=int, default=100),
        ctk_corner_radius=dict(obj="entry", type=int, default=3),
        search_grid_preview_row_height=dict(obj="options", type=int, values=["75", "100", "125"], default="75")
    ),
    Zoom=dict(
        interpolation_type=dict(obj="options", type=eval, values=ZOOM_INTERPOLATION_TYPES, default="cv2.INTER_NEAREST"),
    ),
    Functionality=dict(
        max_fps=dict(obj="entry", type=int, default=60),
        reduce_cpu_usage_in_background=dict(obj="options", type=bool, values=["true", "false"], default="true"),
    ),
    Keybindings=dict(
        prev_file=dict(obj="entry", type=str, default="a"),
        next_file=dict(obj="entry", type=str, default="d"),
        prev_file_alternate=dict(obj="entry", type=str, default="<Left>"),
        next_file_alternate=dict(obj="entry", type=str, default="<Right>"),
        pause_video=dict(obj="entry", type=str, default="<space>"),
        prev_method=dict(obj="entry", type=str, default="z"),
        next_method=dict(obj="entry", type=str, default="c"),
        prev_method_alternate=dict(obj="entry", type=str, default="<Up>"),
        next_method_alternate=dict(obj="entry", type=str, default="<Down>"),
        skip_to_1_frame_before=dict(obj="entry", type=str, default="-"),
        skip_to_1_frame_after=dict(obj="entry", type=str, default="="),
        skip_to_10_frame_before=dict(obj="entry", type=str, default="_"),
        skip_to_10_frame_after=dict(obj="entry", type=str, default="+"),
    ),
    Color=dict(
        correct_h264_bt709=dict(obj="options", type=bool, values=["true", "false"], default="false")
    )
)


def read_config(configuration_path: str) -> configparser.ConfigParser:
    """
    Reads configuration file.
    :param configuration_path: Path to configuration file
    :return: configparser object
    """
    config_parser = configparser.ConfigParser()
    config_parser.read(configuration_path)
    return config_parser


def write_config(configuration_path: str, new_configuration: configparser.ConfigParser) -> None:
    """
    Writes new configuration to the config file
    :param configuration_path: Path to configuration file
    :param new_configuration: Configparser object with updated configurations
    :return: None
    """
    with open(configuration_path, "w") as config_file:
        new_configuration.write(config_file)


def parse_config(config_parser: configparser.ConfigParser) -> dict:
    """
    :param config_parser: Configparser object to parse
    :return: Parsed configuration
    """
    configuration = {}
    for section in config_parser.sections():
        configuration[section] = {}

        for key in config_parser[section].keys():
            config_value = config_parser[section][key]
            config_type = config_info[section][key]["type"]
            configuration[section][key] = config_type(config_value)
            if config_type is bool:
                configuration[section][key] = config_value == "true"

    return configuration
