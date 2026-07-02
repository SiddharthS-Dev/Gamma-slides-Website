"""Thumbnail generator — creates preview images from presentations."""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def generate_thumbnail(file_path: Path, output_dir: Path) -> Optional[Path]:
    """Generate a thumbnail image from a presentation file.

    Returns the path to the generated thumbnail, or None if generation failed.
    """
    ext = file_path.suffix.lower()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Use file stem as thumbnail name
    thumb_name = f"{file_path.stem}.webp"
    thumb_path = output_dir / thumb_name

    # Skip if thumbnail already exists
    if thumb_path.exists():
        return thumb_path

    try:
        if ext == ".pptx":
            return _thumbnail_from_pptx(file_path, thumb_path)
        elif ext == ".pdf":
            return _thumbnail_from_pdf(file_path, thumb_path)
        elif ext in (".html", ".htm"):
            return _create_placeholder_thumbnail(file_path, thumb_path, "HTML")
        else:
            return None
    except Exception as e:
        logger.warning(f"Failed to generate thumbnail for {file_path.name}: {e}")
        return _create_placeholder_thumbnail(file_path, thumb_path, ext.upper().lstrip('.'))


def _thumbnail_from_pptx(file_path: Path, output_path: Path) -> Optional[Path]:
    """Generate thumbnail from first slide of PPTX.

    Uses python-pptx to extract embedded thumbnail or creates a text-based placeholder.
    """
    try:
        from pptx import Presentation
        import zipfile

        # PPTX files are ZIP archives — try to extract the embedded thumbnail
        with zipfile.ZipFile(str(file_path), 'r') as z:
            # Try common thumbnail paths in PPTX
            thumbnail_paths = [
                'docProps/thumbnail.jpeg',
                'docProps/thumbnail.png',
                'docProps/thumbnail.wmf',
            ]
            for thumb_zip_path in thumbnail_paths:
                if thumb_zip_path in z.namelist():
                    thumb_data = z.read(thumb_zip_path)
                    # Convert to WebP using PIL if available
                    try:
                        from PIL import Image
                        import io
                        img = Image.open(io.BytesIO(thumb_data))
                        img = img.convert('RGB')
                        img = img.resize((640, 360), Image.Resampling.LANCZOS)
                        img.save(str(output_path), 'WebP', quality=85)
                        return output_path
                    except ImportError:
                        # PIL not available — save as-is with jpeg extension
                        jpeg_path = output_path.with_suffix('.jpg')
                        jpeg_path.write_bytes(thumb_data)
                        return jpeg_path

        # If no embedded thumbnail found, create a placeholder
        return _create_placeholder_thumbnail(file_path, output_path, "PPTX")

    except Exception as e:
        logger.warning(f"PPTX thumbnail extraction failed for {file_path.name}: {e}")
        return _create_placeholder_thumbnail(file_path, output_path, "PPTX")


def _thumbnail_from_pdf(file_path: Path, output_path: Path) -> Optional[Path]:
    """Generate thumbnail from first page of PDF."""
    try:
        # Try using pdf2image (requires poppler)
        from pdf2image import convert_from_path
        images = convert_from_path(str(file_path), first_page=1, last_page=1, size=(640, 360))
        if images:
            images[0].save(str(output_path), 'WebP', quality=85)
            return output_path
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"pdf2image failed for {file_path.name}: {e}")

    try:
        # Try using PyMuPDF (fitz)
        import fitz
        doc = fitz.open(str(file_path))
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        pix.save(str(output_path.with_suffix('.png')))
        doc.close()
        # Convert to WebP if PIL available
        try:
            from PIL import Image
            img = Image.open(str(output_path.with_suffix('.png')))
            img = img.resize((640, 360), Image.Resampling.LANCZOS)
            img.save(str(output_path), 'WebP', quality=85)
            output_path.with_suffix('.png').unlink(missing_ok=True)
            return output_path
        except ImportError:
            return output_path.with_suffix('.png')
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"PyMuPDF failed for {file_path.name}: {e}")

    return _create_placeholder_thumbnail(file_path, output_path, "PDF")


def _create_placeholder_thumbnail(file_path: Path, output_path: Path, file_type: str) -> Optional[Path]:
    """Create a colored gradient placeholder thumbnail with text."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io

        # Create gradient background
        width, height = 640, 360
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)

        # Color schemes by type
        colors = {
            "PPTX": [(99, 102, 241), (168, 85, 247)],   # Indigo → Purple
            "PDF": [(239, 68, 68), (234, 88, 12)],        # Red → Orange
            "HTML": [(14, 165, 233), (34, 197, 94)],      # Sky → Green
        }
        c1, c2 = colors.get(file_type, [(99, 102, 241), (168, 85, 247)])

        # Draw gradient
        for y in range(height):
            r = int(c1[0] + (c2[0] - c1[0]) * y / height)
            g = int(c1[1] + (c2[1] - c1[1]) * y / height)
            b = int(c1[2] + (c2[2] - c1[2]) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Draw file type badge
        badge_text = f".{file_type.lower()}"
        try:
            font_large = ImageFont.truetype("arial.ttf", 28)
            font_small = ImageFont.truetype("arial.ttf", 16)
        except OSError:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Draw title text
        title = file_path.stem[:40]
        title = title.replace('-', ' ').replace('_', ' ')
        draw.text((30, height // 2 - 30), title, fill=(255, 255, 255, 220), font=font_large)

        # Draw file type
        draw.text((30, height // 2 + 10), badge_text, fill=(255, 255, 255, 180), font=font_small)

        img.save(str(output_path), 'WebP', quality=85)
        return output_path

    except ImportError:
        logger.info("PIL not available — skipping placeholder thumbnail generation")
        return None
    except Exception as e:
        logger.warning(f"Placeholder thumbnail failed: {e}")
        return None
