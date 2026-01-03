import requests
from config import settings



def get_token():
    url = "https://api.cdek.ru/v2/oauth/token"
    response = requests.post(url, data={"grant_type": "client_credentials", "client_id": settings.CDEK_ACCOUNT, "client_secret": settings.CDEK_SECURE_PASSWORD})
    return response.json()["access_token"]
    

def get_locations():
    url = "https://api.edu.cdek.ru/v2/location/suggest/cities"
    response = requests.get(url, params={"name": "ейский"}, headers={"Authorization": f"Bearer {get_token()}"})
    return response.json()


def get_offices():
    # 347931
    url = "https://api.cdek.ru/v2/deliverypoints"
    response = requests.get(url, params={"city_code": 1069, "type": "PVZ"}, headers={"Authorization": f"Bearer {get_token()}"})
    return response.json()

def create_order():
    url = "https://api.cdek.ru/v2/orders"
    
    # Получаем токен
    token = get_token()
    
    # Подготавливаем данные заказа
    order_data = {
        "type": 1,  # Интернет-магазин
        "number": "1",  # order_id
        "tariff_code": 136,  # Посылка склад-склад
        "shipment_point": "MSK5",  # Код ПВЗ отправления
        "delivery_point": "MSK71",  # Код ПВЗ доставки
        "recipient": {
            "name": "Tim",
            "phones": [
                {
                    "number": "+79991234567"
                }
            ]
        },
        "packages": [
            {
                "number": "1",  # order_id
                "weight": 300,
                "items": [
                    {
                        "name": "Тестовый товар",
                        "ware_key": "slug-black-s",  # slug-color-size
                        "payment": {
                            "value": 1000.0,  # price float
                        },
                        "cost": 1000,  # price int
                        "weight": 300,
                        "amount": 1
                    }
                ]
            }
        ]
    }
    
    # Отправляем запрос
    response = requests.post(
        url,
        json=order_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    return response.json()
def get_order_info_by_uuid(uuid_):
    url = f"https://api.cdek.ru/v2/orders/{uuid_}"
    response = requests.get(url, headers={"Authorization": f"Bearer {get_token()}"})
    return response.json()

        
# offices = get_offices()
print(get_order_info_by_uuid("501c1089-703f-4ab7-a4ce-40c91c058262"))
# for office in offices:
#     print(office["code"])
#     print(office["location"]["address"])
#     print(office["location"]["address_full"])
#     print(office["location"])
#     print(10*"-")