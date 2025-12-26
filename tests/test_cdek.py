"""
Тесты для эндпоинтов CDEK
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_get_cities_by_name(client: httpx.AsyncClient):
    """Тест получения списка городов по названию 'таганрог'"""
    response = await client.get(
        "/api/cdek/suggest_cities",
        params={"name": "таганрог"}
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    cities = response.json()
    assert isinstance(cities, list), "Response should be a list"
    assert len(cities) > 0, "Should return at least one city"
    
    # Проверяем структуру первого города
    city = cities[0]
    assert "city_uuid" in city, "City should have city_uuid"
    assert "code" in city, "City should have code"
    assert "full_name" in city, "City should have full_name"
    assert "country_code" in city, "City should have country_code"
    
    # Проверяем, что в списке есть Таганрог
    city_names = [c["full_name"].lower() for c in cities]
    assert any("таганрог" in name for name in city_names), "Should find Таганрог in results"
    
    return cities


@pytest.mark.asyncio
async def test_get_offices_by_city_code(client: httpx.AsyncClient):
    """Тест получения списка офисов по коду города из первого теста"""
    # Сначала получаем список городов
    cities_response = await client.get(
        "/api/cdek/suggest_cities",
        params={"name": "таганрог"}
    )
    
    assert cities_response.status_code == 200, "Should get cities successfully"
    cities = cities_response.json()
    assert len(cities) > 0, "Should have at least one city"
    
    # Берем первый город из списка
    first_city = cities[0]
    city_code = first_city["code"]
    
    # Получаем офисы по коду города
    response = await client.get(
        "/api/cdek/offices",
        params={"city_code": city_code}
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    offices = response.json()
    assert isinstance(offices, list), "Response should be a list"
    
    # Если есть офисы, проверяем их структуру
    if len(offices) > 0:
        office = offices[0]
        assert "code" in office, "Office should have code"
        assert "uuid" in office, "Office should have uuid"
        assert "type" in office, "Office should have type"
        assert "city_code" in office, "Office should have city_code"
        assert "city" in office, "Office should have city"
        assert "longitude" in office, "Office should have longitude"
        assert "latitude" in office, "Office should have latitude"
        assert "address" in office, "Office should have address"
        
        # Проверяем, что код города совпадает
        assert office["city_code"] == city_code, "Office city_code should match requested city_code"

