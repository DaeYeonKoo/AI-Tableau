# Tableau 구현 가이드 (학습 노트)

> **이 문서의 성격**: `.twb` 파일을 실제로 만들기 위해 필요한 지식을 계속 채워나가는 **성장형 문서**입니다.
> `.twb` 생성은 잠시 미루고, 먼저 이 문서에 지식을 쌓습니다. Claude Code로 핸드오프하기 전 최종
> 레퍼런스가 됩니다.
>
> **신뢰도 표기 규칙** (항목마다 표시):
> - ✅ **검증됨** — 실제 Tableau 2025.3이 저장한 `.twb`/`.twbx` 파일로 확인한 내용
> - 🔷 **공식 XSD 스키마 확인됨** — [tableau/tableau-document-schemas](https://github.com/tableau/tableau-document-schemas)
>   공식 스키마 파일로 구조(엘리먼트/속성 존재 여부)를 확인함. **구문(syntax) 유효성**은
>   보장되지만, 실제 Tableau가 그 값을 의미적으로(semantically) 어떻게 처리하는지는 별개 —
>   특히 `connection`, 계산식 `formula` 내용, 액션의 `command` 값 등은 스키마가 의도적으로
>   검증하지 않음(`processContents="skip"`). 아래 §0-1 참고.
> - 📘 **공식문서 기반** — help.tableau.com에서 확인한 UI/개념 설명 (신뢰도 높음, XML 스키마는 아님)
> - ⚠️ **미검증(추정)** — 일반적인 Tableau XML 지식 기반 추정. 실제 파일로 검증 전까지는
>   **그대로 믿지 말 것.** (PPT2 사례: "기억에 의존한 추측은 반복해서 틀렸다")
>
> **목표 환경**: Tableau Desktop **2025.3** (build `20253.26.0109.0333`), 데이터 소스
> `data/sl_corporation_quality_claims.csv`. PC에는 2023.3~2025.3까지 여러 버전이 설치되어 있음.

---

## 0. 왜 이 문서가 필요한가

`참고 자료/2.AI활용_Tableau_생성프로세스_자료.pptx`에 기록된 실제 실패·성공 경험:

- Claude는 Tableau를 직접 열어볼 수 없다 → XML이 실제로 유효한지 스스로 검증 불가
- "전체 생성 시도 → 실패" (한 번에 완성된 `.twb`를 생성하려는 시도는 실패)
- 성공한 방법: **사용자가 Tableau UI에서 직접 만들고 저장 → 그 파일을 Claude가 읽고 그대로
  복제** → 이후 확보한 문법을 마스터 프롬프트(=이 문서)에 규칙으로 축적

→ 그래서 이 문서는 ①공식 문서로 확인 가능한 개념(계산식 문법, 매개변수, 액션 등)을 먼저
채우고, ②XML 스키마처럼 공식 문서에 없는 부분은 "미검증"으로 표시해두었다가, ③실제 시드
파일을 받으면 그 부분을 검증/수정하는 방식으로 운영합니다.

---

## 0-1. 공식 XSD 스키마 확보 (2026-02 신규) 🔷

Tableau가 2026년 2월 **`.twb` 형식의 공식 XSD 스키마**를 처음으로 공개했습니다:
[github.com/tableau/tableau-document-schemas](https://github.com/tableau/tableau-document-schemas).
아래 §1~§9의 상당 부분이 이 스키마로 직접 검증되어 ⚠️→🔷로 승격되었습니다. 다만 몇 가지
중요한 제약을 먼저 알아야 합니다.

### 버전 커버리지 — 우리 목표(2025.3)는 포함 안 됨 ⚠️
저장소에는 `schemas/2026_1/twb_2026.1.0.xsd`, `schemas/2026_2/twb_2026.2.0.xsd` **두 버전만**
있습니다. 2025.3용 공식 스키마는 없습니다. TWB 스키마는 버전 간 하위 호환성이 높아(핵심 구조가
안정적으로 유지되는 편) 2026.2 스키마를 "가장 가까운 참고자료"로 쓰고 있지만, **2025.3 고유의
차이가 있을 수 있다는 점은 감안**해야 합니다. (참고로 README는 `<workbook version='...'>` 값이
`26.1` ↔ XSD 파일명 `twb_2026.1.0.xsd`처럼 대응한다고 설명합니다 — 즉 2025.3은 아마
`version='25.3'` 근처일 것으로 추정되지만 ⚠️ 미검증.)

### 구문 검증(Syntactic) vs 의미 검증(Semantic) — README 원문 인용
> Successful syntactic validation means that the TWB follows the structure rules imparted by
> the XSD. Syntactic validation **doesn't guarantee that a workbook will open in Tableau.**

즉 **"XSD를 통과한다" ≠ "Tableau에서 정상적으로 열린다."** 아래는 README가 명시적으로
"XSD로 검증되지 않는 것"이라고 밝힌 항목 — 이 부분들은 스키마를 아무리 확인해도 여전히
**실제 파일/실제 Tableau로만 검증 가능**합니다:
- `connection` 엘리먼트의 속성들 (데이터 연결 정보 — §2)
- 계산 필드의 내용(함수명, 필드 참조 등 `formula` 문자열 자체 — §4)
- 다른 워크북 요소를 가리키는 참조(탭 이름 등)

(스키마 내부에서 이런 부분은 `processContents="skip"` 또는 `<xs:any>`/`<xs:anyAttribute>`로
표시되어 있어 검색으로 위치를 특정할 수 있습니다.)

### 실전 활용법 — XML 검증 자동화 가능해짐 🔷
`.twb`가 XML이고 XSD가 공개되었으므로, **`.twb`를 작성한 뒤 `lxml`(Python)로 스키마 검증을
자동으로 돌려볼 수 있습니다.** 즉:
1. `.twb` 작성 (또는 수정)
2. `lxml.etree.XMLSchema(twb_2026.2.0.xsd)`로 구문 오류를 즉시 스스로 확인 (Tableau 없이도!)
3. 구문 오류 없는 상태로 만든 뒤 사용자에게 전달 → Tableau에서 열어 **의미 검증**
4. 열리면 성공, 안 열리면 그 부분만 §2/§4/§9 같은 "XSD가 검증 못 하는 영역"으로 좁혀서 원인 추적

이 흐름은 기존의 "완전히 맹목적인 시행착오"보다 훨씬 빠릅니다 — 최소한 XML 구조 오류(태그
철자, 필수 속성 누락, 잘못된 중첩)는 Tableau를 열지 않고도 걸러낼 수 있습니다.

### Tableau Server/Cloud REST API 검증 (참고, 우리는 미해당)
Tableau Cloud 2026년 6월 / Server 2026.2부터 REST API로 서버 측 구문+의미 검증이 가능하다고
합니다 (Validate Workbook 등). 우리는 Server/Cloud 없이 Desktop만 쓰므로 해당 없음.

### `.twbx` 미지원
이 스키마 저장소는 `.twb`(단일 XML)만 다루고, 패키지 형식인 `.twbx`는 지원하지 않습니다.
우리는 어차피 `.twb` + 외부 CSV 연결 방식을 쓰기로 했으므로 문제 없음.

---

## 1. `.twb` 파일 최상위 구조 개요 🔷

`.twb`는 XML 파일입니다 (`.twbx`는 데이터까지 압축한 패키지 버전 — 우리는 `.twb` + 별도 CSV
연결을 사용). **`WorkbookFile-CT`(루트 타입)의 실제 시퀀스**(2026.2 XSD 기준, 순서 그대로):

```
<workbook>
  <document-format-change-manifest>?   -- 아래 §0-1 ManifestByVersion 참고
  <repository-location>                -- (Workbook-RepositoryLocation-G)
  <preferences>                        -- (Workbook-Preferences-G)
  (스타일 테마 / 스타일)                -- Workbook-StyleTheme-G, Workbook-Styles-G
  (로컬 데이터)                         -- Workbook-LocalData-G
  <datasources>                        -- Workbook-DataSources-G  ★핵심
  (데이터소스 관계)                     -- Workbook-DataSourceRelationships-G
  (지도 소스)                          -- Workbook-MapSources-G
  (공유 뷰)                            -- Workbook-SharedViews-G
  <actions>                            -- Workbook-Actions-G  ★핵심 (§9)
  <worksheets>                         -- Workbook-Worksheets-G  ★핵심
  <dashboards>                         -- Workbook-Dashboards-G  ★핵심
  <windows>                            -- Workbook-Windows-G
  (데이터그래프 / 썸네일 / 도형 등)      -- Workbook-Datagraph-G, Workbook-Thumbnails-G, Shapes-G
  (참조된 확장, Explain Data 등)         -- 우리 프로젝트와 무관, 생략 가능
</workbook>
```

`<workbook>` 자체의 속성 (`Workbook-WorkbookAttributes-AG`, 🔷):
```xml
<workbook original-version='18.1' source-build='2025.3.0' source-platform='win'
          version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
```

### 1-1. ✅ 실제 Tableau 2025.3 오류로 확인된 사실 (최고 신뢰도 — 2026.2 XSD보다 우선)

`SL_Corporation_Quality_Claims.twb` 1차 시도를 사용자가 실제 Tableau 2025.3에서 열어봤고,
"동작을 완료할 수 없습니다" 오류(코드 D2E8DA72)가 발생했습니다. **이 오류 메시지 자체가
Tableau 2025.3의 진짜 파서가 뱉어낸 정확한 content model이라 XSD보다 신뢰도가 높습니다**:

```
Error: element 'explain-data' is not allowed for content model
'(document-format-change-manifest,repository-location?,preferences,style-theme?,style,
local-data?,datasources?,datasource-relationships?,mapsources?,shared-views?,actions?,
worksheets?,dashboards?,windows,thumbnails?,external?)'

Error: element 'simple-id' is not allowed for content model
'(((layout-options?)|(repository-location?)),table)'
```

이걸로 확인/수정된 것:
- ✅ **`version='18.1'`은 2025.3에서 받아들여짐** (버전 불일치 오류가 아니라 그 다음 단계인
  content-model 오류가 났다는 것 자체가 버전 태그는 통과했다는 뜻). §0-1에서 "25.3일 것"이라고
  추정했던 게 **틀렸음** — 2025.3도 여전히 예전 `18.1` 스키마 계열을 씀.
- ✅ **`<workbook>` 최상위는 `document-format-change-manifest`가 필수**(⚠️였던 것과 달리
  `?` 없음), 그 다음 `preferences`, 그 다음 **`style`이 필수**로 있어야 함 (2026.2 XSD엔
  `Workbook-Styles-G`가 있었지만 실제로 최상위에 `<style/>` 엘리먼트가 바로 필요).
- ❌ **`<explain-data>`는 2025.3에 아예 존재하지 않는 엘리먼트** — 2026.x에서 새로 추가된
  기능으로 확인됨. **2025.3 파일에는 절대 넣으면 안 됨.**
- ❌ **`<simple-id>`도 2025.3의 워크시트에는 존재하지 않음** — `<worksheet>`의 content model이
  정확히 `((layout-options?)|(repository-location?)), table` 뿐. `table` 뒤에 아무것도 못 옴.
  (`simple-id`는 대시보드 쪽 `SimpleIdentifierForThisDashboard-G`에서만 쓰이는 것으로 추정 —
  워크시트에는 애초에 해당 없음. §0-1에서 언급했듯 **2026.2 스키마가 2025.3보다 기능이
  많아서 생긴 오탐**의 실제 사례.)
- 🟢 **반대로 오류가 안 난 부분** = 통과했다는 뜻으로 잠정 신뢰 가능: CSV `<connection>`
  구조, 24개 `<column>` 정의, 워크시트의 `<table><view>...<panes>...<rows>/<cols>` 구조 —
  전부 이 1차 오류 목록에 등장하지 않음. (다만 XML 구문 통과 ≠ 데이터가 실제로 로드된다는
  뜻은 아직 아님 — 수정 후 다시 열어봐야 최종 확인됨.)

수정된 최상위 순서 (`scripts/build_twb.py`에 반영 완료): `document-format-change-manifest` →
`preferences` → `style` → `datasources` → `worksheets` → `windows` (둘 다 빈 자기닫힘 태그
`<document-format-change-manifest />`, `<style />`로 일단 시도 — 내용이 필요한지는 다음
테스트에서 확인).

핵심 포인트:
- README 공식 예시(2026.1 기준): `<workbook original-version='26.1' ... version='26.1'>` —
  2026.x부터는 내부 스키마 버전과 제품 버전이 일치하도록 바뀐 것으로 보임. **2025.3은 여전히
  구 체계인 `18.1`을 씀** (✅ §1-1에서 실제 확인 — "25.3일 것"이라던 추측은 틀렸음).
- `<document-format-change-manifest>` 안에 예전에는 사용된 기능을 일일이 나열해야 했는데,
  **README가 권장하는 단순화된 방법**은 `<ManifestByVersion />` 하나만 넣는 것 — 🔷 공식문서 예시:
  ```xml
  <document-format-change-manifest>
    <ManifestByVersion />
  </document-format-change-manifest>
  ```
  이렇게 하면 "이 TWB 버전과 같거나 높은 Tableau"에서 호환됨. **직접 XML을 작성할 때 매우
  유용** — 기능별 매니페스트를 일일이 안 챙겨도 됨.
- 데이터소스는 `<datasources>` 안에 최소 1개(우리 CSV) + 매개변수를 쓸 경우 이름이 정확히
  `Parameters`인 특수 데이터소스가 추가로 생김 (🔷 `hasconnection` 속성 실존 확인, §5).
- `<windows>`는 "지금 열려 있는 탭"을 기록하는 UI 상태값에 가까움 — 워크시트/대시보드 자체
  정의는 `<worksheets>`/`<dashboards>`에 있음. (⚠️ windows 세부 구조는 아직 미조사)
- **로컬라이제이션 참고**: 2026.2 스키마부터 `<user:localizable value="...">` 주석이 붙어
  어떤 문자열이 안전하게 바뀔 수 있는지 표시됨. 우리는 다국어 번역이 목적이 아니라 크게
  중요하진 않지만, `identifier`/`identifier-reference` 타입 속성(예: 워크시트 `name`, 대시보드
  zone의 `name`)은 **다른 곳에서 참조되는 식별자이므로 변경 시 참조하는 곳도 같이 바꿔야 함**
  — 나중에 `caption`(표시용, 자유 변경 가능)과 `name`(식별자, 참조 무결성 필요)을 헷갈리지
  않도록 주의.

---

## 2. 데이터 소스 연결 (CSV) ⚠️ + 🔷(스키마 상 "검증 안 함"이 확인됨)

**중요 발견**: 공식 XSD에서 `<connection>` 엘리먼트는 다음과 같이 정의되어 있음 (🔷 확인됨):
```xml
<xs:element name="connection" type="DataConnection-Connection-CT" minOccurs="0"/>
<!-- DataConnection-Connection-CT 내부 -->
<xs:any/>
<xs:anyAttribute/>
```
즉 **connection 태그 내부는 스키마가 의도적으로 아무 것도 검증하지 않는 완전 자유 영역**
입니다 (README의 "attributes in connection elements" 미검증 항목과 정확히 일치). 이는 곧
**§2 전체가 공식 스키마로도 절대 검증될 수 없고, 오직 실제 Tableau가 저장한 파일을 보고
그대로 베끼는 것만이 확실한 방법**이라는 뜻 — PPT2의 교훈이 스키마 차원에서도 재확인됨.

CSV/텍스트 파일 연결은 Tableau 내부에서 `federated` 데이터소스가 `textscan` 클래스의
`named-connection`을 감싸는 구조로 저장되는 것으로 알려져 있습니다:

```xml
<connection class='federated'>
  <named-connections>
    <named-connection caption='sl_corporation_quality_claims.csv' name='textscan.xxxxxxxx'>
      <connection class='textscan' directory='C:/Users/.../data' filename='sl_corporation_quality_claims.csv'
                  password='' server='' />
    </named-connection>
  </named-connections>
  <relation connection='textscan.xxxxxxxx' name='sl_corporation_quality_claims.csv'
            table='[sl_corporation_quality_claims#csv]' type='table' />
  <metadata-records>
    <metadata-record class='column'>
      <remote-name>customer</remote-name>
      <remote-type>129</remote-type>
      <local-name>[customer]</local-name>
      <parent-name>[sl_corporation_quality_claims#csv]</parent-name>
      <local-type>string</local-type>
      <aggregation>Count</aggregation>
      <contains-null>true</contains-null>
    </metadata-record>
    <!-- 컬럼 수만큼 반복 -->
  </metadata-records>
</connection>
```

**확인이 필요한 리스크 포인트** (PPT2에서 실제로 문제가 됐던 부분과 유사):
- `directory` 경로를 **절대경로**로 박아넣으면 다른 PC(다른 사용자 폴더 구조)에서 파일이
  깨질 수 있음 → Tableau의 "상대 경로" 처리 방식 확인 필요. 실무에서는 `.twb`와 데이터 폴더를
  같은 상대 위치에 두고 Tableau가 상대 경로로 재작성하는지 확인해야 함.
- `remote-type`(ODBC 타입 코드, 예: 129=문자열 계열)은 버전에 따라 다를 수 있음.
- 날짜 컬럼(`production_date`, `delivery_date`, `occurrence_date`, `claim_received_date`,
  `claim_confirmed_date`)이 CSV에서 자동으로 Date 타입으로 인식되는지, 아니면 수동으로
  `local-type`을 지정해야 하는지 ⚠️ 미검증. `claim_confirmed_date`는 미확정 클레임의 경우
  빈 문자열(`""`)인데, Date 타입 컬럼에서 빈 문자열이 Null로 처리되는지도 확인 필요
  (우리 계산식 설계가 이 전제에 의존함 — §5 참고).

---

## 3. 컬럼 정의 & 데이터 타입 매핑 🔷

데이터소스 XML 안에서 각 컬럼은 `<column>` 엘리먼트로 다시 한 번 선언되며 (metadata-record와
별개로), 이 선언이 실제 필드 패널에 보이는 타입/역할을 결정합니다. **`<column>`의 실제
속성 전체 목록** (Column-G, 🔷 확인됨 — 필수만 `use="required"`, 나머지 전부 선택):

```xml
<column name="[customer]" role="dimension" type="nominal" datatype="string" caption="Customer" />
```
- `@name` (필수) — 필드 식별자, `[대괄호]`로 감쌈
- `@role` (필수) — **`FieldRole-ST` enum: `dimension` | `measure` | `unknown`** 3개뿐
- `@type` (필수) — **`FieldType-ST` enum: `nominal` | `ordinal` | `quantitative` | `unknown`**
- `@datatype` (필수) — **`DataType-ST` enum: `integer` | `real` | `string` | `datetime` | `date`
  | `boolean` | `tuple` | `spatial` | `table` | `unknown`** (10종, `date`와 `datetime`이 구분됨)
- `@caption` (선택) — 화면 표시명. 없으면 `name`이 그대로 보임
- 그 외 선택 속성 다수: `aggregation`, `pivot`(`key`|`alias`), `hidden`, `default-format`,
  `semantic-role`, `param-domain-type`(§5), `value`/`alias`(매개변수용) 등

`Data Dictionary.md` 24개 컬럼을 Tableau 타입으로 매핑하면 (🔷 속성명·enum 값은 검증됨,
실제로 이 조합이 Tableau UI에서 기대한 대로 렌더링되는지는 아직 미검증):

| 컬럼 | datatype | role | type |
|---|---|---|---|
| claim_id | string | dimension | nominal |
| customer, customer_plant, claim_country, claim_language | string | dimension | nominal |
| claim_description, production_plant, production_country | string | dimension | nominal |
| part_category, part_name_ko/en, part_number | string | dimension | nominal |
| production_date, delivery_date, occurrence_date, claim_received_date, claim_confirmed_date | date | dimension | ordinal |
| claim_status, defect_type_ko/en, severity | string | dimension | nominal |
| claim_quantity | integer | measure | quantitative |
| unit_price_usd, claim_amount_usd | real | measure | quantitative |

---

## 4. 계산된 필드 (Calculated Fields)

### 4-1. UI에서 만드는 법 📘 (공식문서 확인됨)
분석(Analysis) > 계산된 필드 만들기(Create Calculated Field) → 이름 지정 → 계산 에디터에
`함수 + 필드 + 연산자` 조합으로 수식 입력 → 저장하면 데이터 패널에 새 필드로 추가됨.

### 4-2. XML 구조 🔷
```xml
<column caption="Lead Time To Receive" datatype="integer" name="[Calculation_1234567890123]"
        role="measure" type="quantitative">
  <calculation class="tableau" formula="DATEDIFF(&apos;day&apos;, [occurrence_date], [claim_received_date])" />
</column>
```
`name`이 `[Calculation_<임의의 긴 숫자>]` 형태의 내부 ID이고 `caption`이 화면에 보이는
이름이라는 점이 핵심 — 즉 계산식을 여러 개 추가할 때 ID 충돌 없는 고유값을 만들어야 함
(⚠️ 이 숫자의 생성 규칙은 불명 — 타임스탬프 기반으로 추정. 우리가 직접 만들 때는 그냥
`[Calculation_leadtimetoreceive]`처럼 읽기 쉬운 고유 문자열을 써도 스키마상 문제 없음 — `name`은
`QualifiedName-ST` 타입일 뿐 숫자를 강제하지 않음, 🔷).

**`<calculation>`의 실제 속성** (DataSource-Calculation-G, 🔷 확인됨):
- `@class` (필수) — **`DataSource-CalculationType-ST` enum: `tableau` | `passthrough` | `bin`
  | `categorical-bin`** 4개뿐. 일반 계산식은 항상 `class="tableau"`.
- `@formula` (선택) — 수식 문자열. **XSD 주석 원문**: "The calculated field formula syntax
  should not be translated." → 스키마는 이 문자열의 **내용(함수명, 문법 오류 여부)을 전혀
  검증하지 않음** (자유 문자열). 즉 여기 적은 DATEDIFF 수식이 실제 Tableau 문법에 맞는지는
  스키마가 아니라 §4-3 함수 문서 + 실제 Tableau 계산 에디터로만 확인 가능.
- `@decimals`, `@peg`, `@default` 등은 bin(구간화) 계산 전용, 우리는 미해당

### 4-3. 함수 카테고리 📘 (공식문서 기반, 일부 일반 지식으로 보강)
- **숫자**: ABS, CEILING, FLOOR, ROUND, SQRT, POWER, DIV, MAX, MIN 등
- **문자열**: LEN, LEFT, RIGHT, MID, CONTAINS, REPLACE, SPLIT, TRIM, UPPER/LOWER, FIND 등
- **날짜**: DATEDIFF, DATEADD, DATEPART, DATENAME, DATETRUNC, TODAY, NOW, MAKEDATE 등
- **유형 변환**: INT, FLOAT, STR, DATE, DATETIME
- **논리**: IF/THEN/ELSEIF/ELSE/END, CASE/WHEN/END, IIF, ISNULL, IFNULL, ZN, AND/OR/NOT
- **집계**: SUM, AVG, COUNT, COUNTD, MIN, MAX, MEDIAN, ATTR
- **세부 수준 식(LOD)**: `{FIXED [dim] : AGG(...)}`, `{INCLUDE ...}`, `{EXCLUDE ...}`
- **테이블 계산**: RUNNING_SUM, WINDOW_AVG, RANK, INDEX, LOOKUP, TOTAL

참고: [계산된 필드 작업 팁](https://help.tableau.com/current/pro/desktop/ko-kr/calculations_calculatedfields_tips.htm),
[계산 서식 지정(연산자)](https://help.tableau.com/current/pro/desktop/ko-kr/functions_operators.htm),
[집계 함수](https://help.tableau.com/current/pro/desktop/ko-kr/calculations_calculatedfields_aggregate_create.htm)

### 4-4. 우리 프로젝트에 필요한 계산식 5종 (`대시보드 요구사항.md` §전역 계산 필드 기준)

| 계산 필드명 | Tableau 수식 (초안) | 비고 |
|---|---|---|
| Lead Time To Receive | `DATEDIFF('day', [occurrence_date], [claim_received_date])` | |
| Lead Time To Confirm | `DATEDIFF('day', [claim_received_date], [claim_confirmed_date])` | `claim_confirmed_date`가 Null이면 결과도 Null (미확정 클레임) — CSV 빈값이 Date 컬럼에서 Null로 해석되는지 §2에서 검증 필요 |
| Total Cycle Time | `DATEDIFF('day', [occurrence_date], [claim_confirmed_date])` | 위와 동일한 Null 전제 |
| Is Open | `[claim_status] = "접수" OR [claim_status] = "조사중"` | 불리언. 한글 문자열 비교이므로 인코딩 이슈 없는지 확인 |
| Is Confirmed Liable | `[claim_status] = "확정" OR [claim_status] = "보상완료"` | 불리언 |

⚠️ 위 수식은 문법상 Tableau 표준 계산식 구조를 따르지만, 실제 Tableau 2025.3 계산 에디터에
붙여넣어 오류 없이 저장되는지는 아직 검증 전.

---

## 5. 매개변수 (Parameters) 📘 (공식문서 확인됨) + 🔷(XML)

### 5-1. 개념
데이터 패널 드롭다운 > 매개 변수 만들기 → 이름 / 데이터 유형(정수·실수·문자열·날짜·날짜시간) /
기본값 / 표시 형식 설정. **허용값 방식 3가지**:

| 방식 | 설명 |
|---|---|
| 전체(All) | 텍스트 필드처럼 자유 입력 |
| 목록(List) | 선택 가능한 값들을 사전 지정 (필드 멤버에서 가져오기 가능) |
| 범위(Range) | 최소/최대/단계 크기 지정 |

문자열 매개변수는 **범위를 지원하지 않음**.

### 5-2. XML 구조 🔷
`hasconnection` 속성은 **공식 스키마에 실존** (datasource 최상위 attribute, boolean, 🔷) —
매개변수 전용 데이터소스를 `hasconnection="false"`로 표시하는 우리 가설이 맞았습니다.
`<column>`의 매개변수 관련 속성도 전부 스키마에 존재 (🔷):

```xml
<datasource name='Parameters' hasconnection='false'>
  <column caption="최근 N개월" datatype="integer" name="[Parameter 1]"
          param-domain-type="range" role="measure" type="quantitative" value="12">
    <range min="1" max="60" granularity="1" />
  </column>
  <column caption="비교 기준" datatype="string" name="[Parameter 2]"
          param-domain-type="list" role="measure" type="nominal" value="전체 기간">
    <members>
      <member value="전체 기간" />
      <member value="최근 12개월" />
    </members>
  </column>
</datasource>
```
- `@param-domain-type` (선택) — **`DomainType-ST` enum: `any` | `list` | `range`** — UI의
  "전체/목록/범위" 3가지와 정확히 대응 (🔷 UI 개념과 스키마가 1:1로 확인됨)
- `param-domain-type="list"` → `<members><member value="..." alias="..."/></members>` 사용
- `param-domain-type="range"` → `<range min="..." max="..." granularity="..." period-type-v2="..."/>` 사용
- `@value` — 매개변수의 현재값(기본값)

### 5-3. 우리 프로젝트에서 매개변수가 필요한 곳
현재 `대시보드 기획안.html`의 필터(고객사/생산공장/부품카테고리/시작일/종료일)는 HTML
목업에서는 자바스크립트로 구현했지만, Tableau에서는 **일부는 매개변수, 일부는 필터/액션**으로
나뉠 가능성이 큼:
- 시작일/종료일 → 날짜 필터(Range Filter) 또는 날짜 매개변수 2개 + 계산식 조합 — 어느 쪽이
  적합한지 실제 구현 단계에서 결정 필요 (질문거리로 남겨둠)
- 고객사/생산공장/부품카테고리 → 일반 카테고리 필터로 충분, 매개변수 불필요할 가능성 높음

---

## 6. 워크시트 구조 (마크·인코딩·선반) ⚠️

```xml
<worksheet name="1_KPI">
  <table>
    <view>
      <datasources> ... </datasources>
      <datasource-dependencies datasource="federated.xxxx"> ... 사용된 필드 목록 ... </datasource-dependencies>
      <filter class="categorical" column="[federated.xxxx].[none:customer:nk]" ... />
      <aggregation value="true" />
    </view>
    <style> ... </style>
    <panes>
      <pane selection-relaxation-option="selection-relaxed">
        <mark class="Bar" />
        <encodings>
          <color column="[federated.xxxx].[none:customer:nk]" />
          <text column="[federated.xxxx].[sum:claim_amount_usd:qk]" />
        </encodings>
      </pane>
    </panes>
    <rows>[federated.xxxx].[none:customer:nk]</rows>
    <cols>[federated.xxxx].[sum:claim_amount_usd:qk]</cols>
  </table>
</worksheet>
```

핵심 개념:
- `mark class`: Bar / Line / Area / Circle(산점도) / Square / Text / Map / Pie / Gantt 등
- `encodings`: color, size, label(text), detail, tooltip, shape 등 — 우리 HTML 목업의
  "버블 크기=금액" 같은 인코딩이 여기 대응됨
- `rows`/`cols`: 필드가 `[none:필드명:nk]`(차원, nominal key) 또는
  `[sum:필드명:qk]`(집계된 측정값, quantitative key) 같은 접미사로 표기되는 패턴 ⚠️ 정확한
  접미사 규칙은 실제 파일로 확인 필요 (1차 실물 테스트에서 이 부분은 오류가 안 났음 — §1-1의
  "🟢 통과 추정" 항목. 최종 확정은 아니지만 방향은 맞는 듯)
- ✅ **`<worksheet>`의 실제 content model**(2025.3, §1-1 실물 오류로 확인):
  `((layout-options?)|(repository-location?)), table` — 즉 `<table>` 뒤에는 **아무 형제
  엘리먼트도 올 수 없음** (`<simple-id>` 같은 걸 붙이면 바로 오류)

---

## 7. 서식·색상 (Formatting & Color) ⚠️

카테고리 색상(팔레트) 지정은 워크시트의 `<style>` 안에 `style-rule element="color"`로
들어가는 것으로 보임:

```xml
<style>
  <style-rule element="color">
    <encoding attr="color" field="[federated.xxxx].[none:customer:nk]" type="palette">
      <map to="#1f4e79"><bucket>Hyundai</bucket></map>
      <map to="#c0392b"><bucket>Kia</bucket></map>
    </encoding>
  </style-rule>
</style>
```

우리 HTML 목업에서 이미 확정한 색상 팔레트(navy `#16324f`/`#1f4e79`, red `#c0392b`, amber
`#d98c1f` 등)를 그대로 Tableau 색상 매핑에 재사용하면 HTML 기획안과 최종 `.twb`의 시각적
일관성을 맞출 수 있음.

---

## 8. 대시보드 레이아웃 (Zones) 🔷

**`<zone>`의 실제 속성** (Zone-G, 🔷 확인됨 — 필수 속성이 우리 예상과 달랐던 부분 있음):
- `@x`, `@y`, `@w`, `@h` — **전부 필수, 타입은 `xs:int`** (우리가 추정한 "0~100000 상대
  좌표"가 스키마에 고정된 값은 아니고, 그냥 정수. 실제 스케일은 아래 `is-pixels` 속성에 좌우됨)
- `@id` — 필수, `xs:unsignedInt`. **`zones` 내에서 유일해야 함** (`DemandZoneIdUnique` 제약 — 🔷
  스키마가 실제로 중복 id를 막는 unique 제약을 걺, 우리가 직접 만들 때 id 충돌 주의)
- `@name` — 선택, 문자열. 워크시트를 담는 zone이면 해당 워크시트의 `name`을 가리킴
  (`identifier-reference` — §1 참고, 워크시트 이름 바꾸면 여기도 같이 바꿔야 함)
- `@type-v2` — 선택, `xs:string`이지만 실제로는 `ZoneType-ST`의 값들을 씀 (아래 목록)
- `@is-fixed`, `@fixed-size`, `@hidden`, `@show-title`, `@show-caption`, `@param` 등 다수

**`<zones>` 래퍼 속성** (ZoneCollection-G, 🔷):
```xml
<zones is-pixels="true">
  <zone x="0" y="0" w="1200" h="90" id="2" type-v2="layout-basic">
    <zone x="0" y="0" w="1200" h="90" id="3" name="1_KPI" type-v2="layout-flow" />
  </zone>
</zones>
```
- `@is-pixels` (boolean) — **있으면 x/y/w/h가 실제 픽셀 좌표**. 없거나 false면 예전 방식의
  상대 좌표(0~100000 스케일 — 우리 원래 추정)일 가능성. ⚠️ 어느 쪽이 2025.3 기본값인지는
  실 파일로 확인 필요 — **가장 중요한 미확인 항목 중 하나**로 표시해둠 (좌표 스케일을
  잘못 잡으면 레이아웃이 완전히 깨짐)
- `@use-insets` (boolean)

**`type-v2` (`ZoneType-ST`) 유효값 전체 목록** (🔷, 20개):
`invalid`, `visual`(=워크시트를 담는 일반 zone), `color`, `shape`, `size`, `map`,
`highlighter`, `filter`, `currpage`, `empty`, `title`, `text`, `bitmap`, `web`, `add-in`,
`dashboard-object`, `paramctrl`(매개변수 컨트롤), `flipboard`, `flipboard-nav`,
`layout-basic`(컨테이너), `layout-flow`(컨테이너)

→ 우리 HTML 목업의 각 카드가 워크시트 하나씩이라면 `type-v2="visual"` zone이 되고, 카드들을
묶는 레이아웃 컨테이너는 `layout-basic`/`layout-flow`. 필터 컨트롤은 `filter`,
매개변수 컨트롤은 `paramctrl`.

`<dashboard>`의 `<size>` 속성 (Dashboard-DashboardSizeOptions-G, 🔷): `minwidth`, `minheight`,
`maxwidth`, `maxheight` (전부 `xs:int`), `sizing-mode`(`DashboardSizingMode-ST`, 값 목록은
아직 미조사).

`대시보드 요구사항.md`에서 정의한 페이지별 컴포넌트 배치(KPI 카드 5개 / 트렌드 / 지도+랭킹
등)를 이 zone 좌표로 변환해야 함.

---

## 9. 액션 (Filter / Highlight / URL Actions) 📘 + 🔷(뼈대) + ⚠️(필터 command 값)

### 9-1. 필터 액션 개념 📘 (공식문서 확인됨)
워크시트 간에 정보를 보내는 방식. 사용자가 한 시트에서 데이터를 선택하면 관련된 다른
시트가 자동으로 필터링됨.

절차:
1. 워크시트 메뉴 > 동작(Actions), 또는 대시보드 메뉴 > 동작
2. 동작 추가 > 필터 선택
3. 이름 지정, 원본 시트 선택
4. 실행 조건: **마우스오버 / 선택(클릭) / 메뉴(우클릭)** 중 선택
5. 대상 시트 선택 + 선택 해제 시 동작(필터 유지 / 모든 값 표시 / 모든 값 제외) 정의
6. 원본↔대상 필드 매핑

이 개념이 정확히 우리 HTML 목업에서 구현한 "소형멀티플 카드 클릭 → 카테고리 필터",
"고객사 구성 바 클릭 → 고객사 필터" 인터랙션에 대응됨.

### 9-2. XML 구조 🔷 (이전 초안을 실제 스키마로 대폭 수정함)

⚠️ **이전 버전에 적어뒀던 `<filter><source>...<target>...<field-map>` 구조는 틀렸습니다.**
공식 스키마로 확인한 실제 구조는 다음과 같습니다 — `<action>`은 하나의 통합된 형태이고,
"필터 액션"이라는 별도 태그가 있는 게 아니라 `<link>`/`<command>` 유무와 내용으로
필터/하이라이트/URL 액션이 구분되는 것으로 보입니다:

```xml
<actions>
  <action name="카테고리 필터 액션">
    <activation type="on-select" auto-clear="true" />
    <source type="sheet" worksheet="2_소형멀티플" />
    <!-- 여기부터 액션 종류에 따라 갈라짐: -->
    <link>                              <!-- URL 액션인 경우 -->
      <url-action-type>browser</url-action-type>
      <url-action-target>...</url-action-target>
    </link>
    <command command="namespace:command-name">   <!-- 필터/하이라이트 등은 command로 표현되는 듯 -->
      <param name="..." value="..." />
    </command>
  </action>
</actions>
<!-- 액션 종류가 다른 최상위 엘리먼트로도 존재: -->
<nav-action name="..." />              <!-- 시트 이동 액션 -->
<edit-group-action name="..." />       <!-- 그룹 편집 액션 -->
<edit-parameter-action name="...">     <!-- 매개변수 변경 액션 (우리 필터에 유용할 수 있음) -->
  <agg-type type="..." />
  <clear-option type="..." />
  <params><param name="..." value="..." /></params>
</edit-parameter-action>
```

**확인된 세부 사항** (🔷):
- `<activation>` — `@type`은 `ActivationMethod-ST` enum: **`explicit`(선택/클릭) | `on-select` |
  `on-hover`(마우스오버)** 3개. `@auto-clear`(boolean) — 선택 해제 시 자동 클리어 여부
- `<source>` — `@type`은 `SourceType-ST` enum: **`all` | `datasource` | `sheet`** 3개뿐.
  `@worksheet`/`@dashboard`는 이름 참조(문자열), `<exclude-sheet name="...">`로 특정 시트 제외 가능
- `<link>`는 **URL 액션 전용**으로 보임 (`url-action-type`: `default-zone-or-browser` |
  `browser` | `specific-zone`)
- `<command command="ns:name">` — **`ActionList-CommandName-ST`는 `"[^:]+:[^:]+"` 패턴의
  자유 문자열**(예: `"tabsrv:something"` 형태로 추정) — 즉 **스키마 자체는 실제 명령어
  이름(필터를 의미하는 정확한 문자열이 뭔지)을 전혀 규정하지 않음**. → **필터/하이라이트
  액션을 실제로 어떻게 표현하는지는 스키마만으로는 알 수 없고, 반드시 실제 Tableau가 저장한
  파일로 확인해야 하는 영역**으로 재확인됨 (§0-1의 "의미 검증 불가" 항목에 해당)
- 대안으로 `<edit-parameter-action>`이 있음 — "선택 시 매개변수 값을 바꾼다"는 액션이 별도로
  존재. 우리 HTML 목업의 "카드 클릭 → 필터"는 어쩌면 **필터 액션이 아니라 매개변수 액션 +
  매개변수를 참조하는 계산식(IF [Parameter]="전체" ...)** 조합으로 구현하는 게 더 명확할 수도
  있음 — 시드 파일로 두 가지 접근 다 확인해볼 가치 있음 (질문거리로 남김)

---

## 10. 우리 프로젝트 매핑 체크리스트 (진행 중)

`대시보드 요구사항.md` 페이지별 컴포넌트를 Tableau 구현 방식으로 매핑 (⚠️ 초안, 시드 파일
확보 후 구체화):

| HTML 기획안 요소 | Tableau 구현 방식(가설) | 확인 필요 사항 |
|---|---|---|
| KPI 카드 5개 (기간별) | 계산식으로 기간 플래그 만든 뒤 텍스트 표(Text Table) 워크시트, 또는 각 기간별 워크시트 5개 | 어느 쪽이 유지보수에 유리한지 |
| 월별 트렌드 콤보차트(막대+라인) | 이중 축(Dual Axis) 워크시트 | 이중 축 XML 구조 |
| 국가별 버블맵 | Tableau 내장 지도(Map mark) + 버블 크기 인코딩 | 국가 코드→위경도 자동 인식 여부 |
| 생산공장×결함유형 히트맵 | 텍스트 표 + 색상 인코딩(연속형) | 연속형 색상 팔레트 XML |
| 소형멀티플 5개 | 개별 워크시트 5개를 대시보드에 배치, 또는 트렐리스(패널) 차트 | 트렐리스 가능 여부 |
| 클릭 → 필터링 인터랙션 | 필터 액션 (§9) | 필드 매핑 |
| 공통 필터(고객사/공장/카테고리/기간) | 컨텍스트 필터 또는 매개변수 + 계산식, 대시보드 전체에 적용 | 여러 대시보드 탭에 필터 하나로 공유하는 방법 |
| 시작일/종료일 날짜 필터 | 상대 날짜 필터 vs 날짜 범위 필터 vs 매개변수 2개 | 방식 결정 필요 |

---

## 11. 알려진 리스크 (PPT2 교훈 + 공식 스키마로 재확인된 부분)

- Tableau 관계형 데이터 원본을 XML로 직접 구현하면 로드 자체가 실패한 사례 있음 → 데이터
  원본 연결부(§2)는 특히 신중하게, 실제 파일로 검증 후 진행. **공식 스키마도 이 부분을
  의도적으로 검증하지 않음이 확인됨** (§0-1, §2) — 이건 우리 프로젝트만의 문제가 아니라
  Tableau가 공식적으로 "이 영역은 스키마로 못 잡는다"고 인정한 것.
- 다수 워크시트 기능(집계식 필드 배치, 필터 구현, 카드/히트맵 형식 차트)은 Claude가 XML을
  직접 처음부터 작성해 처리하기 어려웠음 → 최소 구성부터 단계적 검증
- **액션(§9)도 같은 범주**: `<action>`의 뼈대는 스키마로 확인됐지만, 필터 액션을 실제로
  어떤 `command` 문자열로 표현하는지는 스키마에 없음 → 실제 파일 필수
- 돌파구: 사용자가 Tableau UI에서 직접 만들고 저장한 파일을 Claude가 읽고 그대로 복제
- **새로 추가된 안전장치**: 이제 `.twb`를 작성할 때마다 공식 XSD로 **구문 검증을 자동화**할
  수 있음 (§0-1) — "Tableau에서 열리는지"는 여전히 사용자 확인이 필요하지만, 최소한 "XML
  구조 자체가 깨졌는지"는 Claude가 스스로 미리 걸러낼 수 있게 됨. 즉 PPT2 시절보다 실패
  확률을 한 단계 낮출 수 있는 도구가 생김.

---

## 12. TODO — 시드 파일 확보 시 갱신할 항목

**공식 스키마로 이미 해결됨**:
- [x] §3 컬럼 속성 전체 목록 및 datatype/role/type enum
- [x] §4 calculation class enum, formula가 검증 대상이 아니라는 사실
- [x] §5 매개변수 hasconnection/param-domain-type/members/range 구조
- [x] §8 zone 속성 목록, type-v2 enum 20종

**1차 실물 테스트(2025.3 실제 오류)로 확정됨** (§1-1, 2026.2 XSD보다 우선):
- [x] §1 `version='18.1'`이 2025.3에서 허용됨 확인
- [x] §1 workbook 최상위 필수 순서: `document-format-change-manifest`(필수) →
      `preferences` → `style`(필수) → `datasources` → `worksheets` → `windows`
- [x] §1 `<explain-data>`는 2025.3에 없는 엘리먼트 — 절대 넣지 말 것
- [x] §6 `<worksheet>`엔 `<table>` 뒤에 아무 것도 못 옴 (`simple-id` 같은 것 금지)
- [x] §2/§6 CSV 연결·컬럼·워크시트 rows/cols 구조는 1차 오류 목록에 없었음 (잠정 통과)

**아직 미해결 — 다음 테스트에서 확인 필요**:
- [ ] `<document-format-change-manifest/>`, `<style/>`를 빈 태그로 둬도 되는지, 아니면
      내부에 뭔가 있어야 하는지 (2차 테스트에서 확인 예정)
- [ ] 데이터가 실제로 로드되는지 (XML 구문 통과 ≠ CSV 연결 성공) — §2 여전히 리스크
- [ ] 워크시트에 막대그래프가 실제로 그려지는지 (rows/cols 접미사 규칙이 맞았는지)
- [ ] §8 `is-pixels` 기본값 및 2025.3 실제 좌표 스케일 — 대시보드 만들 때 확인
- [ ] §9 필터/하이라이트 액션의 정확한 `command` 문자열 — 액션 만들 때 확인
- [ ] §9 매개변수 액션(`edit-parameter-action`) vs 전통적 필터 액션 중 적합한 것

---

## 13. 확인된 Enum(허용값) 전체 목록 🔷

공식 XSD(`twb_2026.2.0.xsd`)에서 직접 추출한, 우리 프로젝트와 관련된 enum 값 전체입니다.
이 값들 **밖의 문자열을 쓰면 구문 오류**입니다.

| Enum | 값 |
|---|---|
| `FieldRole-ST` (컬럼 role) | `dimension`, `measure`, `unknown` |
| `FieldType-ST` (컬럼 type) | `nominal`, `ordinal`, `quantitative`, `unknown` |
| `DataType-ST` (컬럼 datatype) | `integer`, `real`, `string`, `datetime`, `date`, `boolean`, `tuple`, `spatial`, `table`, `unknown` |
| `DomainType-ST` (매개변수 param-domain-type) | `any`, `list`, `range` |
| `DataSource-CalculationType-ST` (calculation class) | `tableau`, `passthrough`, `bin`, `categorical-bin` |
| `PivotStrategy-ST` | `key`, `alias` |
| `AliasType-ST` | `alias-key`, `alias-key-name`, `alias-key-medname`, `alias-key-longname`, `alias-name`, `alias-name-key`, `alias-medname`, `alias-medname-key`, `alias-longname`, `alias-longname-key` |
| `ZoneType-ST` (zone type-v2) | `invalid`, `visual`, `color`, `shape`, `size`, `map`, `highlighter`, `filter`, `currpage`, `empty`, `title`, `text`, `bitmap`, `web`, `add-in`, `dashboard-object`, `paramctrl`, `flipboard`, `flipboard-nav`, `layout-basic`, `layout-flow` |
| `ActivationMethod-ST` (액션 activation type) | `explicit`, `on-select`, `on-hover` |
| `SourceType-ST` (액션 source type) | `all`, `datasource`, `sheet` |
| `UrlActionType-ST` | `default-zone-or-browser`, `browser`, `specific-zone` |
| `AggType-ST` (집계 방식) | ⚠️ 스키마상 제약 없는 자유 문자열 (`Sum`, `Count` 등 관례적 값 사용 추정) |

※ `StyleElement-ST`(색상/서식 대상 — `mark`, `axis`, `dashboard`, `quick-filter` 등 57개)처럼
목록이 매우 긴 것은 필요할 때 XSD에서 다시 추출. `.twb` 작성 중 특정 enum이 궁금하면
언제든 요청 — 이 저장소를 다시 열어 정확한 값을 뽑아드릴 수 있음.

---

## 14. 참고 링크

**공식 XSD 스키마**:
- [tableau/tableau-document-schemas (GitHub)](https://github.com/tableau/tableau-document-schemas)
- [twb_2026.2.0.xsd (raw)](https://raw.githubusercontent.com/tableau/tableau-document-schemas/main/schemas/2026_2/twb_2026.2.0.xsd)
- [twb_2026.1.0.xsd (raw)](https://raw.githubusercontent.com/tableau/tableau-document-schemas/main/schemas/2026_1/twb_2026.1.0.xsd)

**공식 사용자 문서**:
- [계산된 필드 만들기](https://help.tableau.com/current/pro/desktop/ko-kr/calculations_calculatedfields_formulas.htm)
- [계산된 필드 작업 팁](https://help.tableau.com/current/pro/desktop/ko-kr/calculations_calculatedfields_tips.htm)
- [계산 서식 지정(연산자)](https://help.tableau.com/current/pro/desktop/ko-kr/functions_operators.htm)
- [집계 함수](https://help.tableau.com/current/pro/desktop/ko-kr/calculations_calculatedfields_aggregate_create.htm)
- [매개 변수 만들기](https://help.tableau.com/current/pro/desktop/ko-kr/parameters_create.htm)
- [필터 액션](https://help.tableau.com/current/pro/desktop/ko-kr/actions_filter.htm)
- [Tableau 도움말 홈](https://help.tableau.com/current/pro/desktop/ko-kr/default.htm)
