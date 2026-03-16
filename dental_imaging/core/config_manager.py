"""
Configuration manager for loading and managing application settings.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dental_imaging.models.camera_config import CameraConfig


class ConfigManager:
    """Manages application configuration loading and access."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory containing config files. Defaults to project config/ directory.
        """
        if config_dir is None:
            # Get project root (assuming this file is in dental_imaging/core/)
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = config_dir
        self._default_config: Optional[Dict[str, Any]] = None
        self._camera_config: Optional[CameraConfig] = None
    
    def load_default_config(self) -> Dict[str, Any]:
        """
        Load default application configuration.
        
        Returns:
            Dictionary with application settings
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid
        """
        config_path = self.config_dir / "default_config.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self._default_config = json.load(f)
        
        return self._default_config
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration (loads if not already loaded).
        
        Returns:
            Dictionary with application settings
        """
        if self._default_config is None:
            self.load_default_config()
        
        return self._default_config
    
    def load_camera_config(self) -> CameraConfig:
        """
        Load camera configuration.
        
        Returns:
            CameraConfig object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid
        """
        config_path = self.config_dir / "camera_defaults.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        self._camera_config = CameraConfig.from_dict(config_dict)
        return self._camera_config
    
    def get_camera_config(self) -> CameraConfig:
        """
        Get camera configuration (loads if not already loaded).
        
        Returns:
            CameraConfig object
        """
        if self._camera_config is None:
            self.load_camera_config()
        
        return self._camera_config
    
    def get_preview_resolution(self) -> tuple[int, int]:
        """
        Get preview resolution from config.
        
        Returns:
            Tuple of (width, height)
        """
        config = self.get_default_config()
        preview = config.get("preview", {})
        resolution = preview.get("resolution", {})
        return (resolution.get("width", 1920), resolution.get("height", 1080))
    
    def get_capture_resolution(self) -> tuple[int, int]:
        """
        Get capture resolution from config.
        
        Returns:
            Tuple of (width, height)
        """
        config = self.get_default_config()
        capture = config.get("capture", {})
        resolution = capture.get("resolution", {})
        return (resolution.get("width", 4024), resolution.get("height", 3036))
