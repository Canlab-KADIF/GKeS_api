import json
import os

def find_missing_keys(standard, check, path=""):
    standard_missing = []  # check 기준으로 standard에 없는 속성
    check_missing = []  # standard 기준으로 check에 없는 속성

    all_keys = set(standard.keys()) | set(check.keys())  # 두 dict의 모든 키
    
    for key in all_keys:
        new_path = f"{path}.{key}" if path else key  # 현재 경로

        if key not in standard:
            standard_missing.append(new_path)
        elif key not in check:
            check_missing.append(new_path)
        elif isinstance(standard[key], dict) and isinstance(check[key], dict):
            sm, cm = find_missing_keys(standard[key], check[key], new_path)  # 재귀 호출
            standard_missing.extend(sm)
            check_missing.extend(cm)

    return standard_missing, check_missing

def get_datas_from_folder(folder):
    name = os.path.basename(folder)
    meta_path = os.path.join(folder, name+'_meta.json')
    route_path = os.path.join(folder, name+'_route.json')
    
    with open(meta_path, 'r', encoding='utf-8 sig') as f:
        meta_data = json.load(f)
        
    with open(route_path, 'r') as f:
        route_data = json.load(f)
        
    return meta_data, route_data

def check(check_meta, check_route, standard_data_folder):
    standard_meta, standard_route = get_datas_from_folder(standard_data_folder)
    
    extra_meta_keys_in_check, missing_meta_keys_in_check = find_missing_keys(
        standard_meta, check_meta
    )
    extra_route_keys_in_check, missing_route_keys_in_check = find_missing_keys(
        standard_route["data"][0], check_route["data"][0]
    )

    return extra_meta_keys_in_check, missing_meta_keys_in_check, extra_route_keys_in_check, missing_route_keys_in_check

def check_and_print(check_data_folder, standard_data_folder):   
    check_meta, check_route = get_datas_from_folder(check_data_folder)
    extra_meta, missing_meta, extra_route, missing_route = check(check_meta, check_route, standard_data_folder)

    if extra_meta:
        print("\n---------- META ----------")
        print("✅ check 에만 있음. standard 에 없음:")
        for key in extra_meta:
            print(f"- {key}")
    
    if missing_meta:
        print("\n⚠️ standard 에만 있음. check 에 없음:")
        for key in missing_meta:
            print(f"- {key}")

    if extra_route:
        print("\n---------- ROUTE ----------")
        print("✅ check 에만 있음. standard 에 없음:")
        for key in extra_route:
            print(f"- {key}")

    if missing_route:
        print("\n⚠️ standard 에만 있음. check 에 없음:")
        for key in missing_route:
            print(f"- {key}")