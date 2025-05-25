# create_placeholders.py
import os
from PIL import Image, ImageDraw, ImageFont
import random

def create_placeholder_image(filename, text="Sample Chart", width=800, height=600):
    """
    Create a placeholder image with text
    
    :param filename: Output filename
    :param text: Text to display on the image
    :param width: Image width
    :param height: Image height
    """
    # Create a new image with a random background color
    r = random.randint(200, 240)
    g = random.randint(200, 240)
    b = random.randint(200, 240)
    image = Image.new('RGB', (width, height), color=(r, g, b))
    
    # Get a drawing context
    draw = ImageDraw.Draw(image)
    
    # Draw a border
    draw.rectangle([(10, 10), (width - 10, height - 10)], outline=(100, 100, 100), width=2)
    
    # Draw some random chart elements
    chart_type = random.choice(["bar", "line", "pie"])
    
    if chart_type == "bar":
        # Draw bar chart
        num_bars = random.randint(4, 8)
        bar_width = (width - 100) / num_bars
        for i in range(num_bars):
            bar_height = random.randint(50, height - 150)
            x1 = 50 + i * bar_width
            y1 = height - 50 - bar_height
            x2 = x1 + bar_width - 10
            y2 = height - 50
            draw.rectangle([(x1, y1), (x2, y2)], fill=(random.randint(100, 200), 
                                                      random.randint(100, 200), 
                                                      random.randint(100, 200)))
    elif chart_type == "line":
        # Draw line chart
        num_points = random.randint(5, 10)
        points = []
        for i in range(num_points):
            x = 50 + i * ((width - 100) / (num_points - 1))
            y = random.randint(100, height - 150)
            points.append((x, y))
        
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=(random.randint(50, 150), 
                                                     random.randint(50, 150), 
                                                     random.randint(50, 150)), width=3)
    else:  # pie chart
        # Draw pie chart
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 3
        
        # Draw several pie slices
        start_angle = 0
        for i in range(random.randint(3, 6)):
            angle = random.randint(20, 120)
            draw.pieslice([(center_x - radius, center_y - radius), 
                          (center_x + radius, center_y + radius)], 
                          start=start_angle, end=start_angle + angle, 
                          fill=(random.randint(100, 200), 
                               random.randint(100, 200), 
                               random.randint(100, 200)))
            start_angle += angle
    
    # Draw title text
    # Use default font if no font specified
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        font = ImageFont.load_default()
    
    # Get the size of the text
    text_width, text_height = draw.textsize(text, font=font) if hasattr(draw, 'textsize') else (200, 30)
    
    # Calculate the position to center the text
    text_x = (width - text_width) // 2
    text_y = 30
    
    # Draw the text
    draw.text((text_x, text_y), text, fill=(0, 0, 0), font=font)
    
    # Save the image
    image.save(filename)
    print(f"Created placeholder image: {filename}")

def create_sample_placeholders():
    """Create all needed placeholder images for sample data"""
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    # Create placeholder images for tasks
    create_placeholder_image(
        os.path.join(uploads_dir, 'digital_games_chart.png'),
        text="Global Sales of Digital Games (2000-2006)",
        width=800, height=500
    )
    
    create_placeholder_image(
        os.path.join(uploads_dir, 'poverty_australia_table.png'),
        text="Poverty in Australia (1999)",
        width=800, height=500
    )
    
    create_placeholder_image(
        os.path.join(uploads_dir, 'uk_commuters_graph.png'),
        text="UK Commuters by Transport Mode (1970-2030)",
        width=800, height=500
    )
    
    # Create placeholder image for sample exercise
    create_placeholder_image(
        os.path.join(uploads_dir, 'sample_chart.png'),
        text="Sample Chart for Exercise",
        width=800, height=500
    )
    
    print("All placeholder images created successfully!")

if __name__ == "__main__":
    create_sample_placeholders()