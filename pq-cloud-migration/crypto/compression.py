"""
Sensitivity-Adaptive Compression Module
Implements zlib compression with sensitivity levels:
- Low: maximum compression (aggressive, 9)
- Medium: balanced compression (6)
- High: minimal compression (minimal data loss, 1)
"""
import zlib


class Compressor:
    """
    Compresses data based on sensitivity level.
    Higher sensitivity = less compression (preserve data integrity).
    """
    
    SENSITIVITY_LEVELS = {
        "low": 9,      # Maximum compression (for non-sensitive data)
        "medium": 6,   # Balanced compression
        "high": 1      # Minimal compression (for sensitive data)
    }
    
    def compress(self, data: bytes, sensitivity: str = "medium") -> bytes:
        """
        Compress data using zlib with sensitivity-based compression level.
        
        Args:
            data: Raw bytes to compress
            sensitivity: "low", "medium", or "high"
            
        Returns:
            Compressed bytes
        """
        if sensitivity not in self.SENSITIVITY_LEVELS:
            raise ValueError(f"Invalid sensitivity: {sensitivity}. Must be low/medium/high")
        
        level = self.SENSITIVITY_LEVELS[sensitivity]
        compressed = zlib.compress(data, level=level)
        return compressed
    
    def decompress(self, compressed_data: bytes) -> bytes:
        """
        Decompress zlib-compressed data.
        
        Args:
            compressed_data: Compressed bytes
            
        Returns:
            Decompressed original data
        """
        return zlib.decompress(compressed_data)
    
    def get_compression_ratio(self, original_size: int, compressed_size: int) -> float:
        """Calculate compression ratio as percentage."""
        if original_size == 0:
            return 0.0
        return (1 - compressed_size / original_size) * 100
