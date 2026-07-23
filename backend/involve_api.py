"""
Backward-compatibility adapter for Involve Asia API functions.
Delegates to backend.integrations.involve_asia.involve_client.
"""
import requests
from backend.integrations.involve_asia import involve_client


_token_cache = involve_client._token_cache
_offers_cache = involve_client._offers_cache

def authenticate_session() -> None:
    return involve_client.authenticate()


def get_all_offers() -> list:
    return involve_client.get_all_offers()

def generate_deeplink(
    product_url: str,
    offer_id: int,
    aff_sub: str = None,
    aff_sub2: str = None,
    aff_sub3: str = None,
    aff_sub4: str = None,
    aff_sub5: str = None
) -> str:
    return involve_client.generate_deeplink(
        product_url=product_url,
        offer_id=offer_id,
        aff_sub=aff_sub,
        aff_sub2=aff_sub2,
        aff_sub3=aff_sub3,
        aff_sub4=aff_sub4,
        aff_sub5=aff_sub5
    )
