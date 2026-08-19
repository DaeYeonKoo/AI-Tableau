# -*- coding: utf-8 -*-
"""
전체 3페이지 대시보드 .twb 생성 스크립트 (검증 없이 바로 시도하는 버전).

전제: rows/cols 필드 주소 문법(column-instance)이 아직 실물로 검증되지 않았음.
1차 실패(9CA7205B)의 원인으로 "column-instance를 datasource-dependencies에 선언하지
않고 바로 참조한 것"으로 추정 - 이번엔 사용하는 모든 필드마다 column-instance를 명시적으로
선언한다. 그래도 파일이 열리지 않을 가능성을 사용자에게 명확히 알릴 것.

구성: 데이터소스(24개 원본 컬럼 + 계산식 6개) + 워크시트 17개 + 대시보드 3개.
일부 컴포넌트(KPI 5기간 카드, 이중축 콤보차트, 진짜 히스토그램, 세계지도)는
1차 시도 리스크를 낮추기 위해 단순화했음 - 하단 주석 참고.
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
    inst_name = f"[{derivation.lower()}:{ref}:{suffix}]"
    qualified = f"[{DS_NAME}].{inst_name}"
    return {
        "ref": ref, "dtype": dtype, "role": role, "ftype": out_ftype,
        "inst_name": inst_name, "qualified": qualified,
        "derivation": derivation, "is_measure": is_measure,
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
# 4) 워크시트 빌더
# ------------------------------------------------------------------
def ws_simple_bar(name, dim, meas, meas_agg="Sum", color_dim=None, mark="Bar"):
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
        <style />
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
        <style />
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


def ws_trend(name, dim, meas, meas_agg="Sum", mark="Line"):
    dci = col_instance(dim, "None")
    mci = col_instance(meas, meas_agg)
    filt_cis, filters_xml, slices_xml = common_filter_block()
    deps = datasource_dependencies([dci, mci] + filt_cis, sheet_name=name)
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
        <style />
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


def ws_small_multiple(name, category_value_caption, part_category_literal, meas="claim_amount_usd"):
    """part_category를 필터로 고정한 뒤 월별 트렌드 하나만 보여주는 카드 (5개 반복 생성)."""
    dci = col_instance("OccurrenceMonth", "None")
    mci = col_instance(meas, "Sum")
    fci = col_instance("part_category", "None")
    # part_category는 이 워크시트 자체가 이미 특정 값으로 고정한 필터라서, 공통 필터 박스의
    # "전체 선택" part_category 필터는 제외(같은 필드에 두 개의 <filter>가 생기는 충돌 방지).
    filt_cis, filters_xml, slices_xml = common_filter_block(exclude={"part_category"})
    deps = datasource_dependencies([dci, mci, fci] + filt_cis, sheet_name=name)
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
        <style />
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


def ws_kpi_text(name, card_field):
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
        <style />
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
        <style />
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
    worksheet_blocks.append(xml)
    worksheet_names.append(name)


# Page 1
add("1_KPI_1M", ws_kpi_text("1_KPI_1M", "KPILast1MCard"))
add("1_KPI_3M", ws_kpi_text("1_KPI_3M", "KPILast3MCard"))
add("1_KPI_6M", ws_kpi_text("1_KPI_6M", "KPILast6MCard"))
add("1_KPI_12M", ws_kpi_text("1_KPI_12M", "KPILast12MCard"))
add("1_KPI_All", ws_kpi_text("1_KPI_All", "KPIAllCard"))
add("1_Trend", ws_trend("1_Trend", "OccurrenceMonth", "claim_amount_usd", "Sum"))
add("1_Map", ws_map("1_Map"))
add("1_Top5_Customer", ws_simple_bar("1_Top5_Customer", "customer", "claim_amount_usd"))
add("1_Top5_Defect", ws_simple_bar("1_Top5_Defect", "defect_type_en", "claim_amount_usd"))
add("1_Top5_Plant", ws_simple_bar("1_Top5_Plant", "production_plant", "claim_amount_usd"))

# Page 2
for i, cat in enumerate(CATEGORIES, start=1):
    add(f"2_SM_{i}", ws_small_multiple(f"2_SM_{i}", cat, cat))
add("2_Heatmap", ws_heatmap("2_Heatmap", "production_plant", "defect_type_en", "claim_id", "Count"))
add("2_Rank_Category", ws_simple_bar("2_Rank_Category", "part_category", "claim_amount_usd"))
add("2_Rank_DefectCount", ws_simple_bar("2_Rank_DefectCount", "defect_type_en", "claim_id", "Count"))
add("2_CustComposition", ws_simple_bar("2_CustComposition", "customer", "claim_amount_usd"))

# Page 3
add("3_Status", ws_simple_bar("3_Status", "claim_status", "claim_id", "Count"))
add("3_Cycle_Customer", ws_simple_bar("3_Cycle_Customer", "customer", "TotalCycleTime", "Avg"))
add("3_Cycle_Plant", ws_simple_bar("3_Cycle_Plant", "production_plant", "TotalCycleTime", "Avg"))
add("3_Severity", ws_simple_bar("3_Severity", "severity", "claim_amount_usd", "Sum", color_dim="severity"))
add("3_LeadTime_Receive", ws_simple_bar("3_LeadTime_Receive", "claim_status", "LeadTimeToReceive", "Avg"))
add("3_LeadTime_Confirm", ws_simple_bar("3_LeadTime_Confirm", "claim_status", "LeadTimeToConfirm", "Avg"))

WORKSHEETS_XML = "\n".join(worksheet_blocks)

# ------------------------------------------------------------------
# 6) 대시보드 3개 - 대시보드 기획안.html의 그리드 구조를 가로/세로 컨테이너 트리로 재현.
#    ('leaf', 워크시트이름) | ('vert'|'horz', [자식 노드...])
# ------------------------------------------------------------------
def W(weight, node):
    """render_layout의 vert/horz 자식에 상대적 비중(weight)을 지정. 기본 비중은 1."""
    return ("w", weight, node)


TITLE_COLOR = "#16324F"

PAGE_LAYOUTS = {
    "1. 종합 요약": ("vert", [
        W(2, ("text", "종합 요약", 24, TITLE_COLOR)),
        W(7, ("horz", [
            ("leaf", "1_KPI_1M"), ("leaf", "1_KPI_3M"), ("leaf", "1_KPI_6M"),
            ("leaf", "1_KPI_12M"), ("leaf", "1_KPI_All"),
        ])),
        W(7, ("leaf", "1_Trend")),
        W(12, ("horz", [
            ("leaf", "1_Map"),
            ("vert", [("leaf", "1_Top5_Customer"), ("leaf", "1_Top5_Defect"), ("leaf", "1_Top5_Plant")]),
        ])),
    ]),
    "2. 원인 드릴다운": ("vert", [
        W(2, ("text", "원인 드릴다운", 24, TITLE_COLOR)),
        W(8, ("horz", [("leaf", f"2_SM_{i}") for i in range(1, 6)])),
        W(12, ("horz", [
            ("leaf", "2_Heatmap"),
            ("vert", [("leaf", "2_Rank_Category"), ("leaf", "2_Rank_DefectCount")]),
        ])),
        W(6, ("leaf", "2_CustComposition")),
    ]),
    "3. 리드타임 효율": ("vert", [
        W(2, ("text", "리드타임 · 효율", 24, TITLE_COLOR)),
        W(9, ("horz", [("leaf", "3_Status"), ("leaf", "3_Severity")])),
        W(9, ("horz", [("leaf", "3_LeadTime_Receive"), ("leaf", "3_LeadTime_Confirm")])),
        W(9, ("horz", [("leaf", "3_Cycle_Customer"), ("leaf", "3_Cycle_Plant")])),
    ]),
}


def flatten_leaves(node):
    if node[0] == "leaf":
        return [node[1]]
    if node[0] == "text":
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


DASHBOARD_ZONE_IDS = {}  # dash_name -> {sheet_name: zone_id} (desktop 기준) - window의 active/viewpoints에 재사용

# 탐색 버튼(type-v2='dashboard-object' + <button> zone) 시도는 REAL 2025.3 로드 오류(D2E8DA72,
# 2025-08-17)로 롤백됨: 사용자가 Tableau UI로 저장한 참고 파일과 동일한 구조를 그대로 반영했지만
# 실제 신선 로드 시 "element 'button' is not allowed for content model
# '(formatted-text,layout-cache?,zone,flipboard,zone-style?)'" 로 거부됨 - 즉 Tableau가 저장은
# 하지만 자기 로더는 거부하는 또 다른 저장/로드 포맷 불일치 사례로 확인. <window class='dashboard'>의
# <simple-id>도 같은 오류에서 "element 'simple-id' is not allowed for content model
# '((cards,viewpoint?)|(viewpoints,active,device-preview))'"로 거부됨. 두 기능 모두 실물 검증
# 없이는 재시도하지 않기로 함(Tableau 구현 가이드.md TODO 참고) - 사용자에게 "참고 파일을 완전히
# 닫았다가 다시 열어도 정상 로드되는지" 재확인 요청 예정.


def render_layout(node, id_gen, with_style, x, y, w, h, sheet_zone_ids, reuse_ids=None):
    """레이아웃 트리를 실제 zone XML로 재귀 변환.

    좌표 체계는 매 depth마다 0~100000으로 리셋되는 게 아니라, 대시보드 전체 캔버스 기준
    절대 좌표(0~100000)를 계속 이어받는 것으로 실물 파일('대시보드 2')에서 확인됨 - 자식이
    1개뿐인 컨테이너의 자식 zone이 부모와 완전히 동일한 w/h(98400/98000, 100000이 아님)를
    가졌던 것이 근거. 그래서 이 함수는 x/y/w/h를 절대값으로 받아 그대로 자식에게 분배한다.

    reuse_ids가 주어지면(phone 레이아웃 생성 시) 워크시트 leaf zone의 id를 desktop과
    동일하게 재사용 - 실물 파일에서 확인된 패턴. 컨테이너 zone은 desktop/phone 각자 새 id.
    """
    kind = node[0]
    if kind == "leaf":
        sn = node[1]
        zid = reuse_ids[sn] if reuse_ids else id_gen()
        sheet_zone_ids[sn] = zid
        style = "\n" + ZONE_STYLE if with_style else ""
        return f"          <zone h='{h}' id='{zid}' name='{sn}' w='{w}' x='{x}' y='{y}'>{style}\n          </zone>"

    if kind == "text":
        text, fontsize, color = node[1], node[2], node[3]
        zid = id_gen()
        style = "\n" + ZONE_STYLE if with_style else ""
        return (f"          <zone h='{h}' id='{zid}' type-v2='text' w='{w}' x='{x}' y='{y}'>\n"
                f"            <formatted-text><run bold='true' fontcolor='{color}' fontsize='{fontsize}'>{text}</run></formatted-text>{style}\n"
                f"          </zone>")

    children = [(_c[2], _c[1]) if _c[0] == "w" else (_c, 1) for _c in node[1]]  # (node, weight)
    total_w = sum(wt for _, wt in children)
    cid = id_gen()
    parts = []
    pos = 0
    if kind == "vert":
        for child, wt in children:
            ch_h = h * wt // total_w
            parts.append(render_layout(child, id_gen, with_style, x, y + pos, w, ch_h, sheet_zone_ids, reuse_ids))
            pos += ch_h
    else:  # horz
        for child, wt in children:
            ch_w = w * wt // total_w
            parts.append(render_layout(child, id_gen, with_style, x + pos, y, ch_w, h, sheet_zone_ids, reuse_ids))
            pos += ch_w
    inner_xml = "\n".join(parts)
    style = "\n" + ZONE_STYLE if with_style else ""
    return f"""        <zone h='{h}' id='{cid}' param='{kind}' type-v2='layout-flow' w='{w}' x='{x}' y='{y}'>
{inner_xml}{style}
        </zone>"""


def build_dashboard(dash_name, layout_tree):
    # 실물 확인('대시보드 2', 사용자가 Tableau UI로 만들어 저장 - 정상 동작) + 로드 시점 실제
    # 오류(D2E8DA72)를 합쳐서 확정한 구조:
    #   - <datasources>/<datasource-dependencies>는 대시보드에 아예 없음
    #   - 워크시트를 담는 zone엔 type-v2가 없음, 컨테이너 zone엔 type-v2='layout-flow'
    #     + param='vert'|'horz' (Phone 레이아웃의 실제 예시로 확인됨)
    #   - <size>는 sizing-mode 없이 명시적 min/max로 지정
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
    return f"""    <dashboard name='{dash_name}'>
      <style />
      <size maxheight='2400' maxwidth='1400' minheight='2400' minwidth='1400' />
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
        f"    </window>"
    )
WINDOWS_XML = "\n".join(window_blocks)

# ------------------------------------------------------------------
# 8) 최종 조립
# ------------------------------------------------------------------
METADATA_RECORDS = build_metadata_records()
BASE_COLUMNS_XML = build_base_columns()

WORKBOOK = f"""<?xml version='1.0' encoding='utf-8' ?>

<workbook original-version='18.1' source-build='2025.3.0' source-platform='win' version='18.1'
          xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest />
  <preferences />
  <style />
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

OUT_PATH = "SL_Corporation_Quality_Claims.twb"
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
