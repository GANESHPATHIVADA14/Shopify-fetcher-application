# app/db/models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    url = Column(String(255), unique=True, index=True)
    products = relationship("Product", back_populates="store")
    # ... add other fields like policies, about_us text etc.

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    shopify_product_id = Column(Integer, unique=True)
    title = Column(String(255), index=True)
    vendor = Column(String(255))
    store_id = Column(Integer, ForeignKey("stores.id"))
    store = relationship("Store", back_populates="products")