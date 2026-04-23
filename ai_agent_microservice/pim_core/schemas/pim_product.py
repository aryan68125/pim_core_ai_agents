from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PIMProductRecord(BaseModel):
    """Raw product record as received from the PIM system export.

    Only the fields relevant to description generation are accepted.
    All fields are optional — empty string, empty list, or null values
    are all valid. No field is mandatory.
    """

    productID: int = 0
    ipManufacturer: str = ""
    coordGroupDescription: str = ""
    productName: str = ""
    warranty: str = ""
    productDescription: str = ""
    posDescription: str = ""
    productType: str = ""
    suggestedWebcategory: str = ""
    webManufacturer: str = ""
    copy1: str = ""
    vendorStyle: str = ""
    categorySpecificAttributes: list[Any] = []

    model_config = {"extra": "ignore"}
