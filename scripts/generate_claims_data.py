# -*- coding: utf-8 -*-
"""
SL Corporation 품질 클레임(Quality Claim) 합성 데이터 생성 스크립트.
실존 기업 SL Corporation(자동차 부품 - 램프/미러/샤시/FEM/전장)의 사업 구조를
참고하여 만든 100% 가상의 학습용 데이터셋을 생성한다. (실제 클레임 데이터 아님)
"""
import csv
import random
from datetime import date, timedelta

random.seed(42)

AS_OF_DATE = date(2025, 12, 31)
OCCURRENCE_START = date(2023, 1, 1)
OCCURRENCE_END = date(2025, 12, 31)
N_ROWS = 2200

# ---- 코드 테이블 ----------------------------------------------------------

# customer -> [(plant_name, country_code), ...]
CUSTOMER_PLANTS = {
    "Hyundai": [
        ("현대자동차 울산공장", "KR"), ("현대자동차 아산공장", "KR"),
        ("HMMA (Hyundai Motor Manufacturing Alabama)", "US"),
        ("HMGMA (Hyundai Motor Group Metaplant America)", "US"),
        ("Beijing Hyundai Motor (BHMC)", "CN"),
    ],
    "Kia": [
        ("기아 화성공장", "KR"), ("기아 광명공장", "KR"), ("기아 광주공장", "KR"),
        ("Kia Georgia Plant", "US"), ("Kia India (Anantapur)", "IN"),
    ],
    "GM": [
        ("GM Korea 부평공장", "KR"), ("GM Korea 창원공장", "KR"),
        ("GM Spring Hill Assembly", "US"), ("GM Fort Wayne Assembly", "US"),
        ("SAIC-GM Shanghai", "CN"), ("GM Brazil Gravataí", "BR"),
    ],
    "BMW": [
        ("BMW Leipzig Plant", "DE"), ("BMW Munich Plant", "DE"),
        ("BMW Spartanburg Plant", "US"), ("BMW Brilliance Shenyang", "CN"),
    ],
    "Ford": [
        ("Ford Kentucky Truck Plant", "US"), ("Ford Michigan Assembly", "US"),
        ("Ford-Werke Cologne", "DE"), ("Changan Ford Chongqing", "CN"),
    ],
    "Stellantis": [
        ("Stellantis Toledo Assembly", "US"), ("Stellantis Sterling Heights Assembly", "US"),
        ("Stellantis Toluca Assembly", "MX"),
    ],
    "Honda": [
        ("Honda Marysville Auto Plant", "US"), ("Honda Suzuka Factory", "JP"),
    ],
    "Subaru": [
        ("Subaru of Indiana Automotive", "US"), ("Subaru Gunma Oizumi Plant", "JP"),
    ],
    "KGM": [
        ("KGM 평택공장", "KR"),
    ],
}
CUSTOMER_WEIGHTS = {  # 실제 주요 매출 비중을 단순화해 반영 (현대/기아 비중 높게)
    "Hyundai": 22, "Kia": 20, "GM": 16, "BMW": 10, "Ford": 10,
    "Stellantis": 8, "Honda": 6, "Subaru": 4, "KGM": 4,
}

COUNTRY_LANGUAGE = {
    "KR": "ko", "US": "en", "DE": "de", "CN": "zh",
    "BR": "pt", "MX": "es", "IN": "en", "JP": "ja",
}

# production_plant -> country_code
PRODUCTION_PLANTS = [
    ("SL 진량공장", "KR"), ("SL 대구공장", "KR"), ("SL 안산공장", "KR"),
    ("SL 천안공장", "KR"), ("SL 성서공장", "KR"), ("SL 미러텍(시흥)", "KR"),
    ("SL Tennessee", "US"), ("SL Alabama", "US"),
    ("북경삼립", "CN"), ("SL 옌타이", "CN"), ("동풍삼립(우한)", "CN"),
    ("상해삼립", "CN"), ("호북삼립", "CN"),
    ("SL Brazil", "BR"), ("SL Mexico (SLP)", "MX"),
    ("SL Poland", "PL"), ("SL Lumax (India)", "IN"),
]
PLANTS_BY_COUNTRY = {}
for name, cc in PRODUCTION_PLANTS:
    PLANTS_BY_COUNTRY.setdefault(cc, []).append(name)

# 고객 국가 -> 선호 생산공장 권역 (물류 허브 구조 단순 반영)
REGION_PREFERENCE = {
    "KR": ["KR"], "US": ["US"], "CN": ["CN"], "BR": ["BR"], "MX": ["MX"],
    "IN": ["IN"], "DE": ["PL", "KR"], "JP": ["CN", "KR"],
}

# category -> [(name_ko, name_en), ...], part_number prefix
PART_CATALOG = {
    "Lamp Systems": {
        "prefix": "LMP",
        "parts": [("전조등", "Head Lamp"), ("후미등", "Tail Lamp"), ("안개등", "Fog Lamp"),
                  ("주간주행등", "Daytime Running Lamp"), ("리어콤비램프", "Rear Combination Lamp")],
    },
    "Mirror Systems": {
        "prefix": "MIR",
        "parts": [("아웃사이드미러", "Outside Mirror"), ("룸미러", "Inside Mirror"),
                  ("사이드리피터미러", "Side Repeater Mirror")],
    },
    "Chassis Systems": {
        "prefix": "CHS",
        "parts": [("로어암", "Lower Control Arm"), ("너클", "Steering Knuckle"),
                  ("스태빌라이저링크", "Stabilizer Link")],
    },
    "Front End Module": {
        "prefix": "FEM",
        "parts": [("범퍼빔", "Bumper Beam"), ("본넷래치", "Bonnet Latch"),
                  ("혼", "Horn"), ("라디에이터서포트", "Radiator Support")],
    },
    "Electrification": {
        "prefix": "ELE",
        "parts": [("액추에이터모터", "Actuator Motor"), ("와이어링하네스", "Wiring Harness"),
                  ("센서모듈", "Sensor Module"), ("파워윈도우스위치", "Power Window Switch")],
    },
}
UNIT_PRICE_RANGE_USD = {
    "Lamp Systems": (25, 90), "Mirror Systems": (20, 70), "Chassis Systems": (12, 45),
    "Front End Module": (8, 35), "Electrification": (10, 55),
}

DEFECT_TYPES = [
    ("조립불량", "Assembly Defect"), ("소재불량", "Material Defect"),
    ("설계결함", "Design Flaw"), ("표면·도금불량", "Surface & Plating Defect"),
    ("크랙·파손", "Crack & Breakage"), ("이물혼입", "Foreign Material Contamination"),
    ("치수불량", "Dimensional Out-of-Spec"), ("기능불량", "Functional Failure"),
    ("배선·전장불량", "Wiring & Electrical Defect"), ("기타", "Other"),
]

STATUS_LIST = ["접수", "조사중", "확정", "기각", "보상완료"]
SEVERITY_LIST = ["Critical", "Major", "Minor"]

DESC_TEMPLATE = {
    "ko": "{part_name}({part_number}) 부품에서 {defect} 발생. {plant}에서 확인됨.",
    "en": "{defect} detected on {part_name} ({part_number}). Identified at {plant}.",
    "de": "{defect} bei {part_name} ({part_number}) festgestellt. Erkannt bei {plant}.",
    "zh": "在{part_name}（{part_number}）上发现{defect}。由{plant}确认。",
    "pt": "{defect} detectado em {part_name} ({part_number}). Identificado na {plant}.",
    "es": "Se detectó {defect} en {part_name} ({part_number}). Identificado en {plant}.",
    "pl": "Wykryto {defect} w {part_name} ({part_number}). Zidentyfikowano w {plant}.",
    "ja": "{part_name}（{part_number}）に{defect}を検出。{plant}にて確認。",
}


def weighted_choice(weights: dict):
    keys = list(weights.keys())
    w = list(weights.values())
    return random.choices(keys, weights=w, k=1)[0]


def rand_date_between(d1: date, d2: date) -> date:
    delta = (d2 - d1).days
    if delta <= 0:
        return d1
    return d1 + timedelta(days=random.randint(0, delta))


rows = []
for i in range(1, N_ROWS + 1):
    claim_id = f"CLM-{i:06d}"

    customer = weighted_choice(CUSTOMER_WEIGHTS)
    plant_name, claim_country = random.choice(CUSTOMER_PLANTS[customer])
    claim_language = COUNTRY_LANGUAGE[claim_country]

    pref_countries = REGION_PREFERENCE[claim_country]
    if random.random() < 0.7:
        pool_country = random.choice(pref_countries)
        pool = PLANTS_BY_COUNTRY.get(pool_country, PRODUCTION_PLANTS)
        production_plant = random.choice(pool) if isinstance(pool[0], str) else random.choice(PRODUCTION_PLANTS)[0]
        production_country = pool_country
    else:
        production_plant, production_country = random.choice(PRODUCTION_PLANTS)

    category = random.choice(list(PART_CATALOG.keys()))
    name_ko, name_en = random.choice(PART_CATALOG[category]["parts"])
    prefix = PART_CATALOG[category]["prefix"]
    part_number = f"SL-{prefix}-{random.randint(10000, 99999)}"
    part_name = name_ko if claim_language == "ko" else name_en

    occurrence_date = rand_date_between(OCCURRENCE_START, OCCURRENCE_END)
    delivery_date = occurrence_date - timedelta(days=random.randint(1, 400))
    production_date = delivery_date - timedelta(days=random.randint(3, 20))

    claim_received_date = occurrence_date + timedelta(days=random.randint(1, 15))
    if claim_received_date > AS_OF_DATE:
        claim_received_date = AS_OF_DATE

    days_since_occurrence = (AS_OF_DATE - occurrence_date).days
    if days_since_occurrence < 20:
        claim_status = random.choices(["접수", "조사중"], weights=[70, 30])[0]
    elif days_since_occurrence < 60:
        claim_status = random.choices(["접수", "조사중", "확정", "기각"], weights=[15, 40, 30, 15])[0]
    else:
        claim_status = random.choices(STATUS_LIST, weights=[3, 12, 45, 15, 25])[0]

    claim_confirmed_date = ""
    if claim_status in ("확정", "기각", "보상완료"):
        cc_date = claim_received_date + timedelta(days=random.randint(3, 45))
        if cc_date > AS_OF_DATE:
            cc_date = AS_OF_DATE
        claim_confirmed_date = cc_date.isoformat()

    defect_ko, defect_en = random.choice(DEFECT_TYPES)
    defect_label = defect_ko if claim_language == "ko" else defect_en

    plant_label = plant_name if customer in plant_name else f"{customer} {plant_name}"
    template = DESC_TEMPLATE[claim_language]
    claim_description = template.format(
        part_name=part_name, part_number=part_number, defect=defect_label,
        plant=plant_label,
    )

    claim_quantity = random.choice([1, 2, 3, 5, 8, 12, 20, 50, 100, 200, 500])
    lo, hi = UNIT_PRICE_RANGE_USD[category]
    unit_price_usd = round(random.uniform(lo, hi), 2)
    cost_factor = round(random.uniform(0.8, 1.3), 2)
    claim_amount_usd = round(claim_quantity * unit_price_usd * cost_factor, 2)

    if claim_amount_usd >= 15000:
        severity = "Critical"
    elif claim_amount_usd >= 3000:
        severity = "Major"
    else:
        severity = "Minor"

    rows.append({
        "claim_id": claim_id,
        "customer": customer,
        "customer_plant": plant_name,
        "claim_country": claim_country,
        "claim_language": claim_language,
        "claim_description": claim_description,
        "production_plant": production_plant,
        "production_country": production_country,
        "part_category": category,
        "part_name_ko": name_ko,
        "part_name_en": name_en,
        "part_number": part_number,
        "production_date": production_date.isoformat(),
        "delivery_date": delivery_date.isoformat(),
        "occurrence_date": occurrence_date.isoformat(),
        "claim_received_date": claim_received_date.isoformat(),
        "claim_confirmed_date": claim_confirmed_date,
        "claim_status": claim_status,
        "defect_type_ko": defect_ko,
        "defect_type_en": defect_en,
        "severity": severity,
        "claim_quantity": claim_quantity,
        "unit_price_usd": unit_price_usd,
        "claim_amount_usd": claim_amount_usd,
    })

fieldnames = list(rows[0].keys())
out_path = "data/sl_corporation_quality_claims.csv"
import os
os.makedirs("data", exist_ok=True)
with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {out_path}")
