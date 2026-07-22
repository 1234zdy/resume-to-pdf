#!/usr/bin/env python3
"""
简历 PDF 自动校验器 — 检测排版问题并报告

检测项目：
  1. 粗体/普通文字重叠（不同字重的文字 bounding box 重叠）
  2. 同行文字基线不一致（同一行内不同 span 的 y 偏差过大）
  3. 内容越界（文字超出页边距）
  4. 必需模块缺失（个人总结/教育/实习/项目/技能/自我评价）
  5. 行间距异常（相邻行间距不均匀）
  6. 文字截断检测

用法：
    python validate_resume_pdf.py <pdf_path>         # 校验单个 PDF
    python validate_resume_pdf.py --all               # 校验所有 PDF
    python validate_resume_pdf.py --json              # JSON 输出
"""

import os
import re
import sys
import json
import argparse
from collections import defaultdict

import fitz  # PyMuPDF


# ============================================================
# 配置
# ============================================================

# 页面尺寸 (A4, pt)
PAGE_WIDTH = 595.3
PAGE_HEIGHT = 841.9

# 页边距 (mm -> pt)
MARGIN_LEFT = 20 * 2.835     # ~57pt
MARGIN_RIGHT = 20 * 2.835    # ~57pt
MARGIN_BOTTOM = 15 * 2.835   # ~43pt

# 重叠检测容差 (pt)
OVERLAP_TOLERANCE = 1.5

# 行间距异常阈值
LINE_GAP_DEVIATION = 0.5

# 必需模块关键词
REQUIRED_SECTIONS = [
    '个人总结', '教育经历', '实习经历', '项目经历', '专业技能', '自我评价'
]


# ============================================================
# 文字提取
# ============================================================

def extract_spans(page) -> list:
    """提取页面所有文字 span"""
    spans = []
    blocks = page.get_text("dict").get("blocks", [])

    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            line_spans = []
            for span in line.get("spans", []):
                text = span["text"].strip()
                if not text:
                    continue
                line_spans.append({
                    "text": text,
                    "bbox": span["bbox"],
                    "font": span.get("font", ""),
                    "size": round(span["size"], 1),
                    "flags": span.get("flags", 0),
                })
            if line_spans:
                line_bbox = line["bbox"]
                for s in line_spans:
                    s["line_bbox"] = line_bbox
                spans.extend(line_spans)

    return spans


def is_bold(span) -> bool:
    """判断 span 是否为粗体"""
    if "bold" in span.get("font", "").lower():
        return True
    if span.get("flags", 0) & 2:
        return True
    return False


def spans_on_different_lines(s1, s2) -> bool:
    """判断两个 span 是否在不同行（允许同一行内多个 span）"""
    y0_1, y1_1 = s1["line_bbox"][1], s1["line_bbox"][3]
    y0_2, y1_2 = s2["line_bbox"][1], s2["line_bbox"][3]
    center1 = (y0_1 + y1_1) / 2
    center2 = (y0_2 + y1_2) / 2
    line_h1 = y1_1 - y0_1
    return abs(center1 - center2) > line_h1 * 0.6


# ============================================================
# 检测函数
# ============================================================

def check_text_overlap(spans: list) -> list:
    """检测不同行、粗体vs普通的文字垂直重叠"""
    issues = []
    for i, s1 in enumerate(spans):
        for j, s2 in enumerate(spans):
            if i >= j:
                continue
            if not spans_on_different_lines(s1, s2):
                continue
            if is_bold(s1) == is_bold(s2):
                continue

            # 垂直重叠
            v_overlap = min(s1["bbox"][3], s2["bbox"][3]) - max(s1["bbox"][1], s2["bbox"][1])
            if v_overlap <= OVERLAP_TOLERANCE:
                continue

            # 水平重叠（至少 10pt）
            h_overlap = min(s1["bbox"][2], s2["bbox"][2]) - max(s1["bbox"][0], s2["bbox"][0])
            if h_overlap <= 10:
                continue

            bold_span = s1 if is_bold(s1) else s2
            normal_span = s2 if is_bold(s1) else s1
            issues.append({
                "type": "text_overlap",
                "severity": "error",
                "detail": (
                    f'Bold "{bold_span["text"][:25]}" '
                    f'overlaps with normal "{normal_span["text"][:25]}" '
                    f'(v-overlap={v_overlap:.1f}pt)'
                ),
                "vertical_overlap_pt": round(v_overlap, 1),
            })

    return issues


def check_baseline_alignment(spans: list) -> list:
    """检测同行内 span 的基线偏差"""
    issues = []
    lines = defaultdict(list)
    for s in spans:
        key = tuple(round(v, 1) for v in s["line_bbox"])
        lines[key].append(s)

    for line_spans in lines.values():
        if len(line_spans) < 2:
            continue
        bottoms = [s["bbox"][3] for s in line_spans]
        max_diff = max(bottoms) - min(bottoms)
        if max_diff > 3:
            texts = [s["text"][:15] for s in line_spans]
            issues.append({
                "type": "baseline_misalign",
                "severity": "warning",
                "detail": f'Baseline deviation {max_diff:.1f}pt: {texts}',
                "diff_pt": round(max_diff, 1),
            })

    return issues


def check_content_bounds(spans: list) -> list:
    """检测文字越界"""
    issues = []
    for s in spans:
        b = s["bbox"]
        t = s["text"][:30]
        if b[0] < MARGIN_LEFT - 2:
            issues.append({
                "type": "left_overflow",
                "severity": "error",
                "detail": f'"{t}" exceeds left margin (x0={b[0]:.0f}pt)',
            })
        if b[2] > PAGE_WIDTH - MARGIN_RIGHT + 10:
            issues.append({
                "type": "right_overflow",
                "severity": "warning",
                "detail": f'"{t}" exceeds right margin (x1={b[2]:.0f}pt)',
            })
        if b[3] > PAGE_HEIGHT - MARGIN_BOTTOM:
            issues.append({
                "type": "bottom_overflow",
                "severity": "warning",
                "detail": f'"{t}" too close to bottom (y1={b[3]:.0f}pt)',
            })
    return issues


def check_required_sections(all_text: str) -> list:
    """检测必需模块"""
    issues = []
    for section in REQUIRED_SECTIONS:
        if section not in all_text:
            issues.append({
                "type": "missing_section",
                "severity": "error",
                "detail": f'Missing required section: "{section}"',
            })
    return issues


def check_line_spacing(spans: list) -> list:
    """检测行间距异常"""
    issues = []
    sorted_spans = sorted(spans, key=lambda s: s["line_bbox"][1])
    gaps = []
    for i in range(len(sorted_spans) - 1):
        s1, s2 = sorted_spans[i], sorted_spans[i + 1]
        x_diff = abs(s1["bbox"][0] - s2["bbox"][0])
        if x_diff > 20:
            continue
        gap = s2["line_bbox"][1] - s1["line_bbox"][3]
        if gap > 0:
            gaps.append(gap)

    if len(gaps) < 3:
        return issues

    median_gap = sorted(gaps)[len(gaps) // 2]
    if median_gap < 2:
        return issues

    for i, gap in enumerate(gaps):
        deviation = abs(gap - median_gap) / median_gap
        if deviation > LINE_GAP_DEVIATION and gap > median_gap * 2:
            issues.append({
                "type": "uneven_spacing",
                "severity": "warning",
                "detail": f'Line {i+1} spacing anomaly: {gap:.1f}pt vs median {median_gap:.1f}pt',
                "gap_pt": round(gap, 1),
            })

    return issues


def check_text_truncation(spans: list) -> list:
    """检测文字截断"""
    issues = []
    for s in spans:
        text = s["text"]
        if len(text) > 2 and text[-1] in ',.;:!?' and s["bbox"][2] > PAGE_WIDTH - MARGIN_RIGHT:
            issues.append({
                "type": "possible_truncation",
                "severity": "warning",
                "detail": f'"{text[:30]}" may be truncated at right edge',
            })
    return issues


# ============================================================
# 主入口
# ============================================================

def validate_pdf(pdf_path: str) -> dict:
    """校验单个 PDF"""
    if not os.path.exists(pdf_path):
        return {"file": pdf_path, "error": "file not found"}

    result = {
        "file": pdf_path,
        "pages": 0,
        "issues": [],
        "passed": True,
    }

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        result["error"] = str(e)
        return result

    result["pages"] = len(doc)
    all_text = ""

    for page_num in range(len(doc)):
        page = doc[page_num]
        all_text += page.get_text()
        spans = extract_spans(page)
        if not spans:
            continue

        for check_name, issues in [
            ("text_overlap", check_text_overlap(spans)),
            ("baseline_misalign", check_baseline_alignment(spans)),
            ("content_bounds", check_content_bounds(spans)),
            ("line_spacing", check_line_spacing(spans)),
            ("text_truncation", check_text_truncation(spans)),
        ]:
            for issue in issues:
                issue["page"] = page_num + 1
            result["issues"].extend(issues)

    result["issues"].extend(check_required_sections(all_text))
    doc.close()

    errors = [i for i in result["issues"] if i.get("severity") == "error"]
    result["passed"] = len(errors) == 0
    result["error_count"] = len(errors)
    result["warning_count"] = len(result["issues"]) - len(errors)

    return result


def print_result(result: dict):
    """格式化输出校验结果"""
    print(f'\n{"=" * 60}')
    print(f'  Resume PDF Validator')
    print(f'{"=" * 60}')
    print(f'\n  File: {result["file"]}')
    print(f'  Pages: {result["pages"]}')

    issues = result["issues"]
    if not issues:
        print(f'\n  [PASS] No issues detected!')
        return

    errors = [i for i in issues if i.get("severity") == "error"]
    warnings = [i for i in issues if i.get("severity") == "warning"]

    if errors:
        print(f'\n  [ERROR] {len(errors)} issue(s):')
        for i, issue in enumerate(errors, 1):
            print(f'     {i}. [{issue["type"]}] {issue["detail"]}')

    if warnings:
        print(f'\n  [WARN] {len(warnings)} issue(s):')
        for i, issue in enumerate(warnings[:5], 1):
            print(f'     {i}. [{issue["type"]}] {issue["detail"]}')
        if len(warnings) > 5:
            print(f'     ... +{len(warnings) - 5} more')

    if result.get("passed"):
        print(f'\n  [PASS] Layout OK')
    else:
        print(f'\n  [FAIL] {result["error_count"]} error(s) need fixing')


def validate_all(pdf_dir: str) -> list:
    """校验目录下所有 PDF"""
    results = []
    pdfs = sorted([f for f in os.listdir(pdf_dir)
                   if f.endswith('.pdf') and not f.startswith('~')])
    for fname in pdfs:
        path = os.path.join(pdf_dir, fname)
        result = validate_pdf(path)
        results.append(result)
        print_result(result)
    return results


def main():
    parser = argparse.ArgumentParser(description='Resume PDF Validator')
    parser.add_argument('path', nargs='?', help='PDF file path')
    parser.add_argument('--all', '-a', action='store_true', help='Validate all PDFs')
    parser.add_argument('--json', '-j', action='store_true', help='JSON output')
    parser.add_argument('--dir', '-d', default=r'd:\xiangmu\JIANLI', help='PDF directory')
    args = parser.parse_args()

    if args.all:
        results = validate_all(args.dir)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        total_errors = sum(r.get("error_count", 0) for r in results)
        sys.exit(1 if total_errors > 0 else 0)

    elif args.path:
        result = validate_pdf(args.path)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print_result(result)
        sys.exit(0 if result.get("passed") else 1)

    else:
        pdfs = sorted(
            [f for f in os.listdir(args.dir) if f.endswith('.pdf') and not f.startswith('~')],
            key=lambda f: os.path.getmtime(os.path.join(args.dir, f)),
            reverse=True,
        )
        if not pdfs:
            print("No PDF files found")
            sys.exit(1)
        for pdf in pdfs[:3]:
            result = validate_pdf(os.path.join(args.dir, pdf))
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_result(result)


if __name__ == '__main__':
    main()
