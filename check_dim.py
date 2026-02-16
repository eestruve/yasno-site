import os
import struct

def get_png_dimensions(file_path):
    with open(file_path, 'rb') as f:
        # Check signature
        if f.read(8) != b'\x89PNG\r\n\x1a\n':
            return None
        # Read IHDR chunk
        chunk_len = struct.unpack('>I', f.read(4))[0]
        chunk_type = f.read(4)
        if chunk_type != b'IHDR':
            return None
        # Width and height are 4 bytes each, big-endian
        width = struct.unpack('>I', f.read(4))[0]
        height = struct.unpack('>I', f.read(4))[0]
        return width, height

assets_dir = r"c:\Users\evgen\Desktop\Antigravity\Antigraviti progect\01_Business\Svet\Yasno_Promo_Winter\assets\images"

print(f"{'File':<30} | {'Size (MB)':<10} | {'Dimensions':<15} | {'Est. RAM (MB)':<15}")
print("-" * 80)

total_ram = 0

for root, dirs, files in os.walk(assets_dir):
    for file in files:
        if file.lower().endswith('.png'):
            path = os.path.join(root, file)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            dims = get_png_dimensions(path)
            
            if dims:
                w, h = dims
                # 4 bytes per pixel (RGBA)
                ram_usage = (w * h * 4) / (1024 * 1024) 
                total_ram += ram_usage
                print(f"{file:<30} | {size_mb:<10.2f} | {f'{w}x{h}':<15} | {ram_usage:<15.2f}")

print("-" * 80)
print(f"Total Estimated RAM for decoding: {total_ram:.2f} MB")
