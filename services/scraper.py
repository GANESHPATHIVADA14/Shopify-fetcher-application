import httpx
import asyncio
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
# This is the corrected line
from typing import List, Optional, Dict
from app.schemas.brand import BrandContext, Product, Policy, FAQ, ContactDetails

# Regex for finding contacts
EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
PHONE_REGEX = r'(\+\d{1,3}[- ]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'

class ShopifyScraper:
    def __init__(self, base_url: str):
        self.base_url = base_url
        # Use a common user-agent to avoid being blocked
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        self.client = httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=20.0)

    async def close(self):
        await self.client.aclose()

    async def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = await self.client.get(url)
            response.raise_for_status() # Raise an exception for bad status codes
            return BeautifulSoup(response.text, 'html.parser')
        except httpx.RequestError:
            return None

    # 1. Whole Product Catalog
    async def get_product_catalog(self) -> List[Product]:
        products_url = urljoin(self.base_url, '/products.json')
        products_list = []
        try:
            response = await self.client.get(f"{products_url}?limit=250") # Max limit
            response.raise_for_status()
            products_data = response.json().get('products', [])
            for item in products_data:
                products_list.append(Product(
                    id=item['id'],
                    title=item['title'],
                    vendor=item['vendor'],
                    product_type=item['product_type'],
                    price=f"{item['variants'][0]['price']} {item['variants'][0].get('currency_code', 'USD')}",
                    url=urljoin(self.base_url, f"/products/{item['handle']}"),
                    main_image=item['images'][0]['src'] if item['images'] else None
                ))
        except (httpx.RequestError, KeyError, IndexError):
            # Fallback or log error
            pass
        return products_list

    # 2. Hero Products (Homepage)
    async def get_hero_products(self, soup: BeautifulSoup) -> List[Product]:
        # This is heuristic. Look for links pointing to /products/
        hero_products = []
        product_links = set() # Use a set to avoid duplicates
        for a_tag in soup.find_all('a', href=True):
            if '/products/' in a_tag['href']:
                full_url = urljoin(self.base_url, a_tag['href'])
                # Avoid collection links, focus on specific product URLs
                if full_url not in product_links and 'collections' not in a_tag['href']:
                     # We can fetch more details from the link or just the title/URL
                    product_title = a_tag.get_text(strip=True) or "Unknown Product"
                    # Create a dummy product object as we don't have full data here
                    hero_products.append(Product(
                        id=0, title=product_title, vendor="N/A", product_type="N/A",
                        url=full_url, main_image=None, price="N/A"
                    ))
                    product_links.add(full_url)
        return hero_products[:10] # Limit the number of hero products

    # 3, 4, 8. Generic Page Scraper for Policies & "About Us"
    async def find_and_scrape_page(self, soup: BeautifulSoup, keywords: List[str]) -> Optional[Policy]:
        for a_tag in soup.find_all('a', href=True):
            link_text = a_tag.get_text(strip=True).lower()
            if any(keyword in link_text for keyword in keywords):
                page_url = urljoin(self.base_url, a_tag['href'])
                page_soup = await self._get_soup(page_url)
                if page_soup:
                    # Find a main content area to extract clean text
                    main_content = page_soup.find('main') or page_soup.find('body')
                    return Policy(
                        title=a_tag.get_text(strip=True),
                        url=page_url,
                        content=main_content.get_text(separator='\n', strip=True)
                    )
        return None

    # 5. FAQs
    async def get_faqs(self, soup: BeautifulSoup) -> List[FAQ]:
        # Strategy: Find a link to an FAQ page, then parse it.
        # This is highly variable and a great place for an LLM if direct parsing fails.
        faq_link_tag = soup.find('a', href=True, string=re.compile(r'faq', re.I))
        if not faq_link_tag:
            return []
            
        faq_url = urljoin(self.base_url, faq_link_tag['href'])
        faq_soup = await self._get_soup(faq_url)
        faqs = []
        if faq_soup:
            # Common pattern 1: <details> and <summary> tags
            for item in faq_soup.find_all('details'):
                question = item.find('summary')
                answer = item.find('div') or item # Rest of the content
                if question and answer:
                    faqs.append(FAQ(question=question.get_text(strip=True), answer=answer.get_text(strip=True)))
            # Add more patterns here...
            
            # LLM Fallback (as suggested in hints):
            # if not faqs and OPENAI_API_KEY:
            #   text_content = faq_soup.get_text()
            #   faqs = self.extract_faqs_with_llm(text_content)
        return faqs

    # 6, 7, 9. Get Socials, Contacts, and Important Links
    async def get_site_wide_info(self, soup: BeautifulSoup) -> (dict, ContactDetails, dict):
        socials = {}
        contacts = ContactDetails()
        links = {}
        
        all_links = soup.find_all('a', href=True)
        
        # Socials
        social_patterns = {'instagram': 'instagram.com', 'facebook': 'facebook.com', 'tiktok': 'tiktok.com', 'twitter': 'twitter.com', 'youtube': 'youtube.com'}
        for name, pattern in social_patterns.items():
            if name not in socials: # Find first match
                for a in all_links:
                    if pattern in a['href']:
                        socials[name] = a['href']
                        break
        
        # Contacts
        body_text = soup.get_text()
        contacts.emails = list(set(re.findall(EMAIL_REGEX, body_text)))
        contacts.phone_numbers = list(set(re.findall(PHONE_REGEX, body_text)))

        # Important Links
        link_keywords = {'order_tracking': 'track', 'contact_us': 'contact', 'blog': 'blog'}
        for name, keyword in link_keywords.items():
            for a in all_links:
                if keyword in a.get_text(strip=True).lower():
                    links[name] = urljoin(self.base_url, a['href'])
                    break
        
        return socials, contacts, links

    # Main Orchestration Method
    async def run(self) -> BrandContext:
        homepage_soup = await self._get_soup(self.base_url)
        if not homepage_soup:
            raise ValueError("Could not fetch the website's homepage.")
            
        store_name = homepage_soup.find('title').get_text(strip=True) if homepage_soup.find('title') else "Unknown Store"

        # Run tasks concurrently for speed
        results = await asyncio.gather(
            self.get_product_catalog(),
            self.get_hero_products(homepage_soup),
            self.find_and_scrape_page(homepage_soup, ['privacy']),
            self.find_and_scrape_page(homepage_soup, ['refund', 'return']),
            self.get_faqs(homepage_soup),
            self.get_site_wide_info(homepage_soup),
            self.find_and_scrape_page(homepage_soup, ['about', 'our story'])
        )

        # Unpack results
        all_products, hero_products, privacy, refund, faqs, site_info, about_page = results
        socials, contacts, important_links = site_info
        
        # Assemble the final BrandContext object
        brand_data = BrandContext(
            store_name=store_name,
            base_url=self.base_url,
            all_products=all_products,
            hero_products=hero_products,
            privacy_policy=privacy,
            refund_policy=refund,
            faqs=faqs,
            social_handles=socials,
            contact_details=contacts,
            about_us_context=about_page.content if about_page else None,
            important_links=important_links
        )
        return brand_data