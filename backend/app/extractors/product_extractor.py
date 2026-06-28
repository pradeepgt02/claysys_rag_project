def is_product_type(type_val) -> bool:
    """
    Checks if the type value represents a Product, allowing for case insensitivity
    and handling of list-based type definitions.
    """
    if not type_val:
        return False
    if isinstance(type_val, str):
        return type_val.lower().endswith("product") or "product" in type_val.lower()
    elif isinstance(type_val, list):
        return any(isinstance(t, str) and ("product" in t.lower()) for t in type_val)
    return False

def extract_product_data(jsonld_data: list[dict]) -> list[dict]:
    """
    Iterates through extracted JSON-LD schemas.
    Identifies schemas where @type is Product (case-insensitive).
    Extracts fields:
    - name
    - description
    - brand
    - sku
    - price
    - currency
    - availability
    - rating (aggregateRating value)
    - review_count (aggregateRating reviewCount)
    
    Returns a list of parsed product dictionaries.
    """
    if not jsonld_data:
        return []

    products = []

    for item in jsonld_data:
        if not isinstance(item, dict):
            continue

        if not is_product_type(item.get("@type")):
            # Also search for nested product structures, e.g. in @graph
            graph = item.get("@graph")
            if isinstance(graph, list):
                # Recursively process the graph elements
                products.extend(extract_product_data(graph))
            continue

        # Extract brand
        brand_val = item.get("brand", "")
        brand_name = ""
        if isinstance(brand_val, str):
            brand_name = brand_val
        elif isinstance(brand_val, dict):
            brand_name = brand_val.get("name", "") or brand_val.get("value", "") or ""
        
        # Extract offers details (price, currency, availability)
        offers_val = item.get("offers", "")
        price = ""
        currency = ""
        availability = ""

        # Normalize offers to a list
        offers_list = []
        if isinstance(offers_val, dict):
            offers_list = [offers_val]
        elif isinstance(offers_val, list):
            offers_list = offers_val

        if offers_list:
            # Check first offer for details
            first_offer = offers_list[0]
            if isinstance(first_offer, dict):
                price = first_offer.get("price", "")
                currency = first_offer.get("priceCurrency", "")
                
                avail = first_offer.get("availability", "")
                if isinstance(avail, str):
                    if "/" in avail:
                        availability = avail.split("/")[-1]
                    else:
                        availability = avail
                else:
                    availability = str(avail) if avail is not None else ""

        # Extract ratings
        rating_val = item.get("aggregateRating", "")
        rating = ""
        review_count = ""
        if isinstance(rating_val, dict):
            rating = rating_val.get("ratingValue", "")
            review_count = rating_val.get("reviewCount", "") or rating_val.get("ratingCount", "")

        # Build clean product data
        product_data = {
            "name": " ".join(str(item.get("name", "") or "").split()).strip(),
            "description": " ".join(str(item.get("description", "") or "").split()).strip(),
            "brand": " ".join(str(brand_name).split()).strip(),
            "sku": " ".join(str(item.get("sku", "") or "").split()).strip(),
            "price": " ".join(str(price or "").split()).strip(),
            "currency": " ".join(str(currency or "").split()).strip(),
            "availability": " ".join(str(availability or "").split()).strip(),
            "rating": " ".join(str(rating or "").split()).strip(),
            "review_count": " ".join(str(review_count or "").split()).strip()
        }

        products.append(product_data)

    return products
