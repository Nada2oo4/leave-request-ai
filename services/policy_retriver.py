from policy.vector_store import (
    get_or_create_index,
    embed_text,
)


LEAVE_TYPE_METADATA = {
    "Annual Leave": "is_annual_leave",
    "Sick Leave": "is_sick_leave",
    "Marriage Leave": "is_marriage_leave",
    "Maternity / Paternity Leaves": "is_maternity_paternity",
    "Official and Public Holidays": "is_public_holiday",
    "Unpaid Leave": "is_unpaid_leave",
    "Compassionate Leave": "is_compassionate_leave",
    "Hajj Leave": "is_hajj_leave",
}


def retrieve_policy(
    country: str,
    leave_type: str,
    start_date: str = "",
    end_date: str = "",
    reason: str = "",
    top_k: int = 5,
):
    """
    Retrieve policy evidence specifically for a leave request.

    Retrieval strategy:
    1. Filter by employee country.
    2. Filter by requested leave type.
    3. Use semantic similarity to rank the matching chunks.
    """

    if not country:
        raise ValueError("Country is required.")

    if not leave_type:
        raise ValueError("Leave type is required.")

    query = f"""
    Leave Request

    Country: {country}
    Leave Type: {leave_type}
    Start Date: {start_date}
    End Date: {end_date}
    Reason: {reason}

    Retrieve only the company policy rules that apply
    to this specific leave request.

    Focus on:
    - eligibility
    - service requirements
    - allowed duration
    - leave entitlement
    - required documents
    - notice period
    - approval requirements
    - restrictions
    """

    query_vector = embed_text(query)

    index = get_or_create_index()

    # --------------------------------------------------
    # Metadata filter
    # --------------------------------------------------

    metadata_filter = {
        "country": {
            "$eq": country
        }
    }

    leave_metadata_field = LEAVE_TYPE_METADATA.get(leave_type)

    if leave_metadata_field:
        metadata_filter[leave_metadata_field] = {
            "$eq": True
        }
    print("\nDEBUG METADATA FILTER:")
    print(metadata_filter) 
    # --------------------------------------------------
    # Pinecone search
    # --------------------------------------------------

    results = index.query(
        vector=query_vector,
        top_k=top_k,
        filter=metadata_filter,
        include_metadata=True,
    )

    evidence = []

    for match in results.matches:

        metadata = match.metadata or {}

        evidence.append(
            {
                "score": float(match.score),
                "text": metadata.get("text", ""),
                "page": metadata.get("page"),
                "country": metadata.get("country", ""),
                "section": metadata.get("section", ""),
                "leave_types": metadata.get(
                    "leave_types",
                    [],
                ),
            }
        )

    return evidence

