import logging
from typing import Iterable, Sequence

from src.models.product import Product, ProductColor, ProductStatus
from src.schemas.product import ProductMeta, ProductPublic, ProductSectionOut

logger = logging.getLogger(__name__)


def validate_sections(raw_sections: Sequence[object]) -> list[ProductSectionOut]:
    validated_sections: list[ProductSectionOut] = []
    for section in raw_sections:
        try:
            if hasattr(ProductSectionOut, "model_validate"):
                validated_sections.append(ProductSectionOut.model_validate(section))
            else:
                validated_sections.append(ProductSectionOut.from_orm(section))
        except Exception as exc:
            logger.warning("Error validating product section: %s", exc)
    return validated_sections


def build_product_public(
    product: Product,
    color: ProductColor,
    *,
    sizes: Sequence[object],
    images: Sequence[object],
    main_category: object = None,
    sections: Sequence[object] = (),
) -> ProductPublic:
    effective_price = color.price if color.price is not None else product.price
    effective_discount = color.discount_price if color.discount_price is not None else product.discount_price

    return ProductPublic(
        id=color.id,
        product_id=product.id,
        color_id=color.id,
        slug=color.slug,
        title=color.title,
        categoryPath=[],
        main_category=main_category,
        price=effective_price,
        discount_price=effective_discount,
        currency=product.currency or "RUB",
        weight=product.weight,
        label=color.label or "Default",
        hex=color.hex or "#000000",
        sizes=list(sizes),
        composition=product.composition,
        fit=product.fit,
        description=product.description,
        images=[
            {
                "file": image.file,
                "alt": None,
                "w": None,
                "h": None,
                "color": None,
                "sort_order": getattr(image, "sort_order", 0),
            }
            for image in images
        ],
        meta=ProductMeta(
            care=getattr(product, "meta_care", None),
            shipping=getattr(product, "meta_shipping", None),
            returns=getattr(product, "meta_returns", None),
        ),
        status=product.status or ProductStatus.IN_STOCK,
        custom_sections=validate_sections(sections),
    )
