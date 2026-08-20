# -*- coding: utf-8 -*-
"""
SL_Corporation_Quality_Claims.twb 생성 스크립트 (Tableau Desktop 2025.3 대상).

'대시보드 기획안.html'의 3페이지 대시보드를 실제 Tableau .twb XML로 재현한다. 데이터소스(24개
원본 컬럼 + CSV 연결) + 계산 필드(리드타임/사이클타임/KPI 카드 등) + 워크시트 25개 + 대시보드
3개 + 상단 필터 박스(차원 필터 + 날짜 매개변수) + 기획안과 동일한 색상 팔레트로 구성된다.

아래는 이 파일의 각 섹션이 실제로 어떤 Tableau 기능을 만들어내는지 한눈에 보기 위한 지도.
섹션 번호는 파일 안의 "# N)" 주석과 대응한다.

  1)   COLUMNS / REMOTE_TYPE / build_metadata_records   -> 데이터소스: CSV 연결 + 원본 필드 24개
  1-1) PARAM_DEFS / build_parameters_datasource          -> 상단 필터 박스의 매개변수(Parameters
                                                             데이터소스, 시작일/종료일)
  2)   CALC_FIELDS / KPI_PERIODS / cond_calc / *_expr    -> 계산된 필드: 리드타임, 사이클타임,
       함수들 / KPI_CARD_DEPS                               상태 플래그, KPI 카드 5개(제목/부제/
                                                             건수/증감률/금액/증감률 문자열)
  3)   col_instance / instance_xml / field_ref /         -> rows/cols/filter/encodings가 참조하는
       datasource_dependencies                              column-instance 배선 (qualified 이름,
                                                             derivation='None'|'Sum'|...|'User')
  3-1) FILTER_DIMS / common_filter_block                 -> 대시보드 상단 필터 박스: 고객사/생산
                                                             공장/부품카테고리 차원 필터 + 날짜범위
                                                             필터(매개변수 기반 계산 필드)
  3-2) NAVY 등 색상 상수 / worksheet_style_block /       -> 기획안과 동일한 색상 적용 + 워크시트
       datasource_color_style_block                         제목·머리글 숨김 (mark-color 단색,
                                                             claim_status/severity 카테고리 팔레트)
  4)   ws_simple_bar / ws_heatmap / ws_trend /           -> 워크시트 종류별 빌더(막대, 히트맵,
       ws_small_multiple / ws_kpi_text / ws_map              트렌드, 소형멀티플, KPI 텍스트 카드, 지도)
  5)   add(...) 호출들                                   -> 워크시트 25개 실제 등록(필드/색상 지정)
  6)   PAGE_LAYOUTS / render_layout / build_dashboard    -> 대시보드 화면 배치: 세로/가로 컨테이너
                                                             트리 -> 절대좌표 zone(type-v2=
                                                             'layout-basic') + Phone 디바이스 레이아웃
  7)   CARDS_BLOCK / window_blocks                       -> 워크시트/대시보드 "창(window)" 상태
                                                             (활성 zone, viewpoints, 전체 보기 줌)
  8)   WORKBOOK 최종 조립                                -> 전체 XML 합치기 + 2026.2 XSD 참고 검증
                                                             (2025.3 전용 항목은 알려진 차이로 무시)
"""
import os
import uuid
import tempfile
import urllib.request

TMP = tempfile.gettempdir()
XSD_URL = "https://raw.githubusercontent.com/tableau/tableau-document-schemas/main/schemas/2026_2/twb_2026.2.0.xsd"
XSD_PATH = os.path.join(TMP, "twb_2026.2.0.xsd")
XSD_PATCHED_PATH = os.path.join(TMP, "twb_2026.2.0_patched.xsd")
USER_STUB_PATH = os.path.join(TMP, "user_stub.xsd")
XML_STUB_PATH = os.path.join(TMP, "xml.xsd")

CSV_PATH_ABS = r"c:\Users\milvus-Tom\.claude\Project\AI-Tableau\data\sl_corporation_quality_claims.csv"
CSV_DIR_ABS = CSV_PATH_ABS.replace("\\", "/").rsplit("/", 1)[0]
CSV_FILENAME = "sl_corporation_quality_claims.csv"

# ------------------------------------------------------------------
# 1) 원본 컬럼 (Data Dictionary.md 그대로)
# ------------------------------------------------------------------
COLUMNS = [
    ("claim_id", "string", "dimension", "nominal"),
    ("customer", "string", "dimension", "nominal"),
    ("customer_plant", "string", "dimension", "nominal"),
    ("claim_country", "string", "dimension", "nominal"),
    ("claim_language", "string", "dimension", "nominal"),
    ("claim_description", "string", "dimension", "nominal"),
    ("production_plant", "string", "dimension", "nominal"),
    ("production_country", "string", "dimension", "nominal"),
    ("part_category", "string", "dimension", "nominal"),
    ("part_name_ko", "string", "dimension", "nominal"),
    ("part_name_en", "string", "dimension", "nominal"),
    ("part_number", "string", "dimension", "nominal"),
    ("production_date", "date", "dimension", "ordinal"),
    ("delivery_date", "date", "dimension", "ordinal"),
    ("occurrence_date", "date", "dimension", "ordinal"),
    ("claim_received_date", "date", "dimension", "ordinal"),
    ("claim_confirmed_date", "date", "dimension", "ordinal"),
    ("claim_status", "string", "dimension", "nominal"),
    ("defect_type_ko", "string", "dimension", "nominal"),
    ("defect_type_en", "string", "dimension", "nominal"),
    ("severity", "string", "dimension", "nominal"),
    ("claim_quantity", "integer", "measure", "quantitative"),
    ("unit_price_usd", "real", "measure", "quantitative"),
    ("claim_amount_usd", "real", "measure", "quantitative"),
]
REMOTE_TYPE = {"string": "129", "date": "133", "integer": "20", "real": "5"}

# ------------------------------------------------------------------
# 1-1) 매개변수 (상단 필터 박스의 시작일/종료일) - 별도의 'Parameters' 데이터소스로 존재하는
# 것이 실제 Tableau .twb의 표준 구조. Tableau 공식 샘플 워크북(tableau/TabMon,
# TabMon.twb)에서 실물 확인: hasconnection='false' inline='true' version='<workbook버전>'
# 속성이 전부 있어야 하고(inline='true' 누락이 "매개변수 자체가 생성 안 됨" 버그의 원인이었음),
# 다른 데이터소스의 계산식에서 매개변수를 쓰려면 반드시 [Parameters].[Parameter 1]처럼
# 데이터소스 접두사를 붙여야 하며(같은 샘플의 실제 계산식으로 확인:
# "[Parameters].[Parameter 2] = ..."), 그 계산식을 쓰는 워크시트의 <view>는
#   1) <datasources>에 <datasource name='Parameters' /> 항목을 추가로 넣고
#   2) <datasource-dependencies datasource='Parameters'>에 쓰는 매개변수 column을
#      (Parameters 데이터소스 자체와 동일한 전체 정의로) 별도 선언해야 함.
# ------------------------------------------------------------------
PARAM_DEFS = [
    ("Parameter 1", "Start Date", "date", "#2023-01-01#"),
    ("Parameter 2", "End Date", "date", "#2025-12-31#"),
]


def build_parameters_datasource():
    cols = []
    for name, caption, dtype, default in PARAM_DEFS:
        cols.append(f"""      <column caption='{caption}' datatype='{dtype}' name='[{name}]' param-domain-type='any' role='measure' type='quantitative' value='{default}'>
        <calculation class='tableau' formula='{default}' />
      </column>""")
    cols_xml = "\n".join(cols)
    return f"""    <datasource caption='Parameters' hasconnection='false' inline='true' name='Parameters' version='18.1'>
      <aliases enabled='yes' />
{cols_xml}
    </datasource>"""


def build_parameters_dependency_block():
    """매개변수를 쓰는 계산식이 있는 워크시트라면 어디든 그대로 삽입할 datasource-dependencies
    블록. 위 build_parameters_datasource()와 동일한 column 정의를 그대로 반복해야 함
    (TabMon.twb 실물 예시에서 확인된 패턴 - column-instance는 필요 없음, column 선언만)."""
    cols = []
    for name, caption, dtype, default in PARAM_DEFS:
        cols.append(f"""            <column caption='{caption}' datatype='{dtype}' name='[{name}]' param-domain-type='any' role='measure' type='quantitative' value='{default}'>
              <calculation class='tableau' formula='{default}' />
            </column>""")
    cols_xml = "\n".join(cols)
    return f"""          <datasource-dependencies datasource='Parameters'>
{cols_xml}
          </datasource-dependencies>"""


PARAMETERS_DS_REF = "            <datasource name='Parameters' />"
PARAMETERS_DEP_BLOCK = build_parameters_dependency_block()


# ------------------------------------------------------------------
# 2) 계산된 필드 6개 (대시보드 요구사항.md §전역 계산 필드 + Occurrence Month 보조 필드)
# ------------------------------------------------------------------
CALC_FIELDS = [
    # (내부이름, 캡션, datatype, role, type, formula)
    ("LeadTimeToReceive", "Lead Time To Receive", "integer", "measure", "quantitative",
     "DATEDIFF('day', [occurrence_date], [claim_received_date])"),
    ("LeadTimeToConfirm", "Lead Time To Confirm", "integer", "measure", "quantitative",
     "DATEDIFF('day', [claim_received_date], [claim_confirmed_date])"),
    ("TotalCycleTime", "Total Cycle Time", "integer", "measure", "quantitative",
     "DATEDIFF('day', [occurrence_date], [claim_confirmed_date])"),
    ("IsOpen", "Is Open", "boolean", "dimension", "nominal",
     '[claim_status] = "접수" OR [claim_status] = "조사중"'),
    ("IsConfirmedLiable", "Is Confirmed Liable", "boolean", "dimension", "nominal",
     '[claim_status] = "확정" OR [claim_status] = "보상완료"'),
    ("OccurrenceMonth", "Occurrence Month", "date", "dimension", "ordinal",
     "DATETRUNC('month', [occurrence_date])"),
    # 상단 필터 박스의 시작일/종료일 매개변수(Parameter 1/2)를 워크시트 필터로 쓰기 위한
    # 불리언 계산식. <filter class='categorical'> + groupfilter function='member' member='true'
    # 패턴은 2_SM_* 워크시트에서 이미 검증된(실물 로드 성공) 구조라 이 필터도 그대로 재사용.
    ("DateRangeFilter", "Date Range Filter", "boolean", "dimension", "nominal",
     "[occurrence_date] >= [Parameters].[Parameter 1] AND [occurrence_date] <= [Parameters].[Parameter 2]"),
]

# 1페이지 KPI 카드 5개(최근1/3/6/12개월 + 전체)용 조건부 계산식. 실제 <filter> XML은 아직
# 검증 안 된 영역이라(대시보드 요구사항.md 리스크) 우회 - IF로 기간 밖 값을 NULL 처리한 뒤
# SUM하면 <filter> 없이도 기간별 KPI를 만들 수 있음.
# 각 기간마다: 이번 기간 count/amount + 전년동기 count/amount(증감률용) + 카드 전체를
# 하나의 여러 줄 문자열로 합친 "Card" 계산식(제목/부제/건수/증감률/금액/증감률)까지 생성.
KPI_PERIODS = [
    ("Last1M", "2025-12-01", "2025-12-31", "2024-12-01", "2024-12-31", "최근 1개월", "2025.12"),
    ("Last3M", "2025-10-01", "2025-12-31", "2024-10-01", "2024-12-31", "최근 3개월", "2025.10~12"),
    ("Last6M", "2025-07-01", "2025-12-31", "2024-07-01", "2024-12-31", "최근 6개월", "2025.07~12"),
    ("Last12M", "2025-01-01", "2025-12-31", "2024-01-01", "2024-12-31", "최근 12개월", "2025.01~12"),
]


def cond_calc(start, end):
    return f"[occurrence_date] >= #{start}# AND [occurrence_date] <= #{end}#"


def usd_fmt_expr(sum_expr):
    """$238.3K / $1.00M 처럼 크기에 따라 K·M 단위를 자동으로 바꾸는 Tableau 수식 조각."""
    return (f'IIF({sum_expr} >= 1000000, "$" + STR(ROUND({sum_expr}/1000000,2)) + "M", '
            f'"$" + STR(ROUND({sum_expr}/1000,1)) + "K")')


def pct_badge_expr(cur_expr, prev_expr):
    """▲ 12.3% / ▼ 4.5% 형태의 전기간 대비 증감률 배지 수식 조각."""
    pct = f'ROUND(ABS({cur_expr} - {prev_expr}) / {prev_expr} * 100, 1)'
    arrow = f'IIF({cur_expr} >= {prev_expr}, "▲", "▼")'
    return f'{arrow} + " " + STR({pct}) + "%"'


for pname, start, end, pstart, pend, label, sublabel in KPI_PERIODS:
    CALC_FIELDS.append((f"KPI{pname}Amount", f"KPI {pname} Amount", "real", "measure", "quantitative",
                         f"IF {cond_calc(start, end)} THEN [claim_amount_usd] END"))
    CALC_FIELDS.append((f"KPI{pname}Count", f"KPI {pname} Count", "integer", "measure", "quantitative",
                         f"IF {cond_calc(start, end)} THEN 1 END"))
    CALC_FIELDS.append((f"KPI{pname}PrevAmount", f"KPI {pname} Prev Amount", "real", "measure", "quantitative",
                         f"IF {cond_calc(pstart, pend)} THEN [claim_amount_usd] END"))
    CALC_FIELDS.append((f"KPI{pname}PrevCount", f"KPI {pname} Prev Count", "integer", "measure", "quantitative",
                         f"IF {cond_calc(pstart, pend)} THEN 1 END"))

    cnt = f"SUM([Calculation_KPI{pname}Count])"
    pcnt = f"SUM([Calculation_KPI{pname}PrevCount])"
    amt = f"SUM([Calculation_KPI{pname}Amount])"
    pamt = f"SUM([Calculation_KPI{pname}PrevAmount])"
    card_formula = (
        f'"{label}" + CHAR(10) + "{sublabel} · 전년동기比" + CHAR(10) + CHAR(10) + '
        f'STR({cnt}) + "건" + CHAR(10) + {pct_badge_expr(cnt, pcnt)} + CHAR(10) + CHAR(10) + '
        f'{usd_fmt_expr(amt)} + CHAR(10) + {pct_badge_expr(amt, pamt)}'
    )
    CALC_FIELDS.append((f"KPI{pname}Card", f"KPI {pname} Card", "string", "measure", "nominal", card_formula))

_all_amt = "SUM([claim_amount_usd])"
_all_card_formula = (
    '"전체(3개년)" + CHAR(10) + "2023.01~2025.12" + CHAR(10) + CHAR(10) + '
    'STR(COUNT([claim_id])) + "건" + CHAR(10) + CHAR(10) + ' + usd_fmt_expr(_all_amt)
)
CALC_FIELDS.append(("KPIAllCard", "KPI All Card", "string", "measure", "nominal", _all_card_formula))

# 각 KPI Card 필드가 자기 수식 안에서 SUM()으로 "참조만" 하고 어떤 shelf에도 직접 올리지 않는
# 계산 필드들. 실제로 마크에 이 Card 필드를 올렸을 때 "계산에 오류 있음"(빨간 파란색 필드
# 표시)이 났던 원인으로 확인됨 - 워크시트의 datasource-dependencies에 이 하위 필드들의
# <column> 선언이 전혀 없었음(Card 필드 자기 자신만 선언돼 있었음). Tableau는 워크시트 뷰가
# 실제로 의존하는 모든 필드(수식으로만 참조하는 것 포함)를 그 뷰의 dependencies에 나열해야
# 제대로 평가하는 것으로 확인 - column-instance는 필요 없고 base <column> 선언만 있으면 됨.
KPI_CARD_DEPS = {
    f"KPI{pname}Card": [f"KPI{pname}Count", f"KPI{pname}PrevCount", f"KPI{pname}Amount", f"KPI{pname}PrevAmount"]
    for pname, *_ in KPI_PERIODS
}
KPI_CARD_DEPS["KPIAllCard"] = ["claim_id", "claim_amount_usd"]

# KPI Card 필드들은 그 자체가 이미 SUM()/COUNT()를 품은 "완성된 집계" 계산식이라, 별도 집계 없이
# 그대로 shelf(Text 마크)에 올라간다. 사용자가 Tableau UI에서 이 필드를 뺐다가 다시 넣어서 저장한
# 실물 파일을 diff해서 확인: 이 경우 column-instance의 derivation이 'None'(접두사 'none')이
# 아니라 'User'(접두사 'usr')여야 함 - 그동안 'None'으로 잘못 선언했던 게 마크가 계속 빨간
# 오류로 표시됐던 진짜 원인. (반대로 DateRangeFilter처럼 집계를 전혀 안 쓰는 계산식은 'None'이
# 맞고, 실제로 그쪽은 처음부터 정상 동작했음.)
SELF_AGGREGATING_CALC_REFS = {f"Calculation_{k}" for k in KPI_CARD_DEPS}

# 필드 레지스트리: name -> (datatype, role, type)  (raw + calc 통합)
FIELD_TYPES = {name: (dtype, role, ftype) for name, dtype, role, ftype in COLUMNS}
for internal, caption, dtype, role, ftype, formula in CALC_FIELDS:
    FIELD_TYPES[f"Calculation_{internal}"] = (dtype, role, ftype)
# claim_country가 지리적 역할로 인식되면서 Tableau가 자동 생성하는 위경도 필드 (실물 확인됨 - 필드 패널 스크린샷)
FIELD_TYPES["Latitude (generated)"] = ("real", "measure", "quantitative")
FIELD_TYPES["Longitude (generated)"] = ("real", "measure", "quantitative")

CALC_CAPTION = {f"Calculation_{internal}": caption for internal, caption, *_ in CALC_FIELDS}


def caption_of(name):
    if name in CALC_CAPTION:
        return CALC_CAPTION[name]
    return " ".join(w.capitalize() for w in name.split("_"))


def rand_id(prefix, n=20):
    return prefix + "." + uuid.uuid4().hex[:n]


DS_NAME = rand_id("federated")
CONN_NAME = rand_id("textscan")
TABLE_REF = "[%s#csv]" % CSV_FILENAME.replace(".csv", "")


def build_metadata_records():
    parts = []
    for i, (name, dtype, role, ftype) in enumerate(COLUMNS, start=1):
        parts.append(f"""        <metadata-record class='column'>
          <remote-name>{name}</remote-name>
          <remote-type>{REMOTE_TYPE[dtype]}</remote-type>
          <local-name>[{name}]</local-name>
          <parent-name>{TABLE_REF}</parent-name>
          <remote-alias>{name}</remote-alias>
          <ordinal>{i}</ordinal>
          <family>{CSV_FILENAME}</family>
          <local-type>{dtype}</local-type>
          <aggregation>{'Count' if role == 'dimension' else 'Sum'}</aggregation>
          <contains-null>true</contains-null>
        </metadata-record>""")
    return "\n".join(parts)


def build_base_columns():
    parts = []
    for name, dtype, role, ftype in COLUMNS:
        parts.append(
            f"    <column caption='{caption_of(name)}' datatype='{dtype}' "
            f"name='[{name}]' role='{role}' type='{ftype}' />"
        )
    for internal, caption, dtype, role, ftype, formula in CALC_FIELDS:
        f_escaped = formula.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;").replace('"', "&quot;")
        parts.append(
            f"    <column caption='{caption}' datatype='{dtype}' name='[Calculation_{internal}]' "
            f"role='{role}' type='{ftype}'>\n"
            f"      <calculation class='tableau' formula='{f_escaped}' />\n"
            f"    </column>"
        )
    return "\n".join(parts)


# ------------------------------------------------------------------
# 3) column-instance 헬퍼 (1차 실패 원인으로 추정되는 부분 - 이번엔 명시적으로 선언)
# ------------------------------------------------------------------
def field_ref(name):
    """계산식이면 [Calculation_xxx], 원본 컬럼이면 [name] 그대로."""
    for internal, caption, dtype, role, ftype, formula in CALC_FIELDS:
        if name == internal:
            return f"Calculation_{internal}"
    return name


def col_instance(name, derivation, alias=None):
    """rows/cols/encodings에서 쓸 column-instance 이름/타입/베이스컬럼 정보를 묶어서 반환.

    중요: rows/cols/encodings/filter의 column 속성은 데이터소스 이름까지 포함한
    "[federated.xxx].[instance]" 형태(qualified)로 써야 함 - 1차 시도 이후 리팩토링
    과정에서 이 접두사가 빠졌던 게 2차 실패("필드가 없습니다")의 주된 원인으로 추정됨.
    <column-instance name='...'> 선언 자체의 name 속성은 접두사 없는 bare 형태 사용.
    """
    ref = field_ref(name)
    dtype, role, ftype = FIELD_TYPES[ref]
    # 집계(Sum/Count/Avg 등)를 적용하면 원본 필드 타입과 무관하게 결과는 항상 quantitative
    if derivation == "None":
        out_ftype = ftype
    else:
        out_ftype = "quantitative"
    is_measure = out_ftype == "quantitative"
    suffix = "qk" if is_measure else "nk"
    # SELF_AGGREGATING_CALC_REFS(KPI Card류)는 이미 그 자체로 완성된 집계식이라, 추가 집계 없이
    # 그대로 shelf에 올릴 때 derivation이 'None'이 아니라 'User'(접두사 'usr')여야 함 - 실물
    # 파일 diff로 확인.
    if derivation == "None" and ref in SELF_AGGREGATING_CALC_REFS:
        derivation_label, prefix = "User", "usr"
    else:
        derivation_label, prefix = derivation, derivation.lower()
    inst_name = f"[{prefix}:{ref}:{suffix}]"
    qualified = f"[{DS_NAME}].{inst_name}"
    return {
        "ref": ref, "dtype": dtype, "role": role, "ftype": out_ftype,
        "inst_name": inst_name, "qualified": qualified,
        "derivation": derivation_label, "is_measure": is_measure,
        "caption": alias or caption_of(ref),
    }


def base_column_xml(ref):
    dtype, role, ftype = FIELD_TYPES[ref]
    return f"            <column caption='{caption_of(ref)}' datatype='{dtype}' name='[{ref}]' role='{role}' type='{ftype}' />"


def instance_xml(ci):
    return (f"            <column-instance column='[{ci['ref']}]' derivation='{ci['derivation']}' "
            f"name='{ci['inst_name']}' pivot='key' type='{ci['ftype']}' />")


WORKSHEET_CIS = {}  # worksheet name -> cis 리스트 (대시보드의 datasource-dependencies 합치는 데 재사용)


def datasource_dependencies(cis, sheet_name=None, extra_base_refs=None):
    """cis: col_instance() 결과 리스트. 중복 없이 base column + column-instance 블록 생성.
    sheet_name을 주면 WORKSHEET_CIS에 등록해서, 이 워크시트를 담는 대시보드가 자기 자신의
    datasource-dependencies를 만들 때 재사용할 수 있게 함 (2805CF18 원인으로 추정되는,
    대시보드에 datasource-dependencies가 비어있던 문제 대응).
    extra_base_refs: 어떤 shelf에도 직접 올라가지 않고 다른 계산식 안에서 수식으로만
    참조되는 필드(예: KPI Card가 SUM()으로 참조하는 하위 Count/Amount 계산식들) - column-instance
    없이 base <column> 선언만 추가한다."""
    if sheet_name is not None:
        WORKSHEET_CIS[sheet_name] = cis
    seen_base, seen_inst = set(), set()
    base_parts, inst_parts = [], []
    for ci in cis:
        if ci["ref"] not in seen_base:
            seen_base.add(ci["ref"])
            base_parts.append(base_column_xml(ci["ref"]))
        if ci["inst_name"] not in seen_inst:
            seen_inst.add(ci["inst_name"])
            inst_parts.append(instance_xml(ci))
    for ref in (extra_base_refs or []):
        if ref not in seen_base:
            seen_base.add(ref)
            base_parts.append(base_column_xml(ref))
    return "\n".join(base_parts + inst_parts)


# ------------------------------------------------------------------
# 3-1) 공통 필터(상단 필터 박스): 고객사/생산공장/부품 카테고리 차원 필터 + 매개변수 기반
# 날짜범위 필터. 사용자가 Tableau UI에서 직접 만들어 저장한 '필터 예시' 워크시트의 실제 구조
# (level-members/all + slices)를 그대로 재사용 - 기본값은 "전체 선택" 상태라 필터를 추가해도
# 당장 데이터가 줄어들진 않지만, 대시보드에서 카드를 노출하면 바로 동작하는 상태로 준비됨.
# ------------------------------------------------------------------
FILTER_DIMS = ["customer", "production_plant", "part_category"]


def common_filter_block(exclude=None):
    exclude = exclude or set()
    cis = []
    filter_parts = []
    slice_parts = []
    for dim in FILTER_DIMS:
        if dim in exclude:
            continue
        ci = col_instance(dim, "None")
        cis.append(ci)
        filter_parts.append(
            f"          <filter class='categorical' column='{ci['qualified']}'>\n"
            f"            <groupfilter function='level-members' level='{ci['inst_name']}' user:ui-enumeration='all' user:ui-marker='enumerate' />\n"
            f"          </filter>"
        )
        slice_parts.append(f"            <column>{ci['qualified']}</column>")
    dci = col_instance("DateRangeFilter", "None")
    cis.append(dci)
    filter_parts.append(
        f"          <filter class='categorical' column='{dci['qualified']}'>\n"
        f"            <groupfilter function='member' level='{dci['inst_name']}' member='true' />\n"
        f"          </filter>"
    )
    slice_parts.append(f"            <column>{dci['qualified']}</column>")
    filters_xml = "\n".join(filter_parts)
    slices_xml = "          <slices>\n" + "\n".join(slice_parts) + "\n          </slices>"
    return cis, filters_xml, slices_xml


# ------------------------------------------------------------------
# 3-2) 대시보드 기획안.html에 실제로 쓰인 색상값 그대로 이식 (JS 상수 STATUS_COLOR/SEV_COLOR,
# drawRankBars 기본색 #1f4e79, 트렌드 라인 #16324f, 리드타임 히스토그램 색 등을 그대로 읽어옴).
# ------------------------------------------------------------------
NAVY = "#16324f"
NAVY_2 = "#1f4e79"
GOOD = "#2a7f62"
GRAY_BAR = "#c8d3e0"
AMBER = "#d98c1f"
MUTED = "#7c8494"
BORDER_GRAY = "#e2e6ec"
STATUS_COLOR_MAP = {"접수": "#d98c1f", "조사중": "#e2a53a", "확정": "#1f4e79", "기각": "#9aa4b2", "보상완료": "#2a7f62"}
SEVERITY_COLOR_MAP = {"Critical": "#c0392b", "Major": "#d98c1f", "Minor": "#7a8699"}


def worksheet_style_block(mark_color=None, hide_label_fields=None):
    """모든 워크시트 공통으로 행/열 필드 머리글을 숨기고, 필요하면 단색 mark-color를 적용.
    (카테고리별 커스텀 팔레트는 워크시트가 아니라 데이터소스 레벨 스타일로 옮김 - 아래
    datasource_color_style_block() 및 그 주석 참고.)

    머리글 숨김은 두 겹으로 건다: element='header' + scope=rows/cols(전역 토글, 예전부터 있었지만
    실제로는 "Occurrence Month"/"Customer" 같은 필드명 캡션이 계속 남아있는 게 확인됨)과,
    실물 파일(참고 자료/태블로 예시.twbx, worksheet 'Bunker Price_Header')에서 확인된 진짜
    메커니즘인 element='label' + field='[qualified]' + attr='display'=false(필드별 개별 토글)를
    hide_label_fields로 받은 각 필드마다 추가. 후자가 실제로 이 문제를 해결하는 부분."""
    rules = [
        "          <style-rule element='header'>\n"
        "            <format attr='display' scope='rows' value='false' />\n"
        "            <format attr='display' scope='cols' value='false' />\n"
        "          </style-rule>"
    ]
    if hide_label_fields:
        label_formats = "\n".join(
            f"            <format attr='display' field='{f}' value='false' />" for f in hide_label_fields
        )
        rules.append(f"          <style-rule element='label'>\n{label_formats}\n          </style-rule>")
    if mark_color:
        rules.append(
            "          <style-rule element='mark'>\n"
            f"            <format attr='mark-color' value='{mark_color}' />\n"
            "          </style-rule>"
        )
    return "        <style>\n" + "\n".join(rules) + "\n        </style>"


def datasource_color_style_block():
    """카테고리 값별 커스텀 색상(예: severity Critical=빨강)은 워크시트가 아니라 데이터소스의
    <style><style-rule element='mark'><encoding attr='color' field='[none:필드:nk]'
    type='palette'><map to='#hex'><bucket>&quot;값&quot;</bucket></map>...</encoding></style-rule>
    구조로 선언되는 것을 실제 공개 .twb 예시(berkayalan/Tableau-Tutorials, Section2.twb의
    Region 필드 색상 지정부)로 확인 - 대시보드 기획안.html의 STATUS_COLOR/SEV_COLOR 값을 그대로
    이식. field= 값은 워크시트 shelf 참조와 달리 데이터소스 접두사 없는 bare 형태."""
    def one_rule(field_name, color_map):
        cci = col_instance(field_name, "None")
        maps = "\n".join(
            f"            <map to='{hexval}'>\n              <bucket>&quot;{value}&quot;</bucket>\n            </map>"
            for value, hexval in color_map.items()
        )
        return (
            "        <style-rule element='mark'>\n"
            f"          <encoding attr='color' field='{cci['inst_name']}' type='palette'>\n"
            f"{maps}\n"
            "          </encoding>\n"
            "        </style-rule>"
        )
    rules = [one_rule("claim_status", STATUS_COLOR_MAP), one_rule("severity", SEVERITY_COLOR_MAP)]
    return "      <style>\n" + "\n".join(rules) + "\n      </style>"


# ------------------------------------------------------------------
# 4) 워크시트 빌더
# ------------------------------------------------------------------
def ws_simple_bar(name, dim, meas, meas_agg="Sum", color_dim=None, mark="Bar", mark_color=None):
    """행=차원, 열=집계측정값 가로 막대 (가장 흔한 패턴)."""
    dci = col_instance(dim, "None")
    mci = col_instance(meas, meas_agg)
    cis = [dci, mci]
    color_xml = ""
    if color_dim:
        cci = col_instance(color_dim, "None")
        cis.append(cci)
        color_xml = f"\n              <color column='{cci['qualified']}' />"
    filt_cis, filters_xml, slices_xml = common_filter_block()
    cis.extend(filt_cis)
    deps = datasource_dependencies(cis, sheet_name=name)
    style_block = worksheet_style_block(mark_color=mark_color, hide_label_fields=[dci['qualified']])
    return f"""    <worksheet name='{name}'>
      <table>
        <view>
          <datasources>
            <datasource caption='sl_corporation_quality_claims' name='{DS_NAME}' />
{PARAMETERS_DS_REF}
          </datasources>
          <datasource-dependencies datasource='{DS_NAME}'>
{deps}
          </datasource-dependencies>
{PARAMETERS_DEP_BLOCK}
{filters_xml}
{slices_xml}
          <aggregation value='true' />
        </view>
{style_block}
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='{mark}' />
            <encodings>{color_xml}
            </encodings>
          </pane>
        </panes>
        <rows>{dci['qualified']}</rows>
        <cols>{mci['qualified']}</cols>
      </table>
    </worksheet>"""


def ws_heatmap(name, dim_row, dim_col, meas, meas_agg="Count"):
    rci = col_instance(dim_row, "None")
    cci = col_instance(dim_col, "None")
    mci = col_instance(meas, meas_agg)
    filt_cis, filters_xml, slices_xml = common_filter_block()
    deps = datasource_dependencies([rci, cci, mci] + filt_cis, sheet_name=name)
    style_block = worksheet_style_block(hide_label_fields=[rci['qualified'], cci['qualified']])
    return f"""    <worksheet name='{name}'>
      <table>
        <view>
          <datasources>
            <datasource caption='sl_corporation_quality_claims' name='{DS_NAME}' />
{PARAMETERS_DS_REF}
          </datasources>
          <datasource-dependencies datasource='{DS_NAME}'>
{deps}
          </datasource-dependencies>
{PARAMETERS_DEP_BLOCK}
{filters_xml}
{slices_xml}
          <aggregation value='true' />
        </view>
{style_block}
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Square' />
            <encodings>
              <color column='{mci['qualified']}' />
            </encodings>
          </pane>
        </panes>
        <rows>{rci['qualified']}</rows>
        <cols>{cci['qualified']}</cols>
      </table>
    </worksheet>"""


def ws_trend(name, dim, meas, meas_agg="Sum", mark="Line", mark_color=None):
    dci = col_instance(dim, "None")
    mci = col_instance(meas, meas_agg)
    filt_cis, filters_xml, slices_xml = common_filter_block()
    deps = datasource_dependencies([dci, mci] + filt_cis, sheet_name=name)
    style_block = worksheet_style_block(mark_color=mark_color, hide_label_fields=[dci['qualified']])
    return f"""    <worksheet name='{name}'>
      <table>
        <view>
          <datasources>
            <datasource caption='sl_corporation_quality_claims' name='{DS_NAME}' />
{PARAMETERS_DS_REF}
          </datasources>
          <datasource-dependencies datasource='{DS_NAME}'>
{deps}
          </datasource-dependencies>
{PARAMETERS_DEP_BLOCK}
{filters_xml}
{slices_xml}
          <aggregation value='true' />
        </view>
{style_block}
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='{mark}' />
            <encodings />
          </pane>
        </panes>
        <rows>{mci['qualified']}</rows>
        <cols>{dci['qualified']}</cols>
      </table>
    </worksheet>"""


def ws_dual_axis(name, dim, meas_bar, meas_bar_agg, meas_line, meas_line_agg, bar_color, line_color):
    """막대(왼쪽 축) + 라인(오른쪽 축) 이중축 콤보 차트. 실물 파일(참고 자료/이중축 예시.twbx,
    "막대 라인 이중축" 워크시트)에서 확인된 구조 그대로: <rows>에 두 측정값을
    '(A + B)' 형태로 괄호 묶어 결합하고, <panes>에 기본 pane 1개(mark='Automatic') +
    각 측정값마다 y-axis-name으로 자신을 가리키는 pane(id='1'=A, id='2'=B, 각각 다른
    mark class)을 추가. 실물 예시는 색상을 Measure Names 인코딩으로 나눴지만, 우리는
    막대/라인이 애초에 서로 다른 pane이라 각 pane 자체의 style-rule에 고정 mark-color를
    거는 것만으로 충분(더 단순하고 검증된 mark-color 패턴 재사용)."""
    dci = col_instance(dim, "None")
    bar_ci = col_instance(meas_bar, meas_bar_agg)
    line_ci = col_instance(meas_line, meas_line_agg)
    filt_cis, filters_xml, slices_xml = common_filter_block()
    deps = datasource_dependencies([dci, bar_ci, line_ci] + filt_cis, sheet_name=name)
    style_block = worksheet_style_block(hide_label_fields=[dci['qualified']])
    return f"""    <worksheet name='{name}'>
      <table>
        <view>
          <datasources>
            <datasource caption='sl_corporation_quality_claims' name='{DS_NAME}' />
{PARAMETERS_DS_REF}
          </datasources>
          <datasource-dependencies datasource='{DS_NAME}'>
{deps}
          </datasource-dependencies>
{PARAMETERS_DEP_BLOCK}
{filters_xml}
{slices_xml}
          <aggregation value='true' />
        </view>
{style_block}
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Automatic' />
            <encodings />
          </pane>
          <pane id='1' selection-relaxation-option='selection-relaxation-allow' y-axis-name='{line_ci['qualified']}'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Line' />
            <encodings />
            <style>
              <style-rule element='mark'>
                <format attr='mark-color' value='{line_color}' />
              </style-rule>
            </style>
          </pane>
          <pane id='2' selection-relaxation-option='selection-relaxation-allow' y-axis-name='{bar_ci['qualified']}'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Bar' />
            <encodings />
            <style>
              <style-rule element='mark'>
                <format attr='mark-color' value='{bar_color}' />
              </style-rule>
            </style>
          </pane>
        </panes>
        <rows>({line_ci['qualified']} + {bar_ci['qualified']})</rows>
        <cols>{dci['qualified']}</cols>
      </table>
    </worksheet>"""


def ws_small_multiple(name, category_value_caption, part_category_literal, meas="claim_amount_usd", mark_color=None):
    """part_category를 필터로 고정한 뒤 월별 트렌드 하나만 보여주는 카드 (5개 반복 생성)."""
    dci = col_instance("OccurrenceMonth", "None")
    mci = col_instance(meas, "Sum")
    fci = col_instance("part_category", "None")
    # part_category는 이 워크시트 자체가 이미 특정 값으로 고정한 필터라서, 공통 필터 박스의
    # "전체 선택" part_category 필터는 제외(같은 필드에 두 개의 <filter>가 생기는 충돌 방지).
    filt_cis, filters_xml, slices_xml = common_filter_block(exclude={"part_category"})
    deps = datasource_dependencies([dci, mci, fci] + filt_cis, sheet_name=name)
    style_block = worksheet_style_block(mark_color=mark_color, hide_label_fields=[dci['qualified']])
    return f"""    <worksheet name='{name}'>
      <table>
        <view>
          <datasources>
            <datasource caption='sl_corporation_quality_claims' name='{DS_NAME}' />
{PARAMETERS_DS_REF}
          </datasources>
          <datasource-dependencies datasource='{DS_NAME}'>
{deps}
          </datasource-dependencies>
{PARAMETERS_DEP_BLOCK}
          <filter class='categorical' column='{fci['qualified']}'>
            <groupfilter function='member' level='{fci['inst_name']}' member='&quot;{part_category_literal}&quot;' />
          </filter>
{filters_xml}
{slices_xml}
          <aggregation value='true' />
        </view>
{style_block}
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Line' />
            <encodings />
          </pane>
        </panes>
        <rows>{mci['qualified']}</rows>
        <cols>{dci['qualified']}</cols>
      </table>
    </worksheet>"""


def ws_kpi_text(name, card_field, mark_color=None):
    """기간별 KPI 카드: 제목/부제/건수/증감률/금액/증감률을 전부 담은 여러 줄 문자열
    계산식(card_field, 예: KPILast1MCard) 하나를 Text 마크 라벨로 표시. 행/열 모두 비워서
    "큰 텍스트 블록" 형태로 렌더링(축 없음)."""
    fci = col_instance(card_field, "None")
    filt_cis, filters_xml, slices_xml = common_filter_block()
    # 카드 필드가 SUM()으로 참조만 하는 하위 계산식(Count/PrevCount/Amount/PrevAmount 등)도
    # 이 워크시트의 datasource-dependencies에 명시적으로 선언 - 실제 오류 원인이었음
    # (KPI_CARD_DEPS 선언부 주석 참고).
    extra_refs = [field_ref(r) for r in KPI_CARD_DEPS.get(card_field, [])]
    deps = datasource_dependencies(filt_cis + [fci], sheet_name=name, extra_base_refs=extra_refs)
    style_block = worksheet_style_block(mark_color=mark_color)
    return f"""    <worksheet name='{name}'>
      <table>
        <view>
          <datasources>
            <datasource caption='sl_corporation_quality_claims' name='{DS_NAME}' />
{PARAMETERS_DS_REF}
          </datasources>
          <datasource-dependencies datasource='{DS_NAME}'>
{deps}
          </datasource-dependencies>
{PARAMETERS_DEP_BLOCK}
{filters_xml}
{slices_xml}
          <aggregation value='true' />
        </view>
{style_block}
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Text' />
            <encodings>
              <text column='{fci['qualified']}' />
            </encodings>
          </pane>
        </panes>
        <rows></rows>
        <cols></cols>
      </table>
    </worksheet>"""


def ws_map(name):
    """claim_country 기준 버블맵 - Tableau 자동 생성 위경도 필드 사용 (리스크 큰 시도)."""
    lat = col_instance("Latitude (generated)", "None")
    lon = col_instance("Longitude (generated)", "None")
    ctry = col_instance("claim_country", "None")
    mci = col_instance("claim_amount_usd", "Sum")
    filt_cis, filters_xml, slices_xml = common_filter_block()
    deps = datasource_dependencies([lat, lon, ctry, mci] + filt_cis, sheet_name=name)
    style_block = worksheet_style_block(mark_color=NAVY_2)
    return f"""    <worksheet name='{name}'>
      <table>
        <view>
          <datasources>
            <datasource caption='sl_corporation_quality_claims' name='{DS_NAME}' />
{PARAMETERS_DS_REF}
          </datasources>
          <datasource-dependencies datasource='{DS_NAME}'>
{deps}
          </datasource-dependencies>
{PARAMETERS_DEP_BLOCK}
{filters_xml}
{slices_xml}
          <aggregation value='true' />
        </view>
{style_block}
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Circle' />
            <encodings>
              <size column='{mci['qualified']}' />
              <level column='{ctry['qualified']}' />
            </encodings>
          </pane>
        </panes>
        <rows>{lat['qualified']}</rows>
        <cols>{lon['qualified']}</cols>
      </table>
    </worksheet>"""


# ------------------------------------------------------------------
# 5) 17개 워크시트 조립
# ------------------------------------------------------------------
CATEGORIES = ["Lamp Systems", "Mirror Systems", "Chassis Systems", "Front End Module", "Electrification"]

worksheet_blocks = []
worksheet_names = []


def add(name, xml):
    # <WindowsPersistSimpleIdentifiers/> 매니페스트 플래그를 켜면서 <worksheet>도
    # (((layout-options?)|(repository-location?)),table,simple-id) - 즉 simple-id가
    # 필수가 됨(2025-08-20 실물 오류로 확인). </table> 뒤에 자동으로 붙여줌 - ws_* 빌더
    # 함수를 전부 고칠 필요 없이 등록 시점에 일괄 주입.
    guid = "{" + str(uuid.uuid4()).upper() + "}"
    assert xml.rstrip().endswith("</worksheet>"), f"unexpected worksheet XML tail for {name}"
    xml = xml.rstrip()[: -len("</worksheet>")] + f"      <simple-id uuid='{guid}' />\n    </worksheet>"
    worksheet_blocks.append(xml)
    worksheet_names.append(name)


# Page 1
add("1_KPI_1M", ws_kpi_text("1_KPI_1M", "KPILast1MCard"))
add("1_KPI_3M", ws_kpi_text("1_KPI_3M", "KPILast3MCard"))
add("1_KPI_6M", ws_kpi_text("1_KPI_6M", "KPILast6MCard"))
add("1_KPI_12M", ws_kpi_text("1_KPI_12M", "KPILast12MCard"))
add("1_KPI_All", ws_kpi_text("1_KPI_All", "KPIAllCard", mark_color="#ffffff"))
add("1_Trend", ws_dual_axis("1_Trend", "OccurrenceMonth", "claim_id", "Count", "claim_amount_usd", "Sum",
                             bar_color=GRAY_BAR, line_color=NAVY))
add("1_Map", ws_map("1_Map"))
add("1_Top5_Customer", ws_simple_bar("1_Top5_Customer", "customer", "claim_amount_usd", mark_color=NAVY_2))
add("1_Top5_Defect", ws_simple_bar("1_Top5_Defect", "defect_type_en", "claim_amount_usd", mark_color=NAVY_2))
add("1_Top5_Plant", ws_simple_bar("1_Top5_Plant", "production_plant", "claim_amount_usd", mark_color=NAVY_2))

# Page 2
for i, cat in enumerate(CATEGORIES, start=1):
    add(f"2_SM_{i}", ws_small_multiple(f"2_SM_{i}", cat, cat, mark_color=NAVY_2))
add("2_Heatmap", ws_heatmap("2_Heatmap", "production_plant", "defect_type_en", "claim_id", "Count"))
add("2_Rank_Category", ws_simple_bar("2_Rank_Category", "part_category", "claim_amount_usd", mark_color=NAVY_2))
add("2_Rank_DefectCount", ws_simple_bar("2_Rank_DefectCount", "defect_type_en", "claim_id", "Count", mark_color=NAVY_2))
add("2_CustComposition", ws_simple_bar("2_CustComposition", "customer", "claim_amount_usd", mark_color=NAVY_2))

# Page 3
add("3_Status", ws_simple_bar("3_Status", "claim_status", "claim_id", "Count", color_dim="claim_status"))
add("3_Cycle_Customer", ws_simple_bar("3_Cycle_Customer", "customer", "TotalCycleTime", "Avg", mark_color=NAVY_2))
add("3_Cycle_Plant", ws_simple_bar("3_Cycle_Plant", "production_plant", "TotalCycleTime", "Avg", mark_color=NAVY_2))
add("3_Severity", ws_simple_bar("3_Severity", "severity", "claim_amount_usd", "Sum", color_dim="severity"))
add("3_LeadTime_Receive", ws_simple_bar("3_LeadTime_Receive", "claim_status", "LeadTimeToReceive", "Avg", mark_color=NAVY_2))
add("3_LeadTime_Confirm", ws_simple_bar("3_LeadTime_Confirm", "claim_status", "LeadTimeToConfirm", "Avg", mark_color=GOOD))

WORKSHEETS_XML = "\n".join(worksheet_blocks)

# ------------------------------------------------------------------
# 6) 대시보드 3개 - 대시보드 기획안.html의 그리드 구조를 가로/세로 컨테이너 트리로 재현.
#    ('leaf', 워크시트이름) | ('vert'|'horz', [자식 노드...])
# ------------------------------------------------------------------
def W(weight, node):
    """render_layout의 vert/horz 자식에 상대적 비중(weight)을 지정. 기본 비중은 1."""
    return ("w", weight, node)


TITLE_COLOR = "#16324F"


def captioned(caption, node, cap_h=1, body_h=9):
    """차트 위에 작은 캡션(예: '월별 클레임 건수·금액 추이')을 붙인다 - 기획안의
    .card h2 캡션 문구 재현. 워크시트 자체 제목(show-title)은 계속 숨긴 채, 별도
    text zone으로 캡션만 보여줌."""
    return ("vert", [W(cap_h, ("text", caption, 13, TITLE_COLOR)), W(body_h, node)])


def title_row(text):
    """맨 위 제목 줄 - 기획안처럼 제목(왼쪽) + '기준일' 표시(오른쪽)만. 필터 박스는 별도
    행(filter_row)으로 그 아래에 배치 - 기획안 레이아웃이 제목 줄과 필터 줄을 분리해서
    보여주는 것과 동일한 구조로 맞춤."""
    return ("horz", [
        W(20, ("text", text, 22, TITLE_COLOR)),
        W(6, ("text", "기준일 2025-12-31", 11, "#7c8494")),
    ])


def filter_row(owner_ws):
    """필터 박스: 고객사/생산공장/부품카테고리 드롭다운 + 시작일/종료일. 필터 드롭다운은
    실물 파일(참고 자료/필터 예시.twbx, "Reset filter sample")에서 확인된 type='filter'
    mode='checkdropdown' 구조를 그대로 재현(아래 filterctrl 분기 참고).
    owner_ws: 이 필터를 "소유"하는 워크시트 이름 - 그 대시보드에 실제로 배치된 워크시트여야
    하고(필터 zone의 name= 속성), 이미 모든 워크시트가 동일한 customer/production_plant/
    part_category 필터를 갖고 있어(common_filter_block) 어떤 워크시트를 골라도 됨."""
    return ("horz", [
        W(6, ("filterctrl", "customer", owner_ws)),
        W(6, ("filterctrl", "production_plant", owner_ws)),
        W(6, ("filterctrl", "part_category", owner_ws)),
        W(4, ("paramctrl", "Parameter 1", "시작일", "datetime")),
        W(4, ("paramctrl", "Parameter 2", "종료일", "datetime")),
        W(10, ("empty",)),
    ])


PAGE_CONTENT = {
    "1. 종합 요약": ("vert", [
        W(2, title_row("종합 요약")),
        W(2, filter_row("1_KPI_1M")),
        W(5, ("horz", [
            ("leaf", "1_KPI_1M", "card"), ("leaf", "1_KPI_3M", "card"), ("leaf", "1_KPI_6M", "card"),
            ("leaf", "1_KPI_12M", "card"), ("leaf", "1_KPI_All", "card-hl"),
        ], {"fixed_size": 200})),
        W(7, captioned("월별 클레임 건수 · 금액 추이", ("leaf", "1_Trend"))),
        W(12, ("horz", [
            captioned("국가별 클레임 규모", ("leaf", "1_Map")),
            ("vert", [
                captioned("Top 5 고객사", ("leaf", "1_Top5_Customer")),
                captioned("Top 5 불량 유형", ("leaf", "1_Top5_Defect")),
                captioned("Top 5 생산공장", ("leaf", "1_Top5_Plant")),
            ]),
        ])),
    ]),
    "2. 원인 드릴다운": ("vert", [
        W(2, title_row("원인 드릴다운")),
        W(2, filter_row("2_SM_1")),
        W(8, ("horz", [captioned(cat, ("leaf", f"2_SM_{i}")) for i, cat in enumerate(CATEGORIES, start=1)])),
        W(12, ("horz", [
            captioned("생산공장 × 불량유형 히트맵", ("leaf", "2_Heatmap")),
            ("vert", [
                captioned("부품 카테고리별 순위", ("leaf", "2_Rank_Category")),
                captioned("불량유형별 건수", ("leaf", "2_Rank_DefectCount")),
            ]),
        ])),
        W(6, captioned("고객사별 구성비", ("leaf", "2_CustComposition"))),
    ]),
    "3. 리드타임 효율": ("vert", [
        W(2, title_row("리드타임 · 효율")),
        W(2, filter_row("3_Status")),
        W(9, ("horz", [captioned("클레임 상태", ("leaf", "3_Status")), captioned("심각도", ("leaf", "3_Severity"))])),
        W(9, ("horz", [
            captioned("리드타임 분포 — 발생 → 접수", ("leaf", "3_LeadTime_Receive")),
            captioned("리드타임 분포 — 접수 → 확정", ("leaf", "3_LeadTime_Confirm")),
        ])),
        W(9, ("horz", [
            captioned("고객사별 평균 처리기간", ("leaf", "3_Cycle_Customer")),
            captioned("생산공장별 평균 처리기간", ("leaf", "3_Cycle_Plant")),
        ])),
    ]),
}

DASH_NAMES = list(PAGE_CONTENT.keys())

# 탐색 버튼의 window-id가 가리킬 대상 - 대시보드 window의 <simple-id>.
DASHBOARD_WINDOW_GUIDS = {name: "{" + str(uuid.uuid4()).upper() + "}" for name in DASH_NAMES}


def gnb_column(current_dash):
    """좌측 메뉴바(GNB) - 대시보드 기획안.html의 .sidebar 구조·폰트·색상 그대로 재현:
    (로고 대신) "SL Corporation" 워드마크 + "Quality Claims Dashboard" 태그라인(.brand-tagline과
    동일하게 남색-2/굵게) + 대시보드별 이동 항목(활성/비활성 대비) + 하단 캡션(.sidebar-mini-foot).
    대시보드마다 자기 자신 항목은 강조(활성) 스타일, 나머지는 비활성 스타일."""
    brand = W(6, ("text", "SL Corporation", 15, TITLE_COLOR))
    tagline = W(4, ("text", "Quality Claims Dashboard", 10, NAVY_2))
    spacer = W(2, ("empty",))
    buttons = [W(3, ("navbutton", n, n == current_dash)) for n in DASH_NAMES]
    filler = W(65, ("empty",))
    footer = W(4, ("text", "Synthetic Data", 9, MUTED))
    return ("vert", [brand, tagline, spacer] + buttons + [filler, footer])


# 최종 페이지 트리 = 좌측 GNB(고정 폭) + 기존 콘텐츠(나머지 폭). 실물 파일의 "GNB 컬럼 +
# 콘텐츠 컬럼" horz 2분할 패턴을 그대로 따름(GNB w=13750 즉 폭의 13.75% - 실물 예시와 동일 비율).
PAGE_LAYOUTS = {
    name: ("horz", [W(1375, gnb_column(name)), W(8625, tree)])
    for name, tree in PAGE_CONTENT.items()
}


def flatten_leaves(node):
    if node[0] == "leaf":
        return [node[1]]
    if node[0] in ("text", "paramctrl", "navbutton", "empty", "filterctrl"):
        return []
    out = []
    for child in node[1]:
        child = child[2] if child[0] == "w" else child  # ("w", weight, node) 래퍼 해제
        out.extend(flatten_leaves(child))
    return out


PAGE_SHEETS = {name: flatten_leaves(tree) for name, tree in PAGE_LAYOUTS.items()}

_zone_id_counter = [10]


def next_zone_id():
    _zone_id_counter[0] += 1
    return _zone_id_counter[0]


ZONE_STYLE = """            <zone-style>
              <format attr='border-color' value='#000000' />
              <format attr='border-style' value='none' />
              <format attr='border-width' value='0' />
              <format attr='margin' value='4' />
            </zone-style>"""

OUTER_ZONE_STYLE = """          <zone-style>
            <format attr='border-color' value='#000000' />
            <format attr='border-style' value='none' />
            <format attr='border-width' value='0' />
            <format attr='margin' value='8' />
          </zone-style>"""

# 기획안 .kpi-card CSS(흰 배경, 옅은 테두리, 둥근 모서리) 재현 - KPI 카드 5개 중 "전체(3개년)"만
# .kpi-card.hl(진한 남색 배경)로 강조되는 것도 그대로.
CARD_ZONE_STYLE = """            <zone-style>
              <format attr='border-color' value='#e2e6ec' />
              <format attr='border-style' value='solid' />
              <format attr='border-width' value='1' />
              <format attr='margin' value='4' />
              <format attr='background-color' value='#ffffff' />
            </zone-style>"""

CARD_HIGHLIGHT_ZONE_STYLE = """            <zone-style>
              <format attr='border-color' value='#16324f' />
              <format attr='border-style' value='solid' />
              <format attr='border-width' value='1' />
              <format attr='margin' value='4' />
              <format attr='background-color' value='#16324f' />
            </zone-style>"""

LEAF_ZONE_STYLES = {"card": CARD_ZONE_STYLE, "card-hl": CARD_HIGHLIGHT_ZONE_STYLE}


DASHBOARD_ZONE_IDS = {}  # dash_name -> {sheet_name: zone_id} (desktop 기준) - window의 active/viewpoints에 재사용

DASH_W, DASH_H = 1400, 2400  # <size maxwidth='1400' maxheight='2400'> - fixed-size(px) 환산 기준

# ------------------------------------------------------------------
# 실제 완료된 PoC 워크북(참고 자료/태블로 예시.twbx, Tableau 2024.2.1로 저장)을 통째로 뜯어서
# 확인한 진짜 구조. 이전까지 이 스크립트가 썼던 여러 가정이 이 실물 대조로 뒤집힘 - 특히:
#
#   - "type-v2='layout-flow'는 h/w 비율을 무시하고 Tableau가 알아서 재계산한다"는 가정이 틀렸음.
#     실제로는 layout-flow 컨테이너 자체나 그 자식 zone에 is-fixed='true' + fixed-size='NNN'
#     (NNN은 0~100000 스케일이 아니라 대시보드 실제 픽셀 크기 기준!)을 붙여야 그 방향(세로 흐름
#     이면 높이, 가로 흐름이면 너비) 크기가 고정된다. is-fixed 없이 h/w만 있으면 Tableau가 내용
#     기준으로 재계산 - 지금까지 겪은 "일부는 찌그러지고 일부는 화면을 다 차지"의 진짜 원인.
#     형제 zone을 "동일한 크기"로 맞추는 것도 is-fixed가 아니라 그냥 동일한 w(또는 h) 값을
#     주는 것만으로 충분 (예: KPI 카드 4개가 전부 w='20000'으로 동일, is-fixed는 카드 개별이
#     아니라 카드들을 담은 행(row) 컨테이너 자체에만 걸려 있었음).
#   - 최상위 wrapper는 여전히 layout-basic(param 없음) -> layout-flow(param='vert') ->
#     layout-flow(param='horz') 순으로 중첩되는 게 실물 패턴 - layout-basic으로 전부 바꾼 지난
#     시도는 방향이 틀렸음(원상복구).
#   - <size>에 sizing-mode='fixed'가 실제로 쓰이고 있었음(이전엔 "sizing-mode 없이"가 맞다고
#     판단했는데, 그건 sizing-mode='automatic' 하나만 실패해봤던 것 - 'fixed'는 별개로 확인됨).
# ------------------------------------------------------------------


def render_layout(node, id_gen, with_style, x, y, w, h, sheet_zone_ids, flow_dir="vert", reuse_ids=None):
    """레이아웃 트리를 실제 zone XML로 재귀 변환.

    좌표 체계는 매 depth마다 0~100000으로 리셋되는 게 아니라, 대시보드 전체 캔버스 기준
    절대 좌표(0~100000)를 계속 이어받는 것으로 실물 파일('대시보드 2')에서 확인됨 - 자식이
    1개뿐인 컨테이너의 자식 zone이 부모와 완전히 동일한 w/h(98400/98000, 100000이 아님)를
    가졌던 것이 근거. 그래서 이 함수는 x/y/w/h를 절대값으로 받아 그대로 자식에게 분배한다.

    flow_dir: 이 zone을 담고 있는 부모 컨테이너의 흐름 방향('vert'|'horz') - is-fixed/fixed-size를
    붙일 때 세로 흐름이면 높이(h), 가로 흐름이면 너비(w)를 픽셀로 환산해 고정한다(참고 자료
    실물 파일에서 확인된 fixed-size 단위 = 대시보드 실제 픽셀, 0~100000 비율이 아님).

    reuse_ids가 주어지면(phone 레이아웃 생성 시) 워크시트 leaf zone의 id를 desktop과
    동일하게 재사용 - 실물 파일에서 확인된 패턴. 컨테이너 zone은 desktop/phone 각자 새 id.
    """
    def fixed_attrs(override_px=None):
        if not with_style:
            return ""
        if override_px is not None:
            px = override_px
        else:
            px = round(h / 100000 * DASH_H) if flow_dir == "vert" else round(w / 100000 * DASH_W)
        return f" fixed-size='{px}' is-fixed='true'"

    kind = node[0]
    if kind == "leaf":
        sn = node[1]
        variant = node[2] if len(node) > 2 else None
        zid = reuse_ids[sn] if reuse_ids else id_gen()
        sheet_zone_ids[sn] = zid
        zone_style_xml = LEAF_ZONE_STYLES.get(variant, ZONE_STYLE)
        style = "\n" + zone_style_xml if with_style else ""
        return f"          <zone{fixed_attrs()} h='{h}' id='{zid}' name='{sn}' show-title='false' w='{w}' x='{x}' y='{y}'>{style}\n          </zone>"

    if kind == "text":
        text, fontsize, color = node[1], node[2], node[3]
        zid = id_gen()
        style = "\n" + ZONE_STYLE if with_style else ""
        return (f"          <zone{fixed_attrs()} h='{h}' id='{zid}' type-v2='text' w='{w}' x='{x}' y='{y}'>\n"
                f"            <formatted-text><run bold='true' fontcolor='{color}' fontsize='{fontsize}'>{text}</run></formatted-text>{style}\n"
                f"          </zone>")

    if kind == "paramctrl":
        # 실물 파일(참고 자료/태블로 예시.twbx)에서 확인된 실제 구조 그대로 재현: mode='datetime'
        # 매개변수 컨트롤 zone. param='[Parameters].[필드이름]', custom-title='true' + formatted-text
        # 로 컨트롤 위에 보이는 라벨(예: '시작일')을 지정.
        param_name, label, mode = node[1], node[2], node[3]
        zid = id_gen()
        return (f"          <zone{fixed_attrs()} custom-title='true' h='{h}' id='{zid}' mode='{mode}' "
                f"param='[Parameters].[{param_name}]' type-v2='paramctrl' w='{w}' x='{x}' y='{y}'>\n"
                f"            <formatted-text>\n              <run>{label}</run>\n            </formatted-text>\n"
                f"            <zone-style>\n"
                f"              <format attr='border-color' value='#000000' />\n"
                f"              <format attr='border-style' value='none' />\n"
                f"              <format attr='border-width' value='0' />\n"
                f"              <format attr='margin' value='0' />\n"
                f"              <format attr='padding-top' value='15' />\n"
                f"            </zone-style>\n"
                f"          </zone>")

    if kind == "filterctrl":
        # 필터 드롭다운(고객사/생산공장/부품카테고리). 실물 파일(참고 자료/필터 예시.twbx,
        # "Reset filter sample")에서 확인된 실제 구조: type-v2='filter' mode='checkdropdown'
        # show-apply='true', name=이 필터를 소유한 워크시트 이름, param=필드의 qualified
        # column-instance. 모든 워크시트가 이미 동일한 필터(전체 선택 상태)를 갖고 있어서
        # 어떤 워크시트를 owner로 지정해도 동일하게 동작함(common_filter_block).
        field_name, owner_ws = node[1], node[2]
        fci = col_instance(field_name, "None")
        zid = id_gen()
        return (f"          <zone{fixed_attrs()} h='{h}' id='{zid}' mode='checkdropdown' name='{owner_ws}' "
                f"param='{fci['qualified']}' show-apply='true' type-v2='filter' w='{w}' x='{x}' y='{y}'>\n"
                f"            <zone-style>\n"
                f"              <format attr='border-color' value='#000000' />\n"
                f"              <format attr='border-style' value='none' />\n"
                f"              <format attr='border-width' value='0' />\n"
                f"              <format attr='margin' value='4' />\n"
                f"            </zone-style>\n"
                f"          </zone>")

    if kind == "empty":
        # GNB 사이드바 하단 여백 채우기용 - 실물 파일의 type-v2='empty' 스페이서 zone과 동일.
        zid = id_gen()
        style = "\n" + ZONE_STYLE if with_style else ""
        return f"          <zone{fixed_attrs()} h='{h}' id='{zid}' type-v2='empty' w='{w}' x='{x}' y='{y}'>{style}\n          </zone>"

    if kind == "navbutton":
        # 실제 원인 확정(2025-08-20): <button>/window <simple-id>가 6번 연속 거부된 진짜 이유는
        # zone 구조가 아니라, 워크북 최상위 <document-format-change-manifest>가 비어 있었기
        # 때문이었음. 사용자가 저장한 실물 파일(완전 재시작 후 정상 로드 확인됨)의 manifest에
        # <BasicButtonObject/><BasicButtonObjectTextSupport/><WindowsPersistSimpleIdentifiers/>
        # 등 기능 플래그가 선언돼 있었고, 이게 로더의 스키마 분기 자체를 바꾸는 것으로 확인 -
        # 이 플래그 없이는 로더가 button-in-zone/window simple-id를 아예 모르는 스키마로
        # 검증하다가 거부했던 것. WORKBOOK 템플릿에 이 manifest를 추가했으니 버튼을 다시 복원.
        # 배경색(활성 #555555 / 비활성 #e6e6e6)도 이번 실물 예시 값 그대로 사용.
        # 기획안 .nav-item / .nav-item.active CSS 그대로: 활성은 남색(#16324f) 배경 + 흰 글씨 +
        # 왼쪽 amber(#d98c1f) 강조선, 비활성은 흰 배경 + 어두운 텍스트(#1c2430). 왼쪽 강조선은
        # zone-style의 border-*-left 속성(StyleAttribute-ST에 border-color-left/border-style-left/
        # border-width-left가 개별로 존재 - 일반 border와 별개로 확인됨)으로 구현.
        target_dash, is_active = node[1], node[2]
        zid = id_gen()
        guid = DASHBOARD_WINDOW_GUIDS[target_dash]
        if is_active:
            fontcolor, bg = "#ffffff", NAVY
            left_border = (
                f"              <format attr='border-color-left' value='{AMBER}' />\n"
                f"              <format attr='border-style-left' value='solid' />\n"
                f"              <format attr='border-width-left' value='3' />\n"
            )
        else:
            fontcolor, bg = "#1c2430", "#ffffff"
            left_border = ""
        return (f"          <zone h='{h}' id='{zid}' type-v2='dashboard-object' w='{w}' x='{x}' y='{y}'>\n"
                f"            <button action='tabdoc:goto-sheet window-id=&quot;{guid}&quot;' button-type='text'>\n"
                f"              <button-visual-state>\n"
                f"                <caption>{target_dash}</caption>\n"
                f"                <button-caption-font-style fontcolor='{fontcolor}' fontname='Tableau Bold' fontsize='12' />\n"
                f"                <format attr='background-color' value='{bg}' />\n"
                f"              </button-visual-state>\n"
                f"            </button>\n"
                f"            <zone-style>\n"
                f"              <format attr='border-color' value='#000000' />\n"
                f"              <format attr='border-style' value='none' />\n"
                f"              <format attr='border-width' value='0' />\n"
                f"{left_border}"
                f"              <format attr='margin' value='4' />\n"
                f"            </zone-style>\n"
                f"          </zone>")

    children = [(_c[2], _c[1]) if _c[0] == "w" else (_c, 1) for _c in node[1]]  # (node, weight)
    total_w = sum(wt for _, wt in children)
    cid = id_gen()
    parts = []
    pos = 0
    if kind == "vert":
        for child, wt in children:
            ch_h = h * wt // total_w
            parts.append(render_layout(child, id_gen, with_style, x, y + pos, w, ch_h, sheet_zone_ids, "vert", reuse_ids))
            pos += ch_h
    else:  # horz
        for child, wt in children:
            ch_w = w * wt // total_w
            parts.append(render_layout(child, id_gen, with_style, x + pos, y, ch_w, h, sheet_zone_ids, "horz", reuse_ids))
            pos += ch_w
    inner_xml = "\n".join(parts)
    style = "\n" + ZONE_STYLE if with_style else ""
    # node에 3번째 요소로 {"fixed_size": N} 같은 override dict가 있으면, 비중 계산 대신
    # 그 픽셀값을 그대로 fixed-size에 사용 (예: KPI 카드 행 높이를 정확히 200px로 고정).
    opts = node[2] if len(node) > 2 and isinstance(node[2], dict) else {}
    return f"""        <zone{fixed_attrs(opts.get("fixed_size"))} h='{h}' id='{cid}' param='{kind}' type-v2='layout-flow' w='{w}' x='{x}' y='{y}'>
{inner_xml}{style}
        </zone>"""


def build_dashboard(dash_name, layout_tree):
    # 실물 확인(Dashboard_Isolation_Test.twb '대시보드 2' + 참고 자료/태블로 예시.twbx의 실제
    # PoC 워크북) + 로드 시점 실제 오류(D2E8DA72)를 합쳐서 확정한 구조:
    #   - <datasources>/<datasource-dependencies>는 대시보드에 아예 없음
    #   - 워크시트를 담는 zone엔 type-v2가 없음, 컨테이너 zone엔 type-v2='layout-flow'
    #     + param='vert'|'horz' + is-fixed/fixed-size로 크기 고정(위 render_layout 주석 참고)
    #   - <size>에 sizing-mode='fixed' 명시(실물 PoC 파일에서 확인)
    #   - zone마다 <zone-style> 서식 블록 포함
    #   - <devicelayouts>에 Phone 레이아웃이 실제 내용(자체 size+zones)으로 채워져 있고,
    #     워크시트 zone은 desktop과 동일 id를 재사용함
    #   - simple-id / enable-sort-zone-taborder / devicelayout의 auto-generated는
    #     로드 시엔 허용되지 않아 전부 제외.
    sheet_zone_ids = {}
    desktop_inner = render_layout(layout_tree, next_zone_id, True, 0, 0, 100000, 100000, sheet_zone_ids)
    outer_id = next_zone_id()
    desktop_zones = f"""        <zone h='100000' id='{outer_id}' type-v2='layout-basic' w='100000' x='0' y='0'>
{desktop_inner}
{OUTER_ZONE_STYLE}
        </zone>"""

    phone_ids_unused = {}
    phone_inner = render_layout(layout_tree, next_zone_id, False, 0, 0, 100000, 100000, phone_ids_unused, reuse_ids=sheet_zone_ids)
    phone_outer_id = next_zone_id()
    phone_zones = f"""        <zone h='100000' id='{phone_outer_id}' type-v2='layout-basic' w='100000' x='0' y='0'>
{phone_inner}
        </zone>"""

    DASHBOARD_ZONE_IDS[dash_name] = sheet_zone_ids
    # <dashboard>도 <WindowsPersistSimpleIdentifiers/> 매니페스트 플래그 때문에 이제
    # simple-id가 content model 필수 항목(2025-08-20 실물 오류로 확인) - devicelayouts
    # 뒤에 추가.
    dash_guid = "{" + str(uuid.uuid4()).upper() + "}"
    return f"""    <dashboard name='{dash_name}'>
      <style />
      <size maxheight='{DASH_H}' maxwidth='{DASH_W}' minheight='{DASH_H}' minwidth='{DASH_W}' sizing-mode='fixed' />
      <zones>
{desktop_zones}
      </zones>
      <devicelayouts>
        <devicelayout name='Phone'>
          <size maxheight='2200' minheight='2200' sizing-mode='vscroll' />
          <zones>
{phone_zones}
          </zones>
        </devicelayout>
      </devicelayouts>
      <simple-id uuid='{dash_guid}' />
    </dashboard>"""


DASHBOARDS_XML = "\n".join(build_dashboard(name, tree) for name, tree in PAGE_LAYOUTS.items())

# ------------------------------------------------------------------
# 7) windows (워크시트마다 1개 + 대시보드마다 1개, 동일한 cards 블록 재사용)
# ------------------------------------------------------------------
CARDS_BLOCK = """      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='2147483647'>
            <card type='columns' />
          </strip>
        </edge>
        <edge name='right'>
          <strip size='160'>
            <card type='measures' />
          </strip>
        </edge>
      </cards>"""

# 확정된 사실(2026.2 XSD): 워크시트 창(Window-WorksheetWindow-G)과 대시보드 창
# (Window-DashboardWindow-G)은 완전히 다른 내용 모델을 씀.
#   - 워크시트: Cards-G + VisualDoc-G(선택) + simple-id(선택)  -> 지금까지 쓴 <cards> 구조가 맞음
#   - 대시보드: VisualDocs-G(<viewpoints>) + <active> 필수 + grid(선택) + simple-id(선택)
#     대시보드 창에도 <cards>를 그대로 재사용한 게 2805CF18의 유력한 원인으로 추정됨 - 이번에 분리.
window_blocks = []
for sn in worksheet_names:
    window_blocks.append(f"    <window class='worksheet' name='{sn}'>\n{CARDS_BLOCK}\n    </window>")
for dn, sheets in PAGE_SHEETS.items():
    # 실물 확인('대시보드 2'): <viewpoints>는 비어있지 않고 워크시트별 <viewpoint name='...'/>를
    # 담고 있었으며, <active id='...'/>는 실제 zone id(더미 '0'이 아님 - 존재하지 않는 zone을
    # 가리키면 크래시로 이어졌을 가능성 높음)를 가리켰음. 첫 워크시트의 zone id를 active로 사용.
    zone_ids = DASHBOARD_ZONE_IDS[dn]
    # 대시보드에 배치된 워크시트를 "표준" 대신 "전체 보기"로 설정 - 2026.2 XSD의
    # VisualDoc-Viewpoint-G/VisualDoc-Zoom-G 그룹에서 <viewpoint name='...'><zoom type='...'/>
    # </viewpoint> 구조와 VisualDoc-ZoomType-ST enum(percent/entire-view/fit-width/fit-height)을
    # 확인함 - 대시보드 창의 <viewpoints> 항목마다 붙이는 표준 방식.
    viewpoints_xml = "\n".join(
        f"        <viewpoint name='{sn}'>\n          <zoom type='entire-view' />\n        </viewpoint>"
        for sn in sheets
    )
    active_id = zone_ids[sheets[0]]
    window_blocks.append(
        f"    <window class='dashboard' name='{dn}'>\n"
        f"      <viewpoints>\n{viewpoints_xml}\n      </viewpoints>\n"
        f"      <active id='{active_id}' />\n"
        f"      <simple-id uuid='{DASHBOARD_WINDOW_GUIDS[dn]}' />\n"
        f"    </window>"
    )
WINDOWS_XML = "\n".join(window_blocks)

# ------------------------------------------------------------------
# 8) 최종 조립
# ------------------------------------------------------------------
METADATA_RECORDS = build_metadata_records()
BASE_COLUMNS_XML = build_base_columns()

WORKBOOK = f"""<?xml version='1.0' encoding='utf-8' ?>

<workbook original-version='18.1' source-build='2025.3.2 (20253.26.0109.0333)' source-platform='win' version='18.1'
          xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest>
    <AnimationOnByDefault />
    <BasicButtonObject />
    <BasicButtonObjectTextSupport />
    <MarkAnimation />
    <ObjectModelEncapsulateLegacy />
    <ObjectModelTableType />
    <SchemaViewerObjectModel />
    <SetMembershipControl />
    <SheetIdentifierTracking />
    <WindowsPersistSimpleIdentifiers />
  </document-format-change-manifest>
  <preferences />
  <style>
    <style-rule element='all'>
      <format attr='font-family' value='Noto Sans KR' />
    </style-rule>
  </style>
  <datasources>
    <datasource caption='sl_corporation_quality_claims' inline='true' name='{DS_NAME}' version='18.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='{CSV_FILENAME}' name='{CONN_NAME}'>
            <connection class='textscan' directory='{CSV_DIR_ABS}' filename='{CSV_FILENAME}'
                        password='' server='' />
          </named-connection>
        </named-connections>
        <relation connection='{CONN_NAME}' name='{CSV_FILENAME}' table='{TABLE_REF}' type='table' />
        <metadata-records>
{METADATA_RECORDS}
        </metadata-records>
      </connection>
      <aliases enabled='yes' />
{BASE_COLUMNS_XML}
{datasource_color_style_block()}
    </datasource>
{build_parameters_datasource()}
  </datasources>
  <worksheets>
{WORKSHEETS_XML}
  </worksheets>
  <dashboards>
{DASHBOARDS_XML}
  </dashboards>
  <windows>
{WINDOWS_XML}
  </windows>
</workbook>
"""

OUT_DIR = "대시보드"
os.makedirs(OUT_DIR, exist_ok=True)
OUT_PATH = os.path.join(OUT_DIR, "SL_Corporation_Quality_Claims.twb")
with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(WORKBOOK)

print(f"wrote {OUT_PATH} ({len(WORKBOOK)} bytes), {len(worksheet_names)} worksheets, {len(PAGE_SHEETS)} dashboards")

# ---- 참고용 XSD 검증 (2026.2 기준 - simple-id/explain-data 오류는 2025.3엔 해당 없음, 무시) ----
try:
    from lxml import etree

    def ensure_patched_xsd():
        if not os.path.exists(XSD_PATH):
            urllib.request.urlretrieve(XSD_URL, XSD_PATH)
        if not os.path.exists(USER_STUB_PATH):
            with open(USER_STUB_PATH, "w", encoding="utf-8") as f2:
                f2.write("""<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="http://www.tableausoftware.com/xml/user"
           xmlns:user="http://www.tableausoftware.com/xml/user" elementFormDefault="qualified">
  <xs:attributeGroup name="UserAttributes-AG"><xs:anyAttribute namespace="##any" processContents="skip"/></xs:attributeGroup>
  <xs:element name="localizable"><xs:complexType><xs:attribute name="value" type="xs:string"/><xs:attribute name="source" type="xs:string"/></xs:complexType></xs:element>
</xs:schema>
""")
        if not os.path.exists(XML_STUB_PATH):
            urllib.request.urlretrieve("https://www.w3.org/2001/xml.xsd", XML_STUB_PATH)
        if not os.path.exists(XSD_PATCHED_PATH):
            tree = etree.parse(XSD_PATH)
            root = tree.getroot()
            ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
            for imp in root.findall("xs:import", ns):
                if imp.get("namespace") == "http://www.tableausoftware.com/xml/user":
                    imp.set("schemaLocation", USER_STUB_PATH.replace("\\", "/"))
                elif imp.get("namespace") == "http://www.w3.org/XML/1998/namespace":
                    imp.set("schemaLocation", XML_STUB_PATH.replace("\\", "/"))
            tree.write(XSD_PATCHED_PATH, xml_declaration=True, encoding="utf-8")
        return XSD_PATCHED_PATH

    xsd_doc = etree.parse(ensure_patched_xsd())
    schema = etree.XMLSchema(xsd_doc)
    twb_doc = etree.parse(OUT_PATH)
    ok = schema.validate(twb_doc)
    print("XSD validation (2026.2, reference only):", "PASS" if ok else "FAIL")
    if not ok:
        for err in schema.error_log:
            print(" -", err)
except Exception as e:
    print("XSD validation skipped:", e)
