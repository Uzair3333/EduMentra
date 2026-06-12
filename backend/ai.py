"""AI-powered study tools using Groq API.

This module provides functionality for:
- Generating AI-powered quizzes
- Analyzing study material from images
- Extracting key concepts from study notes
"""

import re
import json
import base64
import io
from groq import Groq
from PIL import Image
import os
from dotenv import load_dotenv


load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
# Initialize one single client for everything
client = Groq(api_key=GROQ_API_KEY)

# --- 📝 QUIZ GENERATION (Llama 3.3) ---
def generate_quiz_from_ai(topic_name: str) -> list | None:
    """Generate an AI-powered 5-question quiz for a given topic.
    
    Args:
        topic_name: The name of the topic to generate quiz questions for
        
    Returns:
        A list of quiz question dictionaries with 'question', 'options', and 'answer' keys.
        Returns None if generation fails.
    """
    prompt = f"""
    Create a 5-question multiple choice quiz about '{topic_name}'.
    Return the response ONLY as a JSON object with a key named 'quiz'.
    Format:
    {{
      "quiz": [
        {{
          "question": "The question text?",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "answer": "The exact string of the correct option"
        }}
      ]
    }}
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a teacher who only outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("quiz", [])
    except json.JSONDecodeError as e:
        print(f"JSON parsing error in quiz generation: {e}")
        return None
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return None

# --- 📸 IMAGE ANALYSIS (LLaVA) ---
def encode_image(image_path: str) -> str:
    """Convert an image file to base64 encoding with aggressive compression.
    
    Compresses the image to reduce payload size and avoid request entity 
    too large errors from the API.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64-encoded string representation of the compressed image
        
    Raises:
        FileNotFoundError: If the image file doesn't exist
        ValueError: If the file is not a supported image format
        IOError: If there's an error reading the file
    """
    supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    file_ext = image_path.lower().split('.')[-1]
    file_ext = f".{file_ext}"
    
    if file_ext not in supported_formats:
        raise ValueError(
            f"Unsupported file format: {file_ext}. Supported formats: {', '.join(supported_formats)}. "
            f"Please provide an image file, not a video or other media type."
        )
    
    try:
        # Open the image and convert to RGB if needed (e.g., RGBA, P mode)
        image = Image.open(image_path)
        original_size = len(open(image_path, 'rb').read())
        print(f"Original image size: {original_size / 1024 / 1024:.2f} MB")
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to smaller dimensions (max 384 pixels on longest side for small payload)
        max_size = 384
        image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Compress with lower quality and optimization
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=60, optimize=True)
        image_data = buffer.getvalue()
        compressed_size = len(image_data)
        base64_size = len(base64.b64encode(image_data))
        
        print(f"Compressed image: {compressed_size / 1024:.2f} KB, Base64 size: {base64_size / 1024 / 1024:.2f} MB")
        
        return base64.b64encode(image_data).decode('utf-8')
    except ValueError:
        # Re-raise ValueError for unsupported formats
        raise
    except Exception as e:
        raise ValueError(f"Failed to process image {image_path}: {e}")


def analyze_study_material(image_path: str) -> str:
    """Analyze a study material image and extract key information.
    
    Provides:
    - Summary of the content
    - 5 Key Concepts
    - 3 Exam Questions
    
    Args:
        image_path: Path to the study material image
        
    Returns:
        Formatted markdown string with analysis results
    """
    def format_choice_lines(text: str) -> str:
        """Ensure each multiple-choice option starts on its own line."""
        text = re.sub(r'(?<=\S)\s+([A-D])[\.)]\s*', r'\n\1. ', text)
        return text

    try:
        base64_image = encode_image(image_path)

        # NOTE: Groq vision models expect multimodal `content` as a list.
        # Some endpoints/models are strict about message content being a string.
        # To be safe, we pass a plain-text prompt in `content` along with the image.
        # If Groq rejects this format, the exception will be returned to the UI.
        prompt = (
            "Analyze these study notes. Provide a Summary, 5 Key Concepts, "
            "and 3 Exam Questions. Use Markdown formatting."
        )

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
        )

        return format_choice_lines(response.choices[0].message.content)

    except FileNotFoundError:
        return "Error: Image file not found. Please check the file path."
    except ValueError as ve:
        return f"Error: {str(ve)}"
    except Exception as e:
        return f"Error analyzing study material: {str(e)}"