import os
import uuid

from fastapi import HTTPException, UploadFile, status

from app.config import settings
from app.utils.logger import logger

CLAIM_UPLOAD_DIR = "generated_files/claim_uploads"

os.makedirs(CLAIM_UPLOAD_DIR, exist_ok=True)


# only allowed file types should be accepted - level 8's own business
# rule, checked against the real file extension, not just the
# client-declared document_type
async def save_claim_document(file: UploadFile, claim_id: int) -> tuple[str, str]:

    try:

        extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

        if extension not in settings.ALLOWED_UPLOAD_EXTENSIONS:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '.{extension}' is not allowed. Allowed types: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}"
            )

        contents = await file.read()

        max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        if len(contents) > max_size_bytes:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds the maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        # unique, safe filename on disk - the original name is preserved
        # separately for display purposes only
        safe_filename = f"claim_{claim_id}_{uuid.uuid4().hex}.{extension}"

        file_path = os.path.join(CLAIM_UPLOAD_DIR, safe_filename)

        with open(file_path, "wb") as output_file:

            output_file.write(contents)

        logger.info(f"Claim document saved : {file_path}")

        return file.filename, file_path

    except HTTPException:

        raise

    except Exception as error:

        logger.error(f"Claim document upload failed : {str(error)}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to upload document.")