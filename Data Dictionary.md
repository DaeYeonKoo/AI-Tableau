# Data Dictionary — SL Corporation Quality Claims

> `Context Brief.md`와 함께 읽어야 합니다. 이 문서는 데이터 파일 자체의 구조(컬럼·
> 타입·도메인·관계)를 정의합니다.

## 파일 정보

| 항목 | 내용 |
|---|---|
| 파일 경로 | `data/sl_corporation_quality_claims.csv` |
| 생성 스크립트 | `scripts/generate_claims_data.py` (재실행 시 동일 결과, seed=42) |
| 인코딩 | UTF-8 (BOM 포함, `utf-8-sig`) — Excel/Tableau에서 한글 깨짐 없이 열림 |
| 로우 수 | 2,200건 |
| 그레인(Grain) | **1 row = 1건의 품질 클레임** (claim_id 기준 고유) |
| 기간 | 발생일자(occurrence_date) 기준 2023-01-01 ~ 2025-12-31 (3개년, YoY 비교 가능) |
| 성격 | 100% 합성(가상) 데이터. 실제 클레임 아님 — 상세는 `Context Brief.md` 3장 참고 |

## 컬럼 정의

| # | 컬럼명 | 타입 | Nullable | 설명 |
|---|---|---|---|---|
| 1 | `claim_id` | string (PK) | N | 클레임 고유 ID. `CLM-000001` 형식 |
| 2 | `customer` | string (category) | N | 클레임을 제기한 완성차 고객사. [고객사 코드표](#고객사) 참고 |
| 3 | `customer_plant` | string | N | 고객사의 조립 공장/법인명 (예: `현대자동차 울산공장`, `BMW Leipzig Plant`) |
| 4 | `claim_country` | string (ISO-2) | N | 클레임 발생 국가 코드. `customer_plant` 소재국과 동일 |
| 5 | `claim_language` | string | N | 클레임 원문 언어 코드 (`ko`,`en`,`de`,`zh`,`pt`,`es`,`ja`). `claim_country` 기준 매핑 |
| 6 | `claim_description` | string (free text) | N | 클레임 내용 — `claim_language` 언어로 작성된 자유 서술 (부품명·결함유형·확인장소 포함) |
| 7 | `production_plant` | string (category) | N | 해당 부품을 생산한 SL 사업장. [생산공장 코드표](#생산공장-slcorporation) 참고 |
| 8 | `production_country` | string (ISO-2) | N | 생산 공장 소재국 |
| 9 | `part_category` | string (category) | N | 부품 대분류(제품군). [부품 코드표](#부품-카테고리) 참고 |
| 10 | `part_name_ko` | string | N | 부품명(국문) |
| 11 | `part_name_en` | string | N | 부품명(영문) |
| 12 | `part_number` | string | N | 부품 번호. `SL-{카테고리prefix}-{5자리 숫자}` (예: `SL-LMP-48213`) |
| 13 | `production_date` | date (YYYY-MM-DD) | N | 부품 생산일자 |
| 14 | `delivery_date` | date (YYYY-MM-DD) | N | 고객사 납품일자 (production_date 이후) |
| 15 | `occurrence_date` | date (YYYY-MM-DD) | N | 결함 발생(확인)일자 (delivery_date 이후) |
| 16 | `claim_received_date` | date (YYYY-MM-DD) | N | 클레임 접수일자 (occurrence_date 이후, +1~15일) |
| 17 | `claim_confirmed_date` | date (YYYY-MM-DD) | **Y** | 클레임 확정(종결)일자. `claim_status`가 확정/기각/보상완료일 때만 값 존재, 접수/조사중이면 빈값(진행 중) |
| 18 | `claim_status` | string (category) | N | 클레임 처리 상태. [상태 코드표](#클레임-상태) 참고 |
| 19 | `defect_type_ko` | string (category) | N | 결함 유형(국문) |
| 20 | `defect_type_en` | string (category) | N | 결함 유형(영문). [결함유형 코드표](#결함-유형) 참고 |
| 21 | `severity` | string (category) | N | 심각도 — `claim_amount_usd` 기준 자동 산정 (`Critical`≥15,000 / `Major`≥3,000 / `Minor`<3,000, 단위 USD) |
| 22 | `claim_quantity` | integer | N | 클레임 대상 수량(개) |
| 23 | `unit_price_usd` | float | N | 부품 단가(USD). `part_category`별 가격대에서 랜덤 산정 |
| 24 | `claim_amount_usd` | float | N | 클레임 금액(USD) = `claim_quantity` × `unit_price_usd` × 처리비용 계수(0.8~1.3) |

### 날짜 순서 규칙 (모든 로우에 적용됨)

```
production_date ≤ delivery_date ≤ occurrence_date ≤ claim_received_date ≤ claim_confirmed_date(있는 경우)
```

## 코드표

### 고객사

| customer | 소속 국가(customer_plant) |
|---|---|
| Hyundai | KR, US, CN |
| Kia | KR, US, IN |
| GM | KR, US, CN, BR |
| BMW | DE, US, CN |
| Ford | US, DE, CN |
| Stellantis | US, MX |
| Honda | US, JP |
| Subaru | US, JP |
| KGM | KR |

### 생산공장 (SL Corporation)

| production_plant | production_country |
|---|---|
| SL 진량공장, SL 대구공장, SL 안산공장, SL 천안공장, SL 성서공장, SL 미러텍(시흥) | KR |
| SL Tennessee, SL Alabama | US |
| 북경삼립, SL 옌타이, 동풍삼립(우한), 상해삼립, 호북삼립 | CN |
| SL Brazil | BR |
| SL Mexico (SLP) | MX |
| SL Poland | PL |
| SL Lumax (India) | IN |

### 부품 카테고리

| part_category | 예시 부품 |
|---|---|
| Lamp Systems | Head Lamp, Tail Lamp, Fog Lamp, Daytime Running Lamp, Rear Combination Lamp |
| Mirror Systems | Outside Mirror, Inside Mirror, Side Repeater Mirror |
| Chassis Systems | Lower Control Arm, Steering Knuckle, Stabilizer Link |
| Front End Module | Bumper Beam, Bonnet Latch, Horn, Radiator Support |
| Electrification | Actuator Motor, Wiring Harness, Sensor Module, Power Window Switch |

### 결함 유형

| defect_type_ko | defect_type_en |
|---|---|
| 조립불량 | Assembly Defect |
| 소재불량 | Material Defect |
| 설계결함 | Design Flaw |
| 표면·도금불량 | Surface & Plating Defect |
| 크랙·파손 | Crack & Breakage |
| 이물혼입 | Foreign Material Contamination |
| 치수불량 | Dimensional Out-of-Spec |
| 기능불량 | Functional Failure |
| 배선·전장불량 | Wiring & Electrical Defect |
| 기타 | Other |

### 클레임 상태

| claim_status | 의미 | claim_confirmed_date |
|---|---|---|
| 접수 | 접수 직후, 조사 미착수 | 없음 |
| 조사중 | 원인 조사 진행 중 | 없음 |
| 확정 | 클레임 인정·확정 | 있음 |
| 기각 | 클레임 반려 | 있음 |
| 보상완료 | 인정 후 보상까지 완료 | 있음 |

## 알려진 한계 (Known Limitations)

- 합성 데이터이므로 계절성, 특정 결함의 실제 근본원인 상관관계 등은 랜덤 생성
  규칙(가중치 기반)을 따르며 실제 품질 이슈 패턴과 다를 수 있습니다.
- `claim_amount_usd`는 통화 환산 없이 전 건 USD로 통일해 생성했습니다 (대시보드
  단순화 목적).
- `customer_plant` 목록은 실제 존재하는 완성차 공장명을 참고했으나, 특정 클레임이
  해당 공장에서 실제 발생했다는 사실 관계는 전혀 없습니다 (전량 가상 매핑).
