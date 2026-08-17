# -*- coding: utf-8 -*-
"""
대시보드 오류(2805CF18) 격리 테스트용 초최소 파일.

지금까지 4단계에 걸쳐 스키마 기반으로 확인/수정한 내용(datasources, datasource-dependencies,
devicelayouts, window의 viewpoints/active 구조)을 전부 반영했는데도 동일 오류가 반복됨.
그래서 변수를 최대한 줄인 상태로 "대시보드 1개 + 워크시트 1개(가장 단순한 막대차트, 지도/필터/
집계문자열 없음)"만 만들어서, 이 최소 조합조차 안 열리는지 확인한다.

- 안 열리면: 대시보드 구조 자체에 아직 못 찾은 근본 문제가 있다는 뜻 -> 접근 방식 재검토 필요
- 열리면: 우리가 쓴 특정 요소(지도의 위경도 필드, 소형멀티플의 filter, 9개 zone 등) 중
  하나가 원인 -> 어떤 걸 다시 추가했을 때 깨지는지 하나씩 늘려가며 좁힐 수 있음
"""
import os
import uuid
import tempfile
import urllib.request

TMP = tempfile.gettempdir()
CSV_PATH_ABS = r"c:\Users\milvus-Tom\.claude\Project\AI-Tableau\data\sl_corporation_quality_claims.csv"
CSV_DIR_ABS = CSV_PATH_ABS.replace("\\", "/").rsplit("/", 1)[0]
CSV_FILENAME = "sl_corporation_quality_claims.csv"

COLUMNS = [
    ("claim_id", "string", "dimension", "nominal"),
    ("customer", "string", "dimension", "nominal"),
    ("claim_status", "string", "dimension", "nominal"),
    ("claim_amount_usd", "real", "measure", "quantitative"),
]
REMOTE_TYPE = {"string": "129", "date": "133", "integer": "20", "real": "5"}


def rand_id(prefix, n=20):
    return prefix + "." + uuid.uuid4().hex[:n]


DS_NAME = rand_id("federated")
CONN_NAME = rand_id("textscan")
TABLE_REF = "[%s#csv]" % CSV_FILENAME.replace(".csv", "")


def caption_of(name):
    return " ".join(w.capitalize() for w in name.split("_"))


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
        parts.append(f"    <column caption='{caption_of(name)}' datatype='{dtype}' name='[{name}]' role='{role}' type='{ftype}' />")
    return "\n".join(parts)


METADATA_RECORDS = build_metadata_records()
BASE_COLUMNS_XML = build_base_columns()

DIM_INST = "[none:customer:nk]"
MEAS_INST = "[sum:claim_amount_usd:qk]"
DIM_Q = f"[{DS_NAME}].{DIM_INST}"
MEAS_Q = f"[{DS_NAME}].{MEAS_INST}"

WORKSHEET_XML = f"""    <worksheet name='Test_Sheet'>
      <table>
        <view>
          <datasources>
            <datasource caption='sl_corporation_quality_claims' name='{DS_NAME}' />
          </datasources>
          <datasource-dependencies datasource='{DS_NAME}'>
            <column caption='Customer' datatype='string' name='[customer]' role='dimension' type='nominal' />
            <column caption='Claim Amount Usd' datatype='real' name='[claim_amount_usd]' role='measure' type='quantitative' />
            <column-instance column='[customer]' derivation='None' name='{DIM_INST}' pivot='key' type='nominal' />
            <column-instance column='[claim_amount_usd]' derivation='Sum' name='{MEAS_INST}' pivot='key' type='quantitative' />
          </datasource-dependencies>
          <aggregation value='true' />
        </view>
        <style />
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Bar' />
            <encodings />
          </pane>
        </panes>
        <rows>{DIM_Q}</rows>
        <cols>{MEAS_Q}</cols>
      </table>
    </worksheet>"""

DASHBOARD_DEPS = f"""            <column caption='Customer' datatype='string' name='[customer]' role='dimension' type='nominal' />
            <column caption='Claim Amount Usd' datatype='real' name='[claim_amount_usd]' role='measure' type='quantitative' />
            <column-instance column='[customer]' derivation='None' name='{DIM_INST}' pivot='key' type='nominal' />
            <column-instance column='[claim_amount_usd]' derivation='Sum' name='{MEAS_INST}' pivot='key' type='quantitative' />"""

DASHBOARD_XML = f"""    <dashboard name='Test_Dashboard'>
      <style />
      <size sizing-mode='automatic' />
      <datasources>
        <datasource caption='sl_corporation_quality_claims' name='{DS_NAME}' />
      </datasources>
      <datasource-dependencies datasource='{DS_NAME}'>
{DASHBOARD_DEPS}
      </datasource-dependencies>
      <zones>
        <zone h='100000' id='2' type-v2='layout-basic' w='100000' x='0' y='0'>
          <zone h='100000' id='3' name='Test_Sheet' type-v2='visual' w='100000' x='0' y='0' />
        </zone>
      </zones>
      <devicelayouts>
        <devicelayout name='Desktop' />
      </devicelayouts>
    </dashboard>"""

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

WINDOWS_XML = f"""    <window class='worksheet' name='Test_Sheet'>
{CARDS_BLOCK}
    </window>
    <window class='dashboard' name='Test_Dashboard'>
      <viewpoints />
      <active id='0' />
    </window>"""

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
  </datasources>
  <worksheets>
{WORKSHEET_XML}
  </worksheets>
  <dashboards>
{DASHBOARD_XML}
  </dashboards>
  <windows>
{WINDOWS_XML}
  </windows>
</workbook>
"""

OUT_PATH = "Dashboard_Isolation_Test.twb"
with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(WORKBOOK)
print(f"wrote {OUT_PATH} ({len(WORKBOOK)} bytes)")
