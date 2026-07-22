# Resume to PDF

> 中文简历 Markdown → 多模板 PDF 生成器，内置自动排版校验

## 快速开始

```bash
# 1. 安装依赖
pip install fpdf2 PyMuPDF

# 2. 编写你的简历 (参考下方格式)
# 3. 生成 PDF + 自动校验
python generate_resume_pdf_v2.py --input 我的简历.md
```

## 使用方法

```bash
# 生成全部 3 套模板（默认带校验）
python generate_resume_pdf_v2.py

# 只生成一种风格
python generate_resume_pdf_v2.py --style internet    # 互联网蓝
python generate_resume_pdf_v2.py --style business    # 商务灰
python generate_resume_pdf_v2.py --style modern      # 现代卡片风

# 跳过自动校验（更快）
python generate_resume_pdf_v2.py --no-validate

# 单独校验 PDF 排版
python validate_resume_pdf.py 简历_互联网蓝.pdf
python validate_resume_pdf.py --all                  # 校验所有
```

## 三套模板

| 风格 | 预览 | 设计来源 |
|------|------|----------|
| 互联网蓝 | 清爽蓝白，强调数据指标 | BOSS直聘 / 拉勾 |
| 商务灰 | 深色稳重，专业商务感 | 猎聘 / 前程无忧 |
| 现代卡片风 | 青绿色调，信息层级清晰 | 超级简历 / Canva |

## Markdown 简历格式

```markdown
# 姓名

**性别 | 电话 | 邮箱 | 城市**

**求职意向：职位方向 | 期望薪资：XX**

---

## 个人总结

一段 2-3 行的自我描述...

---

## 教育经历

**学校名称 | 专业 | 学历 | 2020-2024**

---

## 实习经历

**公司名称 | 职位方向 | 2024.01-2024.06**

- 工作内容要点 1
- 工作内容要点 2

---

## 项目经历

### 项目名称 | 角色

- **背景**：...
- **方案**：...
- **成果**：...

---

## 专业技能

| 类别 | 具体能力 |
|------|---------|
| **类别A** | 技能描述 |
| **类别B** | 技能描述 |

---

## 自我评价

- **关键词**：描述内容
```

## 自动校验

生成 PDF 后自动运行 6 项检测：

- **文字重叠** — 粗体与普通文字 bounding box 是否重叠
- **基线对齐** — 同行文字垂直位置是否一致
- **内容越界** — 文字是否超出页边距
- **模块缺失** — 必需章节是否完整
- **行间距** — 行距是否均匀
- **文字截断** — 内容是否在边界被裁剪

## 文件说明

| 文件 | 用途 |
|------|------|
| `generate_resume_pdf_v2.py` | PDF 生成主脚本 |
| `validate_resume_pdf.py` | PDF 排版自动校验器 |
| `.claude/skills/resume-to-pdf.md` | Claude Code skill |

## 依赖

- Python 3.8+
- [fpdf2](https://github.com/py-pdf/fpdf2) — PDF 生成
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) — 排版校验
- 中文字体：微软雅黑 (`C:\Windows\Fonts\msyh.ttc`)
