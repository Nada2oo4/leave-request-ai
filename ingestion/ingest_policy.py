from pathlib import Path
import re

from pypdf import PdfReader  # type: ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter  # type: ignore


POLICY_PATH = Path("policy/leave_and_absence_policy.pdf")


COUNTRIES = [
    "KSA",
    "Egypt",
    "Jordan",
    "Qatar",
    "UAE",
    "Lebanon",
]


LEAVE_PATTERNS = {
    "Annual Leave": r"\bannual leave\b",
    "Sick Leave": r"\bsick leave\b",
    "Marriage Leave": r"\bmarriage leave\b",
    "Maternity / Paternity Leaves": (
        r"\bmaternity\s*/\s*paternity leaves?\b"
        r"|\bmaternity leave\b"
        r"|\bpaternity leave\b"
    ),
    "Official and Public Holidays": (
        r"\bofficial and public holidays\b"
    ),
    "Unpaid Leave": r"\bunpaid leave\b",
    "Compassionate Leave": r"\bcompassionate leave\b",
    "Hajj Leave": (
        r"\bhajj leave\b|\bpilgrimage leave\b"
    ),
}


SECTION_PATTERNS = {
    "Introduction": r"\b2\s+INTRODUCTION\b",
    "The Need": r"\b3\s+THE NEED\b",
    "Roles and Responsibilities": (
        r"\b4\s+ROLES AND RESPONSIBILITIES\b"
    ),
    "Policy Details": r"\b5\s+POLICY DETAILS\b",
    "Leave Breakdown by Country": (
        r"\b6(?:\.1)?\s+LEAVE BREAKDOWN BY COUNTRY\b"
    ),
    "Notes": r"\b7\s+NOTES\b",
    "Leave Calculation on Resignation/Termination": (
        r"\b8\s+LEAVE CALCULATION ON RESIGNATION/TERMINATION\b"
    ),
    "Approval Workflow": r"\b9\s+APPROVAL WORKFLOW\b",
    "Authorization": r"\b10\s+AUTHORIZATION\b",
    "Archiving": r"\b11\s+ARCHIVING\b",
    "Appendices": r"\b12\s+APPENDICES\b",
}



LEAVE_METADATA_FIELDS = {
    "Annual Leave": "is_annual_leave",
    "Sick Leave": "is_sick_leave",
    "Marriage Leave": "is_marriage_leave",
    "Maternity / Paternity Leaves": "is_maternity_paternity",
    "Official and Public Holidays": "is_public_holiday",
    "Unpaid Leave": "is_unpaid_leave",
    "Compassionate Leave": "is_compassionate_leave",
    "Hajj Leave": "is_hajj_leave",
}


def clean_text(text: str) -> str:
    """Clean extracted PDF text while preserving readability."""

    if not text:
        return ""

    text = text.replace("\r", "\n")

    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(
        r"\n\s*\n+",
        "\n\n",
        text,
    )

    return text.strip()


def detect_country(text: str) -> str | None:
    """Detect a country explicitly mentioned in the text."""

    for country in COUNTRIES:

        pattern = rf"\b{re.escape(country)}\b"

        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):
            return country

    return None


def detect_section(text: str) -> str | None:
    """Detect the main policy section."""

    for section_name, pattern in SECTION_PATTERNS.items():

        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):
            return section_name

    return None


def detect_leave_types(text: str) -> list[str]:
    """Detect leave types mentioned in a chunk."""

    leave_types = []

    for leave_type, pattern in LEAVE_PATTERNS.items():

        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):
            leave_types.append(leave_type)

    return leave_types


def create_leave_metadata(
    leave_types: list[str],
) -> dict:
    """
    Create boolean metadata fields for Pinecone filtering.

    Example:

        Annual Leave
        ->
        is_annual_leave = True
        is_sick_leave = False
        ...
    """

    metadata = {}

    for leave_type, field_name in LEAVE_METADATA_FIELDS.items():

        metadata[field_name] = (
            leave_type in leave_types
        )

    return metadata


def load_pdf() -> list[dict]:
    """Load the policy PDF page by page."""

    if not POLICY_PATH.exists():

        raise FileNotFoundError(
            f"Policy PDF not found: {POLICY_PATH}"
        )

    reader = PdfReader(POLICY_PATH)

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1,
    ):

        raw_text = page.extract_text() or ""

        text = clean_text(raw_text)

        if not text:
            continue

        pages.append(
            {
                "text": text,
                "page": page_number,
            }
        )

    return pages


def create_chunks(
    pages: list[dict],
) -> list[dict]:
    """
    Create policy chunks with retrieval metadata.

    Each chunk contains:

        text
        page
        chunk_index
        country
        section
        leave_types

    Plus boolean Pinecone filter fields.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    chunks = []

    current_country = None
    current_section = None

    for page in pages:

        text = page["text"]

        # --------------------------------------------------
        # Detect page-level metadata
        # --------------------------------------------------

        detected_country = detect_country(text)

        detected_section = detect_section(text)

        # Only update the current country when the page
        # explicitly introduces a country.
        if detected_country:
            current_country = detected_country

        if detected_section:
            current_section = detected_section

        # --------------------------------------------------
        # Split page
        # --------------------------------------------------

        page_chunks = splitter.split_text(text)

        for chunk_index, chunk in enumerate(
            page_chunks
        ):

            chunk = chunk.strip()

            if not chunk:
                continue

            # --------------------------------------------------
            # Leave metadata
            # --------------------------------------------------

            leave_types = detect_leave_types(
                chunk
            )

            leave_metadata = create_leave_metadata(
                leave_types
            )

            # --------------------------------------------------
            # Create chunk
            # --------------------------------------------------

            chunk_data = {
                "text": chunk,
                "page": page["page"],
                "chunk_index": chunk_index,
                "country": current_country,
                "section": current_section,
                "leave_types": leave_types,
            }

            # Add boolean metadata fields
            chunk_data.update(
                leave_metadata
            )

            chunks.append(chunk_data)

    return chunks


if __name__ == "__main__":

    from policy.vector_store import upsert_chunks

    pages = load_pdf()

    chunks = create_chunks(pages)

    print(
        f"Pages: {len(pages)}"
    )

    print(
        f"Chunks: {len(chunks)}"
    )

    # Show metadata before uploading
    print("\nSample chunk metadata:")

    for chunk in chunks[:5]:

        print(
            {
                "page": chunk["page"],
                "country": chunk["country"],
                "section": chunk["section"],
                "leave_types": chunk["leave_types"],
            }
        )

    # Upload to Pinecone
    upsert_chunks(chunks)

    print(
        "\nPolicy ingestion completed successfully."
    )