import pytest
import json
import os
from api import PetFriends

pf = PetFriends()
valid_email = 'lmao@lmao.lm'
valid_password = 'lmao'

@pytest.fixture(scope='class')
def auth_key(email=valid_email, password=valid_password) -> json:
    status, result = pf.get_api_key(email=email, password=password)
    assert status == 200
    assert 'key' in result
    return result['key']

@pytest.fixture(scope='function')
def get_pet_id(auth_key):
    """Создает временного питомца и возвращает его ID для тестов"""
    status, result = pf.add_new_pet_without_photo(auth_key, 'Тестовый питомец', 'Тестовый вид', 5)
    return result['id']

@pytest.mark.parametrize("password", ['123456'], ids=['invalid pass'])
@pytest.mark.parametrize("email", ['ffff@hhhh.gg'], ids=['invalid email'])
def test_auth_should_fail(email, password):
    status, result = pf.get_api_key(email, password)
    assert status == 403
    assert 'key' not in result

def test_list_pets(auth_key):
    """Проверка списка питомцев"""
    status, result = pf.get_list_of_pets(auth_key)
    assert status == 200 and len(result['pets']) > 0

def test_list_my_pets(auth_key):
    """Проверка списка моих питомцев"""
    status, result = pf.get_list_of_pets(auth_key, 'my_pets')
    assert status == 200 and len(result['pets']) > 0

def test_cant_add_negative_age(auth_key):
    """Проверка добавления питомца с отрицательным возрастом"""
    status, result = pf.add_new_pet_without_photo(auth_key, 'Кот', 'Кот', -99)
    assert status == 400

def test_cant_add_huge_age(auth_key):
    """Проверка добавления питомца с очень большим возрастом"""
    status, result = pf.add_new_pet_without_photo(auth_key, 'Кот', 'Кот', 9999)
    assert status == 400

def test_cant_add_extra_huge_age(auth_key):
    """Проверка добавления питомца с экстремально большим возрастом"""
    status, result = pf.add_new_pet_without_photo(auth_key, 'Кот', 'Кот', 9999999999999999999999999)
    assert status == 400

def test_cant_add_empty_name(auth_key):
    """Проверка добавления питомца с пустым именем"""
    status, result = pf.add_new_pet_without_photo(auth_key, '', '-', 10)
    assert status == 400

def test_cant_add_empty_type(auth_key):
    """Проверка добавления питомца с пустым типом"""
    status, result = pf.add_new_pet_without_photo(auth_key, '-', '', 10)
    assert status == 400

def test_cant_add_long_type(auth_key):
    """Проверка добавления питомца с длинным типом"""
    name = 'ы' * 990
    status, result = pf.add_new_pet_without_photo(auth_key, '-', name, 10)
    assert status == 400

def test_add_new_pet_without_photo_success(auth_key):
    """Добавление питомца без фото"""
    status, result = pf.add_new_pet_without_photo(auth_key, 'Барсик', 'Кот', 3)
    assert status == 200
    assert result['name'] == 'Барсик'
    assert result['animal_type'] == 'Кот'
    assert result['age'] == '3'

def test_add_new_pet_with_photo_success(auth_key):
    """Добавление питомца с фото"""
    test_img_path = 'test_pet_photo.jpg'
    with open(test_img_path, 'w') as f:
        f.write('Test image content')
    try:
        status, result = pf.add_new_pet(auth_key, 'Мурзик', 'Кот', '2', test_img_path)
        assert status == 200
        assert result['name'] == 'Мурзик'
        assert 'pet_photo' in result
    finally:
        if os.path.exists(test_img_path):
            os.remove(test_img_path)

def test_delete_pet_success(auth_key, get_pet_id):
    """Удаление питомца"""
    pet_id = get_pet_id
    status, result = pf.delete_pet(auth_key, pet_id)
    assert status == 200
    status, my_pets = pf.get_list_of_pets(auth_key, 'my_pets')
    assert status == 200
    assert not any(pet['id'] == pet_id for pet in my_pets['pets'])

def test_update_pet_info_success(auth_key, get_pet_id):
    """Обновление информации о питомце"""
    pet_id = get_pet_id
    res = pf.update_pet_info(auth_key, pet_id, 'Обновленный', 'Обновленный вид', 7)
    assert res.status_code == 200
    status, my_pets = pf.get_list_of_pets(auth_key, 'my_pets')
    pet = next(pet for pet in my_pets['pets'] if pet['id'] == pet_id)
    assert pet['name'] == 'Обновленный'
    assert pet['animal_type'] == 'Обновленный вид'
    assert pet['age'] == '7'

def test_add_pet_photo_success(auth_key, get_pet_id):
    """Добавление фото питомцу"""
    pet_id = get_pet_id
    test_img_path = 'test_update_photo.jpg'
    with open(test_img_path, 'w') as f:
        f.write('Updated test image content')
    try:
        status, result = pf.add_pet_photo(auth_key, pet_id, test_img_path)
        assert status == 200
        assert 'pet_photo' in result
    finally:
        if os.path.exists(test_img_path):
            os.remove(test_img_path)

def test_get_list_pets_with_invalid_auth_key():
    """Список питомцев с неверным ключом"""
    status, result = pf.get_list_of_pets('invalid_auth_key')
    assert status == 403

def test_add_pet_with_invalid_auth_key():
    """Добавление питомца с неверным ключом"""
    status, result = pf.add_new_pet_without_photo('invalid_auth_key', 'Тест', 'Тест', 5)
    assert status == 403

def test_delete_pet_with_invalid_auth_key(auth_key, get_pet_id):
    """Удаление питомца с неверным ключом"""
    pet_id = get_pet_id
    status, result = pf.delete_pet('invalid_auth_key', pet_id)
    assert status == 403

def test_delete_pet_with_invalid_id(auth_key):
    """Удаление питомца с несуществующим ID"""
    status, result = pf.delete_pet(auth_key, 'invalid_pet_id')
    assert status == 404 or status == 400

def test_update_pet_with_invalid_auth_key(get_pet_id):
    """Обновление питомца с неверным ключом"""
    pet_id = get_pet_id
    res = pf.update_pet_info('invalid_auth_key', pet_id, 'Тест', 'Тест', 5)
    assert res.status_code == 403

def test_update_pet_with_invalid_id(auth_key):
    """Обновление питомца с несуществующим ID"""
    res = pf.update_pet_info(auth_key, 'invalid_pet_id', 'Тест', 'Тест', 5)
    assert res.status_code == 404 or res.status_code == 400
