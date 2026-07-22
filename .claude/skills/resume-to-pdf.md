---
name: resume-to-pdf
description: Generate a professionally formatted Chinese resume PDF from Markdown with automatic layout validation and self-healing fixes.
type: workflow
---

# Resume to PDF Generator with Auto-Validation

Generate a polished, multi-template Chinese resume PDF from Markdown. Automatically validates for layout issues (text overlap, missing sections, content overflow) and self-heals common problems.

## Usage

```
/resume-to-pdf                    # Generate all 3 templates with validation
/resume-to-pdf --style internet   # Single template
/resume-to-pdf --quick            # Skip validation (faster)
```

## Workflow

### Phase 1: Parse the Markdown Resume

The Markdown resume lives at `d:\xiangmu\JIANLI\张冬阳-通用简历-PM-AIPM.md`.

Key sections expected:
- `# Name` (H1)
- `**个人信息行**` (gender, phone, email, location)
- `**求职意向**` (job target + salary)
- `## 个人总结`
- `## 教育经历`
- `## 实习经历`
- `## 项目经历` (H2) with `### 项目名` (H3) sub-sections
- `## 专业技能` (table format)
- `## 自我评价`

The parser is in `generate_resume_pdf_v2.py` → `parse_markdown_resume()`.

### Phase 2: Generate PDFs

Run: `d:/python39/python.exe generate_resume_pdf_v2.py`

Three templates are generated:
| Template | Style | Output |
|----------|-------|--------|
| Internet Blue | BOSS直聘风格 | 张冬阳_简历_互联网蓝.pdf |
| Business Gray | 猎聘风格 | 张冬阳_简历_商务灰.pdf |
| Modern Card | 超级简历风格 | 张冬阳_简历_现代卡片风.pdf |

### Phase 3: Validate PDFs Automatically

The validator runs automatically after generation (use `--no-validate` to skip).

Or run standalone: `d:/python39/python.exe validate_resume_pdf.py --all`

**What it checks:**
1. **Text overlap** — Bold text overlapping with adjacent normal text (the most common issue)
2. **Baseline misalignment** — Same-line text with different vertical positions
3. **Content overflow** — Text exceeding page margins
4. **Missing sections** — Required sections absent from the resume
5. **Uneven line spacing** — Anomalous gaps between lines
6. **Text truncation** — Content cut off at page edges

### Phase 4: Self-Heal on Error

If validation finds `text_overlap` errors:

1. Identify which section has the overlap (check the surrounding text in the error detail)
2. Open `generate_resume_pdf_v2.py`
3. In the corresponding `draw_*` method, increase the `set_y(get_y() + N)` offset after the `cell()` call
4. Start by increasing the offset by 2mm (5.7pt)
5. Regenerate and re-validate
6. Repeat until clean

**Common overlap patterns and fixes:**

| Pattern | Location | Fix |
|---------|----------|-----|
| Bold title + normal bullets | `draw_projects` | `set_y(+6.5)` after title `cell()` |
| Bold category + content | `draw_skills` | `set_y(+6)` after category `cell()` |
| Bold school/company + subtitle | `draw_education` / `draw_internship` | `set_y(+7)` after first-line `cell()` |
| Summary close to section title | `draw_summary` | `set_y(+3)` after `section_title()` |

### Phase 5: Final Cleanup

When all templates pass validation:
- Remove temporary `_v2`, `_v3` suffix files
- Report final output files with their paths

## Key Technical Notes

### The `cell()` Trap
`fpdf2.cell()` does NOT advance the y-coordinate. After every `cell()` call that represents a full line of text, you MUST manually call `pdf.set_y(pdf.get_y() + cell_height + gap)` before drawing the next line. **This is the #1 cause of text overlap in the generated PDFs.**

### Font Registration
Chinese fonts are loaded from `C:\Windows\Fonts`:
- `msyh.ttc` → YaHei (Microsoft YaHei Regular)
- `msyhbd.ttc` → YaHei Bold
- Falls back to SimHei, SimKai, SimFang

### Page Layout
- A4 page: 210 × 297 mm
- Margins: left=20mm, right=20mm, top=10mm
- Content area: x=27 to 190 (163mm wide)
- Auto page break at 15mm from bottom

## Files

| File | Purpose |
|------|---------|
| `generate_resume_pdf_v2.py` | Main generation script with 3 templates |
| `validate_resume_pdf.py` | PDF layout validator |
| `张冬阳-通用简历-PM-AIPM.md` | Source markdown resume |

## Dependencies

```
pip install fpdf2 PyMuPDF
```

- `fpdf2` — PDF generation
- `PyMuPDF` (fitz) — PDF text extraction and validation
