"""
Minimal XLSX exporter for comparison summaries.

No third-party dependency is required. The generated file is a normal
.xlsx workbook with one sheet named "Comparison".
"""

from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


HEADERS = [
    "Case",
    "N",
    "M",
    "b",
    "LowerBound",
    "Solver",
    "Status",
    "MaxLoad",
    "DeltaCP",
    "GainGreedy",
    "GapLBPercent",
    "TimeSeconds",
    "PeakMemoryKB",
    "Notes",
]


def _col_name(col_index):
    name = ""
    while col_index:
        col_index, rem = divmod(col_index - 1, 26)
        name = chr(65 + rem) + name
    return name


def _cell_ref(row_index, col_index):
    return f"{_col_name(col_index)}{row_index}"


def _cell_xml(row_index, col_index, value):
    ref = _cell_ref(row_index, col_index)
    if value is None:
        return f'<c r="{ref}"/>'
    if isinstance(value, bool):
        return f'<c r="{ref}" t="b"><v>{1 if value else 0}</v></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}"><v>{value}</v></c>'
    text = escape(str(value))
    return f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>'


def _sheet_xml(rows):
    xml_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = "".join(
            _cell_xml(row_index, col_index, value)
            for col_index, value in enumerate(row, start=1)
        )
        xml_rows.append(f'<row r="{row_index}">{cells}</row>')

    dimension = f"A1:{_cell_ref(max(1, len(rows)), len(HEADERS))}"
    cols = "".join(
        f'<col min="{i}" max="{i}" width="{width}" customWidth="1"/>'
        for i, width in enumerate([24, 8, 8, 6, 12, 12, 18, 10, 10, 14, 14, 14, 14, 42], start=1)
    )
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
           xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <dimension ref="{dimension}"/>
  <sheetViews><sheetView workbookViewId="0"/></sheetViews>
  <sheetFormatPr defaultRowHeight="15"/>
  <cols>{cols}</cols>
  <sheetData>{''.join(xml_rows)}</sheetData>
  <autoFilter ref="{dimension}"/>
</worksheet>'''


def _workbook_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Comparison" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>'''


def _workbook_rels_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"
    Target="worksheets/sheet1.xml"/>
</Relationships>'''


def _root_rels_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
    Target="xl/workbook.xml"/>
</Relationships>'''


def _content_types_xml():
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml"
    ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>'''


def comparison_rows(summaries):
    if isinstance(summaries, dict):
        summaries = [summaries]

    rows = [HEADERS]
    for summary in summaries:
        results = summary.get("results", [])
        greedy = next((r for r in results if r.get("solver") == "Greedy"), None)
        cpsat = next((r for r in results if r.get("solver") == "CP-SAT"), None)
        greedy_max = greedy.get("max_load") if greedy else None
        cpsat_max = cpsat.get("max_load") if cpsat else None
        lb = summary.get("lower_bound")

        for result in results:
            max_load = result.get("max_load")
            delta_cp = (
                max_load - cpsat_max
                if isinstance(max_load, int) and isinstance(cpsat_max, int) and cpsat_max >= 0
                else None
            )
            gain_greedy = (
                greedy_max - max_load
                if isinstance(max_load, int) and isinstance(greedy_max, int) and greedy_max >= 0
                else None
            )
            gap_lb = (
                round((max_load - lb) / lb * 100, 4)
                if isinstance(max_load, int) and isinstance(lb, int) and lb > 0 and max_load >= 0
                else None
            )
            extra = result.get("extra", {})
            notes = extra.get("source") or extra.get("status") or ""

            rows.append([
                summary.get("case_name"),
                summary.get("N"),
                summary.get("M"),
                summary.get("b"),
                lb,
                result.get("solver"),
                result.get("status"),
                max_load,
                delta_cp,
                gain_greedy,
                gap_lb,
                round(result.get("time_seconds", 0), 6),
                round(result.get("peak_memory_kb", 0), 2),
                notes,
            ])

    return rows


def write_comparison_excel(summaries, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = comparison_rows(summaries)

    with ZipFile(output_path, "w", ZIP_DEFLATED) as xlsx:
        xlsx.writestr("[Content_Types].xml", _content_types_xml())
        xlsx.writestr("_rels/.rels", _root_rels_xml())
        xlsx.writestr("xl/workbook.xml", _workbook_xml())
        xlsx.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml())
        xlsx.writestr("xl/worksheets/sheet1.xml", _sheet_xml(rows))

    return output_path
