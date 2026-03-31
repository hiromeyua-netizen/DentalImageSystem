"""
Frame conversion utilities for converting pypylon frames to OpenCV/numpy formats.
"""

from typing import Optional

import cv2
import numpy as np
from pypylon import pylon


def pylon_image_to_numpy(pylon_image: pylon.PylonImage) -> np.ndarray:
    """Convert a pypylon image to a numpy array."""
    return pylon_image.GetArray()


def pylon_image_to_opencv(pylon_image: pylon.PylonImage) -> np.ndarray:
    """Convert a pypylon image to OpenCV format (BGR)."""
    img = pylon_image_to_numpy(pylon_image)

    pixel_format = pylon_image.GetPixelType()

    if pixel_format == pylon.PixelType_Mono8:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif pixel_format == pylon.PixelType_RGB8packed:
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    elif pixel_format == pylon.PixelType_BGR8packed:
        pass
    elif pixel_format == pylon.PixelType_BayerBG8:
        img = cv2.cvtColor(img, cv2.COLOR_BayerBG2BGR)
    elif pixel_format == pylon.PixelType_BayerGB8:
        img = cv2.cvtColor(img, cv2.COLOR_BayerGB2BGR)
    elif pixel_format == pylon.PixelType_BayerGR8:
        img = cv2.cvtColor(img, cv2.COLOR_BayerGR2BGR)
    elif pixel_format == pylon.PixelType_BayerRG8:
        img = cv2.cvtColor(img, cv2.COLOR_BayerRG2BGR)
    else:
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    return img


def grab_result_to_opencv(grab_result: pylon.GrabResult) -> Optional[np.ndarray]:
    """Convert a pypylon GrabResult to OpenCV format (BGR)."""
    if not grab_result.GrabSucceeded():
        return None

    converter = pylon.ImageFormatConverter()
    converter.OutputPixelFormat = pylon.PixelType_BGR8packed
    converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

    pylon_image = converter.Convert(grab_result)
    return pylon_image_to_numpy(pylon_image)


def resize_for_preview(
    image: np.ndarray, target_width: int = 1920, target_height: int = 1080
) -> np.ndarray:
    """Resize image for preview display while maintaining aspect ratio."""
    if image is None or image.size == 0:
        return image

    height, width = image.shape[:2]

    if width <= target_width and height <= target_height:
        return image

    scale_w = target_width / width
    scale_h = target_height / height
    scale = min(scale_w, scale_h)

    new_width = int(width * scale)
    new_height = int(height * scale)

    if scale < 0.5:
        interpolation = cv2.INTER_LANCZOS4
    else:
        interpolation = cv2.INTER_CUBIC

    return cv2.resize(image, (new_width, new_height), interpolation=interpolation)
