"""Service for converting PPTX presentations to PDF using Microsoft PowerPoint COM automation."""

import logging
from pathlib import Path
import pythoncom
import win32com.client

logger = logging.getLogger(__name__)

def convert_pptx_to_pdf(pptx_path: Path, pdf_path: Path) -> bool:
    """Convert a PPTX file to PDF using Microsoft PowerPoint.
    
    Returns True if conversion succeeded, False otherwise.
    """
    abs_pptx = str(pptx_path.resolve())
    abs_pdf = str(pdf_path.resolve())
    
    logger.info(f"Starting PowerPoint PDF conversion: {abs_pptx} -> {abs_pdf}")
    
    # Initialize COM for the current thread
    pythoncom.CoInitialize()
    
    powerpoint = None
    presentation = None
    success = False
    
    try:
        # DispatchEx creates a new instance of PowerPoint
        powerpoint = win32com.client.DispatchEx("PowerPoint.Application")
        
        # Open presentation in read-only mode, without window/gui
        presentation = powerpoint.Presentations.Open(
            abs_pptx,
            ReadOnly=True,
            Untitled=False,
            WithWindow=False
        )
        
        # Save as PDF (Format type 32)
        presentation.SaveAs(abs_pdf, 32)
        success = True
        logger.info(f"PowerPoint PDF conversion successful: {abs_pdf}")
    except Exception as e:
        logger.error(f"Failed to convert PPTX to PDF via PowerPoint COM: {e}", exc_info=True)
    finally:
        if presentation:
            try:
                presentation.Close()
            except Exception as e:
                logger.warning(f"Error closing presentation: {e}")
        if powerpoint:
            try:
                powerpoint.Quit()
            except Exception as e:
                logger.warning(f"Error quitting PowerPoint Application: {e}")
        # Uninitialize COM for this thread
        pythoncom.CoUninitialize()
        
    return success


async def preconvert_presentation_by_id(presentation_id: str, file_path_str: str) -> bool:
    """Run PDF conversion in a separate thread so it doesn't block the async event loop."""
    import asyncio
    from app.config import get_settings
    settings = get_settings()
    file_path = Path(file_path_str)
    cache_pdf_path = settings.cache_path / f"{presentation_id}.pdf"
    if cache_pdf_path.exists():
        return True
    
    return await asyncio.to_thread(convert_pptx_to_pdf, file_path, cache_pdf_path)


async def preconvert_all_presentations(db: AsyncSession):
    """Batch pre-convert all PPTX presentations to PDF sequentially in a background task."""
    from sqlalchemy import select
    from app.models.presentation import Presentation
    from sqlalchemy.ext.asyncio import AsyncSession
    
    result = await db.execute(select(Presentation).where(Presentation.file_type == "pptx"))
    presentations = result.scalars().all()
    
    logger.info(f"Checking pre-conversion to PDF for {len(presentations)} PPTX presentations...")
    
    count = 0
    for pres in presentations:
        try:
            success = await preconvert_presentation_by_id(str(pres.id), pres.file_path)
            if success:
                count += 1
        except Exception as e:
            logger.error(f"Failed to pre-convert {pres.file_name} during batch run: {e}")
            
    logger.info(f"Completed pre-conversion checking. Successfully cached/verified {count}/{len(presentations)} PDFs.")

