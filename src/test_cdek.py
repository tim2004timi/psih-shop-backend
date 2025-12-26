import requests



def get_token():
    url = "https://api.cdek.ru/v2/oauth/token"
    response = requests.post(url, data={"grant_type": grant_type, "client_id": client_id, "client_secret": client_secret})
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

offices = get_offices()
print(offices[0])
# for office in offices:
#     print(office["code"])
#     print(office["location"]["address"])
#     print(office["location"]["address_full"])
#     print(office["location"])
#     print(10*"-")