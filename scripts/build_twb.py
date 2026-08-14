# -*- coding: utf-8 -*-
"""
최소 구성 .twb 생성 스크립트 (1단계 시드 테스트용).

목적: Tableau 구현 가이드.md 에서 확보한 지식(공식 XSD + 공식문서)으로 만든 첫 실제 시도.
구성: CSV 데이터 연결 1개 + 컬럼 24개(타입 매핑) + 워크시트 1개(고객사별 클레임 금액 막대그래프).
대시보드는 아직 없음 — 데이터 연결과 워크시트 자체가 Tableau에서 정상적으로 열리는지부터 확인.

가장 리스크가 큰 부분(주석 표시):
  - <connection> 내부 구조 (공식 스키마도 검증 안 하는 영역)
  - rows/cols 필드 표기 규칙 (:nk, :qk 접미사)
  - workbook version/original-version 값 (2025.3 정확한 값 미확인, 18.1로 추정)
"""
import os
import re
import uuid
import tempfile
import urllib.request

TMP = tempfile.gettempdir()
XSD_URL = "https://raw.githubusercontent.com/tableau/tableau-document-schemas/main/schemas/2026_2/twb_2026.2.0.xsd"
XSD_PATH = os.path.join(TMP, "twb_2026.2.0.xsd")
XSD_PATCHED_PATH = os.path.join(TMP, "twb_2026.2.0_patched.xsd")
USER_STUB_PATH = os.path.join(TMP, "user_stub.xsd")
XML_STUB_PATH = os.path.join(TMP, "xml.xsd")


def ensure_patched_xsd():
    """공식 XSD를 내려받고, lxml이 바로 못 읽는 user:/xml: 네임스페이스 import에
    schemaLocation을 채운 로컬 패치본을 만든다 (구조 검증과 무관한 로더 이슈 우회)."""
    from lxml import etree

    if not os.path.exists(XSD_PATH):
        urllib.request.urlretrieve(XSD_URL, XSD_PATH)
    if not os.path.exists(USER_STUB_PATH):
        with open(USER_STUB_PATH, "w", encoding="utf-8") as f:
            f.write("""<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="http://www.tableausoftware.com/xml/user"
           xmlns:user="http://www.tableausoftware.com/xml/user"
           elementFormDefault="qualified">
  <xs:attributeGroup name="UserAttributes-AG">
    <xs:anyAttribute namespace="##any" processContents="skip"/>
  </xs:attributeGroup>
  <xs:element name="localizable">
    <xs:complexType>
      <xs:attribute name="value" type="xs:string"/>
      <xs:attribute name="source" type="xs:string"/>
    </xs:complexType>
  </xs:element>
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


CSV_PATH_ABS = r"c:\Users\milvus-Tom\.claude\Project\AI-Tableau\data\sl_corporation_quality_claims.csv"
CSV_DIR_ABS = CSV_PATH_ABS.replace("\\", "/").rsplit("/", 1)[0]
CSV_FILENAME = "sl_corporation_quality_claims.csv"

# (컬럼명, datatype, role, type) -- Data Dictionary.md / Tableau 구현 가이드.md §3 매핑 그대로
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


def caption_of(name):
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


def build_columns():
    parts = []
    for name, dtype, role, ftype in COLUMNS:
        parts.append(
            f"    <column caption='{caption_of(name)}' datatype='{dtype}' "
            f"name='[{name}]' role='{role}' type='{ftype}' />"
        )
    return "\n".join(parts)


METADATA_RECORDS = build_metadata_records()
COLUMNS_XML = build_columns()

WORKBOOK = f"""<?xml version='1.0' encoding='utf-8' ?>

<workbook original-version='18.1' source-build='2025.3.0' source-platform='win' version='18.1'
          xmlns:user='http://www.tableausoftware.com/xml/user'>
  <preferences />
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
{COLUMNS_XML}
    </datasource>
  </datasources>
  <worksheets>
    <worksheet name='0_Test_고객사별금액'>
      <table>
        <view>
          <datasources>
            <datasource caption='sl_corporation_quality_claims' name='{DS_NAME}' />
          </datasources>
          <datasource-dependencies datasource='{DS_NAME}'>
            <column caption='Customer' datatype='string' name='[customer]' role='dimension' type='nominal' />
            <column caption='Claim Amount Usd' datatype='real' name='[claim_amount_usd]' role='measure' type='quantitative' />
          </datasource-dependencies>
          <aggregation value='true' />
        </view>
        <style />
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Automatic' />
            <encodings>
              <text column='[{DS_NAME}].[sum:claim_amount_usd:qk]' />
            </encodings>
          </pane>
        </panes>
        <rows>[{DS_NAME}].[none:customer:nk]</rows>
        <cols>[{DS_NAME}].[sum:claim_amount_usd:qk]</cols>
      </table>
      <simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' />
    </worksheet>
  </worksheets>
  <windows>
    <window class='worksheet' name='0_Test_고객사별금액'>
      <cards>
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
      </cards>
    </window>
  </windows>
  <explain-data enabled-for-viewer='true' extreme-values-enabled-for-all='false'>
    <explanation-types />
  </explain-data>
</workbook>
"""

with open("SL_Corporation_Quality_Claims.twb", "w", encoding="utf-8") as f:
    f.write(WORKBOOK)

print("wrote SL_Corporation_Quality_Claims.twb (%d bytes)" % len(WORKBOOK))

# ---- XSD 구문 검증 (2026.2 스키마 기준 - 2025.3용 공식 스키마는 없어 참고용) ----
# 원본 XSD는 user:/xml: 네임스페이스를 schemaLocation 없이 import하므로 lxml이 바로 못 읽음.
# 로컬 스텁 스키마(user_stub.xsd, xml.xsd)를 만들어 import에 schemaLocation을 채운
# "_patched" 버전을 대신 사용 (구조 검증 자체와는 무관한 lxml 로더 이슈 우회).
try:
    from lxml import etree
    xsd_doc = etree.parse(ensure_patched_xsd())
    schema = etree.XMLSchema(xsd_doc)
    twb_doc = etree.parse("SL_Corporation_Quality_Claims.twb")
    ok = schema.validate(twb_doc)
    print("XSD validation (2026.2, reference only):", "PASS" if ok else "FAIL")
    if not ok:
        for err in schema.error_log:
            print(" -", err)
except Exception as e:
    print("XSD validation skipped:", e)
