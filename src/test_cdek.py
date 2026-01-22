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
        "type": 1,  # Всегда 1
        "number": "1",  # order_id
        "tariff_code": 136,  # Посылка склад-склад 136
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
                "weight": 300,  # total weight in grams
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


def create_waybill(order_uuid: str, copy_count: int = 2):
    """
    Формирование квитанции к заказу
    
    Args:
        order_uuid: UUID заказа в системе CDEK
        copy_count: Число копий квитанции на листе (рекомендуется 2)
    
    Returns:
        JSON ответ с информацией о квитанции
    """
    url = "https://api.cdek.ru/v2/print/orders"
    
    request_data = {
        "orders": [
            {
                "order_uuid": order_uuid
            }
        ],
        "copy_count": copy_count
    }
    
    response = requests.post(
        url,
        json=request_data,
        headers={"Authorization": f"Bearer {get_token()}"}
    )
    
    return response.json()


def get_waybill(waybill_uuid: str):
    """
    Получение квитанции к заказу по UUID квитанции
    
    Args:
        waybill_uuid: UUID квитанции в системе CDEK
    
    Returns:
        JSON ответ с информацией о квитанции (статус, ссылка на скачивание и т.д.)
    """
    url = f"https://api.cdek.ru/v2/print/orders/{waybill_uuid}"
    
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {get_token()}"}
    )
    
    return response.json()


def create_barcode(order_uuid: str, copy_count: int = 1, format: str = "A4", lang: str = "RUS"):
    """
    Формирование ШК места к заказу
    
    Args:
        order_uuid: UUID заказа в системе CDEK
        copy_count: Число копий (по умолчанию 1)
        format: Формат печати - A4, A5, A6, A7 (по умолчанию A4)
        lang: Язык печатной формы - RUS или ENG (по умолчанию RUS)
    
    Returns:
        JSON ответ с информацией о ШК (uuid для скачивания)
    """
    url = "https://api.cdek.ru/v2/print/barcodes"
    
    request_data = {
        "orders": [
            {
                "order_uuid": order_uuid
            }
        ],
        "copy_count": copy_count,
        "format": "A4",
        "lang": lang
    }
    
    response = requests.post(
        url,
        json=request_data,
        headers={"Authorization": f"Bearer {get_token()}"}
    )
    
    return response.json()


def get_barcode(barcode_uuid: str):
    """
    Получение ШК места к заказу по UUID
    
    Args:
        barcode_uuid: UUID ШК в системе CDEK
    
    Returns:
        JSON ответ с информацией о ШК (статус, ссылка на скачивание и т.д.)
    """
    url = f"https://api.cdek.ru/v2/print/barcodes/{barcode_uuid}"
    
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {get_token()}"}
    )
    
    return response.json()


def download_waybill_pdf(waybill_uuid: str, output_filename: str = None):
    """
    Скачивание готовой квитанции в формате PDF
    
    Args:
        waybill_uuid: UUID квитанции в системе CDEK
        output_filename: Имя файла для сохранения (по умолчанию waybill_{uuid}.pdf)
    
    Returns:
        Путь к сохраненному файлу или None при ошибке
    """
    url = f"https://api.cdek.ru/v2/print/orders/{waybill_uuid}.pdf"
    
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {get_token()}"}
    )
    
    if response.status_code == 200:
        filename = output_filename or f"waybill_{waybill_uuid}.pdf"
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Квитанция сохранена в файл: {filename}")
        return filename
    else:
        print(f"Ошибка скачивания квитанции: {response.status_code}")
        print(response.text)
        return None


def download_barcode_pdf(barcode_uuid: str, output_filename: str = None):
    """
    Скачивание готового ШК места в формате PDF
    
    Args:
        barcode_uuid: UUID ШК в системе CDEK
        output_filename: Имя файла для сохранения (по умолчанию barcode_{uuid}.pdf)
    
    Returns:
        Путь к сохраненному файлу или None при ошибке
    """
    url = f"https://api.cdek.ru/v2/print/barcodes/{barcode_uuid}.pdf"
    
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {get_token()}"}
    )
    
    if response.status_code == 200:
        filename = output_filename or f"barcode_{barcode_uuid}.pdf"
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"ШК сохранен в файл: {filename}")
        return filename
    else:
        print(f"Ошибка скачивания ШК: {response.status_code}")
        print(response.text)
        return None




# print(create_waybill("20a52bef-58a7-43cb-9c61-cf4f8a55617a"))
# print(get_waybill("4fa62a24-3107-45a9-a5a4-8b51072fc2f7"))
# download_waybill_pdf("4fa62a24-3107-45a9-a5a4-8b51072fc2f7")

# print(create_barcode("20a52bef-58a7-43cb-9c61-cf4f8a55617a"))
print(get_barcode("816d0d30-e9aa-40e6-bd3c-bfb302609ee8"))
# download_barcode_pdf("d412164e-ca8b-4c6f-8f26-d592b32e13cf")


# Тест скачивания ШК

# for office in offices:
#     print(office["code"])
#     print(office["location"]["address"])
#     print(office["location"]["address_full"])
#     print(office["location"])
#     print(10*"-")