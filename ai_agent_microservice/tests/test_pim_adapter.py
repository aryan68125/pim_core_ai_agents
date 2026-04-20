from __future__ import annotations

from pim_core.adapters.pim_adapter import pim_record_to_product
from pim_core.schemas.pim_product import PIMProductRecord


def _make_record(**kwargs) -> PIMProductRecord:
    """Return a minimal valid PIM record, overriding fields via kwargs."""
    defaults = {
        "productID": 705517,
        "productName": "MACSTUDIO E25 M4M/64/1TB",
        "coordGroupDescription": "APPLE DESKTOP SYSTEMS    ",
        "ipManufacturer": "APPLE",
        "productDescription": "MACSTUDIO E25 M4M/64/1TB",
        "warranty": "1 year",
        "vendorStyle": "15098309",
    }
    defaults.update(kwargs)
    return PIMProductRecord(**defaults)


def test_adapter_maps_product_id_as_string():
    product = pim_record_to_product(_make_record(productID=705517))
    assert product.id == "705517"


def test_adapter_maps_product_name():
    product = pim_record_to_product(_make_record(productName="MACSTUDIO E25 M4M/64/1TB"))
    assert product.name == "MACSTUDIO E25 M4M/64/1TB"


def test_adapter_strips_trailing_spaces_from_category():
    product = pim_record_to_product(_make_record(coordGroupDescription="APPLE DESKTOP SYSTEMS    "))
    assert product.category == "APPLE DESKTOP SYSTEMS"


def test_adapter_maps_manufacturer_as_brand():
    product = pim_record_to_product(_make_record(ipManufacturer="APPLE"))
    assert product.attributes.brand == "APPLE"


def test_adapter_brand_is_none_when_manufacturer_empty():
    product = pim_record_to_product(_make_record(ipManufacturer=""))
    assert product.attributes.brand is None


def test_adapter_includes_warranty_in_additional():
    product = pim_record_to_product(_make_record(warranty="1 year"))
    assert product.attributes.additional["warranty"] == "1 year"


def test_adapter_includes_vendor_part_number_in_additional():
    product = pim_record_to_product(_make_record(vendorStyle="15098309"))
    assert product.attributes.additional["vendor_part_number"] == "15098309"


def test_adapter_includes_web_manufacturer_in_additional():
    product = pim_record_to_product(_make_record(webManufacturer="Apple Inc"))
    assert product.attributes.additional["web_manufacturer"] == "Apple Inc"


def test_adapter_includes_web_category_in_additional():
    product = pim_record_to_product(_make_record(suggestedWebcategory="Computers<br />Desktop Computers"))
    assert product.attributes.additional["web_category"] == "Computers<br />Desktop Computers"


def test_adapter_includes_product_type_in_additional():
    product = pim_record_to_product(_make_record(productType="Hardware"))
    assert product.attributes.additional["product_type"] == "Hardware"


def test_adapter_excludes_empty_optional_fields():
    product = pim_record_to_product(_make_record(
        webManufacturer="", suggestedWebcategory="", productType=""
    ))
    assert "web_manufacturer" not in product.attributes.additional
    assert "web_category" not in product.attributes.additional
    assert "product_type" not in product.attributes.additional


def test_adapter_includes_category_attributes_when_non_empty():
    import json
    attrs = [{"name": "Color", "value": "Black"}, {"name": "Weight", "value": "1.2kg"}]
    product = pim_record_to_product(_make_record(categorySpecificAttributes=attrs))
    assert product.attributes.additional["category_attributes"] == json.dumps(attrs)


def test_adapter_excludes_category_attributes_when_empty():
    product = pim_record_to_product(_make_record(categorySpecificAttributes=[]))
    assert "category_attributes" not in product.attributes.additional


def test_adapter_copy1_used_as_existing_description():
    """copy1 is preferred over productDescription as existing_description."""
    product = pim_record_to_product(_make_record(
        productName="Sony Alpha 7V",
        copy1="Full-frame mirrorless camera with 33MP sensor and AI subject recognition.",
        productDescription="Sony Alpha 7V",
    ))
    assert product.existing_description == "Full-frame mirrorless camera with 33MP sensor and AI subject recognition."


def test_adapter_falls_back_to_product_description():
    """Falls back to productDescription when copy1 is empty or same as product name."""
    product = pim_record_to_product(_make_record(
        productName="MACSTUDIO E25 M4M/64/1TB",
        copy1="",
        productDescription="Apple Mac Studio with M4 Max chip, 64GB RAM, 1TB SSD.",
    ))
    assert product.existing_description == "Apple Mac Studio with M4 Max chip, 64GB RAM, 1TB SSD."


def test_adapter_falls_back_to_pos_description():
    """Falls back to posDescription when copy1 and productDescription add no value."""
    product = pim_record_to_product(_make_record(
        productName="MACSTUDIO E25 M4M/64/1TB",
        copy1="",
        productDescription="MACSTUDIO E25 M4M/64/1TB",
        posDescription="Mac Studio M4 Max desktop workstation.",
    ))
    assert product.existing_description == "Mac Studio M4 Max desktop workstation."


def test_adapter_skips_existing_description_when_same_as_product_name():
    """All description fields repeat the product name — existing_description is None."""
    product = pim_record_to_product(_make_record(
        productName="MACSTUDIO E25 M4M/64/1TB",
        copy1="",
        productDescription="MACSTUDIO E25 M4M/64/1TB",
        posDescription="MACSTUDIO E25 M4M/64/1TB",
    ))
    assert product.existing_description is None


def test_adapter_image_urls_always_empty():
    """image_urls is always empty — image fields are not in the new schema."""
    product = pim_record_to_product(_make_record())
    assert product.image_urls == []


def test_adapter_sku_always_empty():
    """sku is always empty — shortSku is not in the new schema."""
    product = pim_record_to_product(_make_record())
    assert product.sku == ""


def test_adapter_ignores_extra_fields():
    """Extra fields present in the raw JSON are silently ignored (extra='ignore')."""
    record = PIMProductRecord(**{
        "productID": 1,
        "productName": "Test",
        "shortSku": "999",       # removed field
        "image1": "http://img",  # removed field
        "asteaWarranty": "1yr",  # removed field
    })
    product = pim_record_to_product(record)
    assert product.id == "1"
