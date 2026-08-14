# Tableau 구현 가이드 (학습 노트)

> **이 문서의 성격**: `.twb` 파일을 실제로 만들기 위해 필요한 지식을 계속 채워나가는 **성장형 문서**입니다.
> `.twb` 생성은 잠시 미루고, 먼저 이 문서에 지식을 쌓습니다. Claude Code로 핸드오프하기 전 최종
> 레퍼런스가 됩니다.
>
> **신뢰도 표기 규칙** (항목마다 표시):
> - ✅ **검증됨** — 실제 Tableau 2025.3이 저장한 `.twb`/`.twbx` 파일로 확인한 내용
> - 📘 **공식문서 기반** — help.tableau.com에서 확인한 UI/개념 설명 (신뢰도 높음, XML 스키마는 아님)
> - ⚠️ **미검증(추정)** — 일반적인 Tableau XML 지식 기반 추정. 실제 파일로 검증 전까지는
>   **그대로 믿지 말 것.** (PPT2 사례: "기억에 의존한 추측은 반복해서 틀렸다")
>
> **목표 환경**: Tableau Desktop **2025.3** (build `20253.26.0109.0333`), 데이터 소스
> `data/sl_corporation_quality_claims.csv`

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

## 1. `.twb` 파일 최상위 구조 개요 ⚠️

`.twb`는 XML 파일입니다 (`.twbx`는 데이터까지 압축한 패키지 버전 — 우리는 `.twb` + 별도 CSV
연결을 사용). 최상위 골격은 대략 다음과 같이 구성됩니다 (⚠️ 정확한 속성명·중첩 구조는 버전마다
달라 실제 파일 확인 필요):

```xml
<?xml version='1.0' encoding='utf-8' ?>
<workbook source-build='2025.3.x' source-platform='win' version='18.1'
          xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest> ... </document-format-change-manifest>
  <preferences> ... </preferences>
  <datasources>
    <datasource name='Parameters' hasconnection='false'> ... </datasource>
    <datasource caption='sl_corporation_quality_claims' inline='true'
                name='federated.xxxxxxxxxxxxxxxxxxxxx' version='18.1'>
      ... (연결 정보 + 컬럼 정의) ...
    </datasource>
  </datasources>
  <worksheets>
    <worksheet name='...'> ... </worksheet>
  </worksheets>
  <dashboards>
    <dashboard name='...'> ... </dashboard>
  </dashboards>
  <windows>
    <window class='worksheet' name='...'> ... </window>
    <window class='dashboard' name='...'> ... </window>
  </windows>
  <thumbnails> ... </thumbnails>
</workbook>
```

핵심 포인트:
- `version` 속성은 **내부 XML 스키마 버전**이며 Tableau 제품 버전(2025.3)과 1:1로 같은 숫자가
  아님 (예: 18.1 계열이 최근 여러 제품 버전에 걸쳐 쓰임). ⚠️ 2025.3의 정확한 값은 시드 파일로 확인.
- 데이터소스는 `<datasources>` 안에 최소 1개(우리 CSV) + 매개변수를 쓸 경우 이름이 정확히
  `Parameters`인 특수 데이터소스가 추가로 생김.
- `<windows>`는 "지금 열려 있는 탭"을 기록하는 UI 상태값에 가까움 — 워크시트/대시보드 자체
  정의는 `<worksheets>`/`<dashboards>`에 있음.

---

## 2. 데이터 소스 연결 (CSV) ⚠️

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

## 3. 컬럼 정의 & 데이터 타입 매핑 ⚠️

데이터소스 XML 안에서 각 컬럼은 `<column>` 엘리먼트로 다시 한 번 선언되며 (metadata-record와
별개로), 이 선언이 실제 필드 패널에 보이는 타입/역할을 결정하는 것으로 보입니다:

```xml
<column caption="Customer" datatype="string" name="[customer]" role="dimension" type="nominal" />
<column caption="Claim Amount Usd" datatype="real" name="[claim_amount_usd]" role="measure" type="quantitative" />
<column caption="Occurrence Date" datatype="date" name="[occurrence_date]" role="dimension" type="ordinal" />
```

`Data Dictionary.md` 24개 컬럼을 Tableau 타입으로 매핑하면 (⚠️ datatype/role/type 조합은
실제 파일로 검증 필요):

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

### 4-2. XML 구조 ⚠️
```xml
<column caption="Lead Time To Receive" datatype="integer" name="[Calculation_1234567890123]"
        role="measure" type="quantitative">
  <calculation class="tableau" formula="DATEDIFF(&apos;day&apos;, [occurrence_date], [claim_received_date])" />
</column>
```
`name`이 `[Calculation_<임의의 긴 숫자>]` 형태의 내부 ID이고 `caption`이 화면에 보이는
이름이라는 점이 핵심 — 즉 계산식을 여러 개 추가할 때 ID 충돌 없는 고유값을 만들어야 함
(⚠️ 이 숫자의 생성 규칙은 불명 — 타임스탬프 기반으로 추정).

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

## 5. 매개변수 (Parameters) 📘 (공식문서 확인됨) + ⚠️(XML)

### 5-1. 개념
데이터 패널 드롭다운 > 매개 변수 만들기 → 이름 / 데이터 유형(정수·실수·문자열·날짜·날짜시간) /
기본값 / 표시 형식 설정. **허용값 방식 3가지**:

| 방식 | 설명 |
|---|---|
| 전체(All) | 텍스트 필드처럼 자유 입력 |
| 목록(List) | 선택 가능한 값들을 사전 지정 (필드 멤버에서 가져오기 가능) |
| 범위(Range) | 최소/최대/단계 크기 지정 |

문자열 매개변수는 **범위를 지원하지 않음**.

### 5-2. XML 구조 ⚠️
매개변수는 이름이 정확히 `Parameters`인 특수 데이터소스(`hasconnection='false'`) 안에
컬럼으로 저장되는 것으로 보임:

```xml
<datasource name='Parameters' hasconnection='false'>
  <column caption="최근 N개월" datatype="integer" name="[Parameter 1]"
          param-domain-type="range" role="measure" type="quantitative" value="12">
    <range max="60" min="1" granularity="1" />
  </column>
</datasource>
```

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
  접미사 규칙은 실제 파일로 확인 필요

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

## 8. 대시보드 레이아웃 (Zones) ⚠️

```xml
<dashboard name="1. 종합 요약">
  <size sizing-mode="automatic" />
  <zones>
    <zone h="100000" id="2" type-v2="layout-basic" w="100000" x="0" y="0">
      <zone h="20000" id="3" name="1_KPI" w="100000" x="0" y="0" />
      <zone h="80000" id="4" name="1_Trend" w="100000" x="0" y="20000" />
    </zone>
  </zones>
</dashboard>
```

`zones`는 좌표 기반 타일링 레이아웃(w/h/x/y가 0~100000 스케일의 상대 좌표)으로 보임 —
`대시보드 요구사항.md`에서 정의한 페이지별 컴포넌트 배치(KPI 카드 5개 / 트렌드 / 지도+랭킹
등)를 이 zone 좌표로 변환해야 함. ⚠️ floating 레이아웃, 컨테이너(수평/수직 레이아웃 컨테이너)
문법은 아직 조사 전.

---

## 9. 액션 (Filter / Highlight / URL Actions)

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

### 9-2. XML 구조 ⚠️
```xml
<actions>
  <action caption="카테고리 필터 액션">
    <filter>
      <source><worksheet name="2_소형멀티플" /></source>
      <target><worksheets><worksheet name="2_히트맵" /><worksheet name="2_랭킹" /></worksheets></target>
      <field-map><map source-field="[part_category]" target-field="[part_category]" /></field-map>
      <options activation="selection" clear-on-select-none="true" />
    </filter>
  </action>
</actions>
```

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

## 11. 알려진 리스크 (PPT2 교훈 요약)

- Tableau 관계형 데이터 원본을 XML로 직접 구현하면 로드 자체가 실패한 사례 있음 → 데이터
  원본 연결부(§2)는 특히 신중하게, 실제 파일로 검증 후 진행
- 다수 워크시트 기능(집계식 필드 배치, 필터 구현, 카드/히트맵 형식 차트)은 Claude가 XML을
  직접 처음부터 작성해 처리하기 어려웠음 → 최소 구성부터 단계적 검증
- 돌파구: 사용자가 Tableau UI에서 직접 만들고 저장한 파일을 Claude가 읽고 그대로 복제

---

## 12. TODO — 시드 파일 확보 시 갱신할 항목

- [ ] §1 `version`/`source-build` 정확한 값
- [ ] §2 CSV 연결의 정확한 XML (특히 경로 처리 방식)
- [ ] §2 날짜 컬럼 자동 인식 여부, `claim_confirmed_date` 빈값→Null 처리 확인
- [ ] §3 컬럼별 datatype/role/type 실제 값
- [ ] §4 계산식 XML의 `name` ID 생성 규칙
- [ ] §6 `rows`/`cols` 필드 접미사 표기 규칙 (`:nk`, `:qk` 등)
- [ ] §8 zone 좌표 체계, floating/container 문법
- [ ] §9 액션 XML 구조 검증

---

## 13. 참고 링크 (공식 문서)

- [계산된 필드 만들기](https://help.tableau.com/current/pro/desktop/ko-kr/calculations_calculatedfields_formulas.htm)
- [계산된 필드 작업 팁](https://help.tableau.com/current/pro/desktop/ko-kr/calculations_calculatedfields_tips.htm)
- [계산 서식 지정(연산자)](https://help.tableau.com/current/pro/desktop/ko-kr/functions_operators.htm)
- [집계 함수](https://help.tableau.com/current/pro/desktop/ko-kr/calculations_calculatedfields_aggregate_create.htm)
- [매개 변수 만들기](https://help.tableau.com/current/pro/desktop/ko-kr/parameters_create.htm)
- [필터 액션](https://help.tableau.com/current/pro/desktop/ko-kr/actions_filter.htm)
- [Tableau 도움말 홈](https://help.tableau.com/current/pro/desktop/ko-kr/default.htm)
