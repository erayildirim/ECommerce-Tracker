"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "E-Commerce Price Tracker" in response.json()["message"]


def test_get_statistics(client):
    """Test statistics endpoint."""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_products" in data
    assert "total_sites_tracked" in data


# def test_create_product(client):
#     """Test product creation."""
#     product_data = {
#         "product_name": "Test Product",
#         "price": 99.99,
#         "url": "https://example.com/product/123",
#         "currency": "USD",
#         "stock_status": "in_stock"
#     }
#     
#     response = client.post("/api/v1/products", json=product_data)
#     assert response.status_code == 200
#     data = response.json()
#     assert data["product_name"] == product_data["product_name"]
#     assert data["price"] == product_data["price"]


# def test_list_products(client):
#     """Test product listing."""
#     response = client.get("/api/v1/products")
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
