"""
Frame conversion utilities for converting pypylon frames to OpenCV/numpy formats.
"""

import numpy as np
from typing import Optional
from pypylon import pylon
import cv2


def pylon_image_to_numpy(pylon_image: pylon.PylonImage) -> np.ndarray:
    """
    Convert a pypylon image to a numpy array.
    
    Args:
        pylon_image: pypylon PylonImage object
        
    Returns:
        numpy array representing the image
    """
    # Convert to numpy array
    img = pylon_image.GetArray()
    return img


def pylon_image_to_opencv(pylon_image: pylon.PylonImage) -> np.ndarray:
    """
    Convert a pypylon image to OpenCV format (BGR).
    
    Args:
        pylon_image: pypylon PylonImage object
        
    Returns:
        numpy array in BGR format (OpenCV compatible)
    """
    img = pylon_image_to_numpy(pylon_image)
    
    # Convert pixel format if needed
    pixel_format = pylon_image.GetPixelType()
    
    # Handle different pixel formats
    if pixel_format == pylon.PixelType_Mono8:
        # Grayscale to BGR
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif pixel_format == pylon.PixelType_RGB8packed:
        # RGB to BGR
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    elif pixel_format == pylon.PixelType_BGR8packed:
        # Already BGR
        pass
    elif pixel_format == pylon.PixelType_BayerBG8:
        # Bayer to BGR
        img = cv2.cvtColor(img, cv2.COLOR_BayerBG2BGR)
    elif pixel_format == pylon.PixelType_BayerGB8:
        img = cv2.cvtColor(img, cv2.COLOR_BayerGB2BGR)
    elif pixel_format == pylon.PixelType_BayerGR8:
        img = cv2.cvtColor(img, cv2.COLOR_BayerGR2BGR)
    elif pixel_format == pylon.PixelType_BayerRG8:
        img = cv2.cvtColor(img, cv2.COLOR_BayerRG2BGR)
    else:
        # Default: assume grayscale and convert to BGR
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    
    return img


def grab_result_to_opencv(grab_result: pylon.GrabResult) -> Optional[np.ndarray]:
    """
    Convert a pypylon GrabResult to OpenCV format.
    
    Args:
        grab_result: pypylon GrabResult object
        
    Returns:
        numpy array in BGR format, or None if grab failed
    """
    if not grab_result.GrabSucceeded():
        return None
    
    try:
        # Get pixel format
        pixel_format = grab_result.GetPixelType()
        
        # Convert to PylonImage with format conversion if needed
        converter = pylon.ImageFormatConverter()
        
        # Try to convert to BGR8 if possible
        try:
            converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            pylon_image = converter.Convert(grab_result)
            img = pylon_image_to_numpy(pylon_image)
            
            # Ensure it's BGR (3 channels)
            if len(img.shape) == 2:
                # Grayscale, convert to BGR
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif img.shape[2] == 1:
                # Single channel, convert to BGR
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif img.shape[2] == 4:
                # RGBA, convert to BGR
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            
            return img
            
        except Exception:
            # Fallback: convert directly from grab result
            img = grab_result.GetArray()
            
            # Handle different pixel formats
            if pixel_format == pylon.PixelType_Mono8:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif pixel_format == pylon.PixelType_RGB8packed:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            elif pixel_format in [pylon.PixelType_BayerBG8, pylon.PixelType_BayerGB8,
                                   pylon.PixelType_BayerGR8, pylon.PixelType_BayerRG8]:
                # Bayer pattern, convert to BGR
                if pixel_format == pylon.PixelType_BayerBG8:
                    img = cv2.cvtColor(img, cv2.COLOR_BayerBG2BGR)
                elif pixel_format == pylon.PixelType_BayerGB8:
                    img = cv2.cvtColor(img, cv2.COLOR_BayerGB2BGR)
                elif pixel_format == pylon.PixelType_BayerGR8:
                    img = cv2.cvtColor(img, cv2.COLOR_BayerGR2BGR)
                else:  # BayerRG8
                    img = cv2.cvtColor(img, cv2.COLOR_BayerRG2BGR)
            
            return img
            
    except Exception as e:
        print(f"Frame conversion error: {e}")
        return None


def resize_for_preview(image: np.ndarray, target_width: int = 1920, target_height: int = 1080) -> np.ndarray:
    """
    Resize image for preview display while maintaining aspect ratio.
    
    Args:
        image: Input image as numpy array
        target_width: Target preview width (default: 1920)
        target_height: Target preview height (default: 1080)
        
    Returns:
        Resized image
    """
    if image is None or image.size == 0:
        return image
    
    height, width = image.shape[:2]
    
    # Calculate scaling factor to fit within target dimensions
    scale_w = target_width / width
    scale_h = target_height / height
    scale = min(scale_w, scale_h)
    
    # Calculate new dimensions
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    # Resize image
    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
    
    return resized
