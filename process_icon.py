from PIL import Image, ImageDraw, ImageFilter
import os

def process_icon(input_path, output_path):
    # Load image
    img = Image.open(input_path).convert("RGBA")
    
    # Get bounding box of non-transparent and non-white pixels
    # We want to find the main dark content
    gray = img.convert("L")
    # Threshold to find non-white content
    bbox = img.getbbox()
    
    if bbox:
        # Crop to the actual content (the black box)
        img = img.crop(bbox)
        
    # Resize the content to fill the 512x512 canvas entirely (Full Bleed)
    final_size = 512
    img = img.resize((final_size, final_size), Image.Resampling.LANCZOS)
    
    # GNOME Squircle Mask
    # Creating a proper superellipse mask
    mask = Image.new("L", (final_size, final_size), 0)
    draw = ImageDraw.Draw(mask)
    
    # Draw rounded rectangle with slightly tighter radius for GNOME style
    # GNOME icons usually fill the canvas
    draw.rounded_rectangle((0, 0, final_size, final_size), radius=120, fill=255)
    
    # Create final image
    output = Image.new("RGBA", (final_size, final_size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask=mask)
    
    # Save
    output.save(output_path, "PNG")
    print(f"Processed icon saved to {output_path}")

if __name__ == "__main__":
    process_icon("assets/icon.png", "assets/icon_processed.png")
