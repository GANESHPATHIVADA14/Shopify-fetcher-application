from fastapi import APIRouter, HTTPException, status
from app.schemas.brand import InsightRequest, BrandContext
from app.services.scraper import ShopifyScraper

router = APIRouter()

@router.post("/fetch-insights", response_model=BrandContext)
async def fetch_store_insights(request: InsightRequest):
    """
    Accepts a Shopify store URL and returns a structured JSON object
    with insights scraped from the website.
    """
    scraper = ShopifyScraper(str(request.website_url))
    try:
        brand_data = await scraper.run()
        return brand_data
    except ValueError as e:
        # This can be triggered if the homepage is unreachable
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website not found or unreachable: {e}"
        )
    except Exception as e:
        # Generic catch-all for any other scraping or parsing error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred: {e}"
        )
    finally:
        await scraper.close() # Ensure the httpx client is closed