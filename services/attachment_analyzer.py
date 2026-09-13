from pathlib import Path
import base64
from dotenv import load_dotenv
from typing import Any, cast
import httpx
from openai import OpenAI
from pypdf import PdfReader
from docx import Document
load_dotenv()
client = OpenAI(
    http_client=cast(Any, httpx.Client())
)
# ==================================================
# 1. Check Attachment Requirement
# ==================================================
def check_attachment_requirement(
    leave_request: dict,
) -> dict:
    country = leave_request.get("country")
    leave_type = leave_request.get("leave_type")
    requested_days = leave_request.get(
        "requested_days",
        0,
    )
    attachment_required = False
    attachment_type = None
    reason = ""
    # ==================================================
    # Sick Leave
    # ==================================================
    if leave_type == "Sick Leave":
        attachment_type = "Medical Certificate"
        # Jordan:
        # 2 or more days require a medical certificate.
        # One-day sick leave may be taken without one
        # in isolated cases, subject to manager approval.
        if country == "Jordan":
            if requested_days >= 2:
                attachment_required = True
                reason = (
                    "A medical certificate is required "
                    "for sick leave of two or more "
                    "calendar days in Jordan."
                )
            else:
                attachment_required = False
                reason = (
                    "A one-day sick leave may be taken "
                    "without a medical certificate in "
                    "isolated cases, subject to line "
                    "manager approval."
                )
        else:
            # KSA, Egypt, Qatar, UAE, Lebanon
            attachment_required = True
            reason = (
                "A medical certificate or medical report "
                "is required for sick leave."
            )
    # ==================================================
    # Maternity / Paternity Leave
    # ==================================================
    elif leave_type == "Maternity / Paternity Leaves":
        if country == "Egypt":
            attachment_required = True
            attachment_type = (
                "Medical Certificate / "
                "Authenticated Birth Certificate"
            )
            reason = (
                "A medical certificate should be presented "
                "when applying for maternity leave, and an "
                "authenticated birth certificate is required "
                "for maternity or paternity leave."
            )
        elif country == "Jordan":
            attachment_required = True
            attachment_type = "Birth Certificate"
            reason = (
                "A copy of the child's birth certificate "
                "is required as a supporting document "
                "for paternity leave."
            )
        elif country == "Qatar":
            attachment_required = True
            attachment_type = "Medical Report"
            reason = (
                "A medical report issued by a licensed "
                "physician is required for maternity leave."
            )
        elif country == "UAE":
            attachment_required = True
            attachment_type = "Birth Certificate"
            reason = (
                "A birth certificate is required for "
                "maternity and paternity leave."
            )
        else:
            # KSA / Lebanon
            attachment_required = False
            reason = (
                "No supporting document requirement was "
                "explicitly specified for this leave type "
                "in the policy for this country."
            )
    # ==================================================
    # Compassionate Leave
    # ==================================================
    elif leave_type == "Compassionate Leave":
        if country in {
            "KSA",
            "Jordan",
            "Qatar",
            "UAE",
            "Lebanon",
        }:
            attachment_required = True
            attachment_type = "Proof of Death"
            reason = (
                "Proof of death is required for "
                "compassionate leave."
            )
        else:
            # Egypt
            attachment_required = False
            reason = (
                "Compassionate leave is not applicable "
                "in Egypt."
            )
    # ==================================================
    # Unpaid Leave
    # ==================================================
    elif leave_type == "Unpaid Leave":
        if country == "Jordan":
            attachment_required = True
            attachment_type = "Supporting Proof"
            reason = (
                "Proof is required for special conditions "
                "such as study leave, preparing for Hajj, "
                "or medical treatment."
            )
        else:
            attachment_required = False
            reason = (
                "The policy does not explicitly require "
                "an attachment for unpaid leave in this "
                "country."
            )
    # ==================================================
    # Other Leave Types
    # ==================================================
    else:
        attachment_required = False
        reason = (
            "No supporting attachment is explicitly "
            "required for this leave type according "
            "to the policy."
        )
    # ==================================================
    # Check Attachment Presence
    # ==================================================
    attachment_path = leave_request.get(
        "attachment_path"
    )
    attachment_present = ( 
        bool(attachment_path) and Path(attachment_path).exists()
    )
    return {
        "attachment_required": attachment_required,
        "attachment_present": attachment_present,
        "attachment_type": attachment_type,
        "attachment_reason": reason,
    }
# ==================================================
# 2. Extract Text From Documents
# ==================================================
def extract_document_text(
    file_path: Path,
) -> str:
    suffix = file_path.suffix.lower()

    # --------------------------------------------------
    # PDF
    # --------------------------------------------------
    if suffix == ".pdf":
        try:
            reader = PdfReader(
                str(file_path),
                strict=False,
            )

            pages = []

            for page in reader.pages:
                text = page.extract_text()

                if text:
                    pages.append(text)

            return "\n".join(pages)

        except Exception as e:
            print(f"PDF extraction error: {e}")
            return ""

    # --------------------------------------------------
    # DOCX
    # --------------------------------------------------
    if suffix == ".docx":
        try:
            document = Document(str(file_path))

            paragraphs = [
                paragraph.text
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]

            return "\n".join(paragraphs)

        except Exception as e:
            print(f"DOCX extraction error: {e}")
            return ""

    # --------------------------------------------------
    # TXT
    # --------------------------------------------------
    if suffix == ".txt":
        try:
            return file_path.read_text(
                encoding="utf-8"
            )

        except Exception as e:
            print(f"TXT extraction error: {e}")
            return ""

    return ""
# ==================================================
# 3. Analyze Attachment Using GPT-4o
# ==================================================
def analyze_attachment(
    leave_request: dict,
) -> dict:
    attachment_path = leave_request.get(
        "attachment_path"
    )
    leave_type = leave_request.get(
        "leave_type",
        "",
    )
    attachment_type = leave_request.get(
        "attachment_type",
        "supporting document",
    )
    # ==================================================
    # No Attachment
    # ==================================================
    if not attachment_path:
        return {
            "attachment_valid": False,
            "analysis": (
                "No attachment was provided."
            ),
        }
    file_path = Path(attachment_path)
    # ==================================================
    # File Does Not Exist
    # ==================================================
    if not file_path.exists():
        return {
            "attachment_valid": False,
            "analysis": (
                "The provided attachment "
                "could not be found."
            ),
        }
    suffix = file_path.suffix.lower()
    # ==================================================
    # TEXT-BASED DOCUMENTS
    # ==================================================
    if suffix in {
        ".pdf",
        ".docx",
        ".txt",
    }:
        document_text = extract_document_text(
            file_path
        )
        if not document_text.strip():
            return {
                "attachment_valid": False,
                "analysis": (
                    "The attachment could not be "
                    "read or contains no extractable text."
                ),
            }
        prompt = f"""
You are an attachment verification agent
for an employee leave management system.
Leave type:
{leave_type}
Expected supporting document:
{attachment_type}
Analyze the document and determine whether it
is an appropriate supporting document for this
leave request.
Your task is ONLY to verify the attachment.
Do NOT decide whether the leave request itself
should be approved or denied.
Determine whether the document:
1. Is relevant to the requested leave type.
2. Appears to be the expected type of supporting document.
3. Contains sufficient information to be considered
   a valid supporting document.
Return EXACTLY this format:
VALID: YES or NO
REASON: <short explanation>
Document:
{document_text}
"""
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an attachment verification "
                        "agent for an employee leave management "
                        "system."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0,
        )
        result = response.choices[0].message.content
        if not result:
            return {
                "attachment_valid": False,
                "analysis": (
                    "The LLM did not return an analysis."
                ),
            }
        attachment_valid = (
            "VALID: YES" in result.upper()
        )
        return {
            "attachment_valid": attachment_valid,
            "analysis": result,
        }
    # ==================================================
    # IMAGE DOCUMENTS
    # ==================================================
    if suffix in {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }:
        image_bytes = file_path.read_bytes()
        encoded_image = base64.b64encode(
            image_bytes
        ).decode("utf-8")
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }[suffix]
        prompt = f"""
Analyze this attachment for an employee leave request.
Leave type:
{leave_type}
Expected supporting document:
{attachment_type}
Determine whether the document is an appropriate
and relevant supporting document for this leave type.
Do NOT decide whether the leave itself should be
approved or denied.
Only verify the attachment.
Return EXACTLY:
VALID: YES or NO
REASON: <short explanation>
"""
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an attachment verification "
                        "agent for an employee leave management "
                        "system."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    f"data:{mime_type};"
                                    f"base64,{encoded_image}"
                                )
                            },
                        },
                    ],
                },
            ],
            temperature=0,
        )
        result = response.choices[0].message.content
        if not result:
            return {
                "attachment_valid": False,
                "analysis": (
                    "The LLM did not return an analysis."
                ),
            }
        attachment_valid = (
            "VALID: YES" in result.upper()
        )
        return {
            "attachment_valid": attachment_valid,
            "analysis": result,
        }
    # ==================================================
    # Unsupported File Type
    # ==================================================
    return {
        "attachment_valid": False,
        "analysis": (
            f"Unsupported attachment type: {suffix}"
        ),
    }