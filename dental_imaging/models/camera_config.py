"""
Camera configuration model.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Resolution:
    """Image resolution configuration."""
    width: int
    height: int
    
    def __repr__(self) -> str:
        return f"{self.width}x{self.height}"


@dataclass
class ExposureConfig:
    """Exposure configuration."""
    auto: bool = False
    value: int = 10000  # in microseconds
    
    def validate(self) -> None:
        """Validate exposure settings."""
        if not self.auto and self.value < 0:
            raise ValueError("Exposure value must be non-negative")


@dataclass
class GainConfig:
    """Gain configuration."""
    auto: bool = False
    value: float = 1.0
    
    def validate(self) -> None:
        """Validate gain settings."""
        if not self.auto and self.value < 0:
            raise ValueError("Gain value must be non-negative")


@dataclass
class WhiteBalanceConfig:
    """White balance configuration."""
    auto: bool = True


@dataclass
class CameraConfig:
    """Complete camera configuration."""
    resolution: Resolution
    exposure: ExposureConfig
    gain: GainConfig
    white_balance: WhiteBalanceConfig
    frame_rate: int = 30
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.exposure.validate()
        self.gain.validate()
        
        if self.frame_rate <= 0:
            raise ValueError("Frame rate must be positive")
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'CameraConfig':
        """
        Create CameraConfig from dictionary.
        
        Args:
            config_dict: Dictionary with camera configuration
            
        Returns:
            CameraConfig instance
        """
        resolution = Resolution(
            width=config_dict["resolution"]["width"],
            height=config_dict["resolution"]["height"]
        )
        
        exposure = ExposureConfig(
            auto=config_dict["exposure"]["auto"],
            value=config_dict["exposure"]["value"]
        )
        
        gain = GainConfig(
            auto=config_dict["gain"]["auto"],
            value=config_dict["gain"]["value"]
        )
        
        white_balance = WhiteBalanceConfig(
            auto=config_dict["white_balance"]["auto"]
        )
        
        frame_rate = config_dict.get("frame_rate", 30)
        
        return cls(
            resolution=resolution,
            exposure=exposure,
            gain=gain,
            white_balance=white_balance,
            frame_rate=frame_rate
        )
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "resolution": {
                "width": self.resolution.width,
                "height": self.resolution.height
            },
            "exposure": {
                "auto": self.exposure.auto,
                "value": self.exposure.value
            },
            "gain": {
                "auto": self.gain.auto,
                "value": self.gain.value
            },
            "white_balance": {
                "auto": self.white_balance.auto
            },
            "frame_rate": self.frame_rate
        }
