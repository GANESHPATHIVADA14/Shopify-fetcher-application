from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict

class InsightRequest(BaseModel):
    website_url: HttpUrl

class Product(BaseModel):
    id: int
    title: str
    vendor: str
    product_type: str
    url: HttpUrl
    main_image: Optional[HttpUrl]
    price: str

class Policy(BaseModel):
    title: str
    url: Optional[HttpUrl]
    content: str

class FAQ(BaseModel):
    question: str
    answer: str

class ContactDetails(BaseModel):
    emails: List[str] = []
    phone_numbers: List[str] = []

class BrandContext(BaseModel):
    store_name: str
    base_url: HttpUrl
    all_products: List[Product] = []
    hero_products: List[Product] = []
    privacy_policy: Optional[Policy]
    refund_policy: Optional[Policy]
    faqs: List[FAQ] = []
    social_handles: Dict[str, HttpUrl] = {}
    contact_details: ContactDetails
    about_us_context: Optional[str]
    important_links: Dict[str, HttpUrl] = {}