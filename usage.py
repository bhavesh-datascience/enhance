import argparse
import cv2
import numpy as np
import os
from datetime import datetime
from gfpgan import GFPGANer
from PIL import Image

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, required=True, help='Input image path (already with background removed)')
    parser.add_argument('-s', '--upscale', type=int, default=2, help='Upscaling factor (1-4)')
    parser.add_argument('-w', '--weight', type=float, default=0.5, help='Enhancement strength (0-1)')
    args = parser.parse_args()

    # Create output directory
    os.makedirs('done', exist_ok=True)

    # Set up GFPGAN with fixed version
    model_url = 'https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.3.pth'
    restorer = GFPGANer(
        model_path=model_url,
        upscale=args.upscale,
        arch='clean',
        channel_multiplier=2,
        bg_upsampler=None
    )

    # Process the image (it should have already had its background removed)
    img = cv2.imread(args.input, cv2.IMREAD_UNCHANGED)  # Read image with transparency (alpha channel)

    # Check if the image has an alpha channel (transparency)
    if img.shape[2] == 4:
        # Separate the alpha channel
        alpha_channel = img[:, :, 3]
        # Convert the image to RGB (ignore the alpha channel for enhancement)
        img_rgb = img[:, :, :3]
    else:
        # If no alpha channel, treat as a normal RGB image
        alpha_channel = None
        img_rgb = img

    # Apply face enhancement only on the non-transparent areas (face region)
    _, _, restored_img = restorer.enhance(
        img_rgb,
        has_aligned=False,               # Skip alignment for better quality
        only_center_face=False,         # Don't restrict to the center
        paste_back=False,                 # Paste the enhanced face back
        weight=args.weight              # Weight for the enhancement strength
    )

    # If alpha channel exists, reapply it to the enhanced image to preserve transparency
    if alpha_channel is not None:
        # Ensure the alpha channel is the correct size and depth (8-bit)
        alpha_channel = cv2.cvtColor(alpha_channel, cv2.COLOR_GRAY2BGR)
        alpha_channel = alpha_channel[:, :, 0]  # Make sure it's a single channel for merging

        # Ensure restored_img and alpha_channel have the same size
        if restored_img.shape[:2] != alpha_channel.shape[:2]:
            restored_img = cv2.resize(restored_img, (alpha_channel.shape[1], alpha_channel.shape[0]))

        # Merge the enhanced image with the alpha channel to preserve transparency
        restored_img = cv2.merge([restored_img[:, :, 0], restored_img[:, :, 1], restored_img[:, :, 2], alpha_channel])

    # Generate timestamp for the output filename
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S_") + f"{now.microsecond // 1000:03d}"
    output_name = f"enhanced_{timestamp}.png"
    output_path = os.path.join('done', output_name)

    # Save the final result (with transparency preserved)
    cv2.imwrite(output_path, restored_img)
    print(f"Saved enhanced image: {output_path}")

if __name__ == '__main__':
    main()
