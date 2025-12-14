from PIL import Image, ImageDraw

def process_icon(input_path, output_path):
    print(f"Processing: {input_path}")
    # Load image
    img = Image.open(input_path).convert("RGBA")
    
    # 1. Resize to 512x512
    # User provided a square 1024x1024 image, just resize it down.
    final_size = 512
    img = img.resize((final_size, final_size), Image.Resampling.LANCZOS)
    
    # 2. GNOME Squircle Mask
    mask = Image.new("L", (final_size, final_size), 0)
    draw = ImageDraw.Draw(mask)
    # Radius ~20-25% of size for GNOME look
    draw.rounded_rectangle((0, 0, final_size, final_size), radius=100, fill=255)
    
    # 3. Create final image
    output = Image.new("RGBA", (final_size, final_size), (0, 0, 0, 0))
    output.paste(img, (0, 0), mask=mask)
    
    # Save
    output.save(output_path, "PNG")
    print(f"Processed icon saved to {output_path}")

if __name__ == "__main__":
    # User provided image path
    input_path = "/home/taylan/.gemini/antigravity/brain/5081a95a-8ee7-402b-b493-375ec43a2248/uploaded_image_1765672184203.jpg"
    process_icon(input_path, "assets/icon_processed_final.png")
