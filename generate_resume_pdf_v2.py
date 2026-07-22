#!/usr/bin/env python3
"""
简历 PDF 生成器 v2 — 自动解析 Markdown 简历 + 多套模板样式
模板风格来源：BOSS直聘、猎聘、超级简历等主流招聘平台的设计语言

用法：
    python generate_resume_pdf_v2.py                    # 生成全部3套模板
    python generate_resume_pdf_v2.py --style internet    # 仅生成互联网蓝风格
    python generate_resume_pdf_v2.py --style business    # 仅生成商务灰风格
    python generate_resume_pdf_v2.py --style modern      # 仅生成现代卡片风格
"""

import os
import re
import sys
import argparse
from fpdf import FPDF
from fpdf.enums import XPos, YPos, TableCellFillMode


# ============================================================
# 0. 通用工具
# ============================================================

def clean_md(text: str) -> str:
    """彻底清理所有 Markdown 格式标记，返回纯文本"""
    # 去掉链接 [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # 去掉粗体/斜体 **text** *text* ***text*** → text
    text = re.sub(r'\*{1,3}([^*]+?)\*{1,3}', r'\1', text)
    # 去掉行内代码 `text`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # 去掉 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()


# ============================================================
# 1. Markdown 简历解析器
# ============================================================

def parse_markdown_resume(md_path: str) -> dict:
    """解析 Markdown 简历为结构化字典"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.strip().split('\n')

    data = {
        'name': '',
        'info': '',           # 性别/电话/邮箱/地点
        'job_intent': '',     # 求职意向
        'summary': '',        # 个人总结
        'education': [],      # 教育经历
        'internship': [],     # 实习经历
        'projects': [],       # 项目经历
        'skills': {},         # 专业技能 (dict of category -> items)
        'self_eval': [],      # 自我评价
    }

    i = 0
    # --- 姓名 (H1) ---
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('# ') and not line.startswith('## '):
            data['name'] = line[2:].strip()
            i += 1
            break
        i += 1

    # --- 个人信息行 ---
    while i < len(lines):
        line = lines[i].strip()
        if line and line.startswith('**') and ('男' in line or '女' in line):
            data['info'] = re.sub(r'\*+', '', line).strip()
            i += 1
            break
        i += 1

    # --- 求职意向行 ---
    while i < len(lines):
        line = lines[i].strip()
        if line and '求职意向' in line:
            data['job_intent'] = re.sub(r'\*+', '', line).strip()
            data['job_intent'] = data['job_intent'].replace('求职意向：', '').replace('求职意向:', '')
            i += 1
            break
        i += 1

    # --- 逐段解析 ---
    current_section = None
    current_project = None
    project_lines = []
    skill_table_rows = []

    while i < len(lines):
        line = lines[i].strip()

        # 跳过空行和分隔符
        if not line or line == '---':
            i += 1
            continue

        # H2 标题
        if line.startswith('## '):
            # 保存前一个项目
            if current_project and project_lines:
                current_project['lines'] = project_lines
                data['projects'].append(current_project)
                current_project = None
                project_lines = []

            section_title = line[3:].strip()
            current_section = section_title
            i += 1
            continue

        # H3 标题 (子项目)
        if line.startswith('### '):
            if current_project and project_lines:
                current_project['lines'] = project_lines
                data['projects'].append(current_project)

            project_title = line[4:].strip()
            current_project = {'title': project_title, 'lines': []}
            project_lines = []
            i += 1
            continue

        # 表格行
        if line.startswith('|') and current_section == '专业技能':
            skill_table_rows.append(line)
            i += 1
            continue

        # 列表项
        if line.startswith('- '):
            content = clean_md(line[2:].strip())
            if current_section == '个人总结':
                data['summary'] += content
            elif current_section == '教育经历':
                data['education'].append(content)
            elif current_section == '实习经历':
                data['internship'].append(content)
            elif current_section in ('项目经历',):
                if current_project is not None:
                    project_lines.append(content)
            elif current_section == '自我评价':
                data['self_eval'].append(content)
            i += 1
            continue

        # 粗体行（如公司名、学校名）
        if line.startswith('**'):
            clean = clean_md(line)
            if current_section == '教育经历':
                data['education'].append(clean)
            elif current_section == '实习经历':
                data['internship'].append(clean)
            elif current_section in ('项目经历',):
                if current_project is not None:
                    current_project['title'] += ' | ' + clean
            i += 1
            continue

        # 普通文本段落（非空、非列表、非标题、非表格）
        if line and not line.startswith('#') and not line.startswith('|'):
            clean = clean_md(line)
            if current_section == '个人总结':
                data['summary'] += clean
            elif current_section == '教育经历':
                data['education'].append(clean)
            elif current_section == '实习经历':
                data['internship'].append(clean)
            elif current_section == '自我评价':
                data['self_eval'].append(clean)

        i += 1

    # 保存最后一个项目
    if current_project and project_lines:
        current_project['lines'] = project_lines
        data['projects'].append(current_project)

    # --- 解析技能表格 ---
    for row in skill_table_rows:
        cols = [c.strip() for c in row.split('|') if c.strip()]
        if len(cols) >= 2 and cols[0] not in ('类别', '---', '------'):
            # 清理 markdown bold 标记
            category = re.sub(r'\*+', '', cols[0]).strip()
            abilities = re.sub(r'\*+', '', cols[1]).strip()
            data['skills'][category] = abilities

    return data


# ============================================================
# 2. 字体注册
# ============================================================

FONT_DIR = r'C:\Windows\Fonts'
FONT_YAHEI = os.path.join(FONT_DIR, 'msyh.ttc')
FONT_YAHEI_BOLD = os.path.join(FONT_DIR, 'msyhbd.ttc')
FONT_HEI = os.path.join(FONT_DIR, 'simhei.ttf')
FONT_KAI = os.path.join(FONT_DIR, 'simkai.ttf')
FONT_FANG = os.path.join(FONT_DIR, 'simfang.ttf')


def register_fonts(pdf: FPDF):
    """注册中文字体"""
    pdf.add_font('YaHei', '', FONT_YAHEI)
    pdf.add_font('YaHei', 'B', FONT_YAHEI_BOLD)
    pdf.add_font('Hei', '', FONT_HEI)
    pdf.add_font('Kai', '', FONT_KAI)
    pdf.add_font('Fang', '', FONT_FANG)


# ============================================================
# 3. 模板基类
# ============================================================

class ResumeTemplate:
    """简历模板基类"""

    def __init__(self, data: dict):
        self.data = data
        self.pdf = FPDF('P', 'mm', 'A4')
        self.pdf.set_auto_page_break(True, 15)
        register_fonts(self.pdf)
        self.pdf.set_margins(20, 10, 20)

    # ---------- 色彩方案 (子类覆盖) ----------
    @property
    def color_primary(self) -> tuple:
        raise NotImplementedError

    @property
    def color_dark(self) -> tuple:
        raise NotImplementedError

    @property
    def color_gray(self) -> tuple:
        raise NotImplementedError

    @property
    def color_light_bg(self) -> tuple:
        raise NotImplementedError

    @property
    def color_accent(self) -> tuple:
        raise NotImplementedError

    @property
    def color_divider(self) -> tuple:
        raise NotImplementedError

    # ---------- 通用绘制方法 ----------

    def section_title(self, title: str, y_offset: float = 3):
        """绘制统一的 section 标题"""
        pdf = self.pdf
        y = pdf.get_y() + y_offset

        # 左侧色块 + 标题
        pdf.set_y(y)
        pdf.set_fill_color(*self.color_primary)
        pdf.rect(20, y + 1.5, 3, 6, 'F')

        pdf.set_y(y)
        pdf.set_font('YaHei', 'B', 12)
        pdf.set_text_color(*self.color_dark)
        pdf.set_x(27)
        pdf.cell(0, 7, title, align='L')

        # 底部分隔线
        final_y = pdf.get_y() + 1
        pdf.set_draw_color(*self.color_divider)
        pdf.set_line_width(0.3)
        pdf.line(27, final_y, 190, final_y)
        pdf.set_y(final_y + 2.5)

    def bullet_text(self, text: str, indent: float = 27, width: float = 163, line_h: float = 5.5):
        """绘制 bullet 文本（自动推进 y，防止与上行重叠）"""
        pdf = self.pdf
        pdf.set_y(pdf.get_y() + 1.2)
        pdf.set_x(indent)
        pdf.set_font('YaHei', '', 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(width, line_h, text, align='L')

    def tag_badge(self, text: str, x: float, y: float, bg_color: tuple = None, text_color: tuple = None):
        """绘制小标签"""
        pdf = self.pdf
        if bg_color is None:
            bg_color = self.color_primary
        if text_color is None:
            text_color = (255, 255, 255)

        pdf.set_font('YaHei', '', 7.5)
        w = pdf.get_string_width(text) + 8
        h = 5.5
        pdf.set_fill_color(*bg_color)
        pdf.set_text_color(*text_color)
        pdf.set_xy(x, y)
        pdf.cell(w, h, text, fill=True, align='C')

    def metric_highlight(self, text: str, y_offset: float = 3):
        """高亮指标条"""
        pdf = self.pdf
        pdf.set_y(pdf.get_y() + y_offset)
        pdf.set_fill_color(*self.color_light_bg)
        pdf.set_x(27)
        pdf.set_font('YaHei', 'B', 9)
        pdf.set_text_color(*self.color_primary)
        pdf.cell(163, 7.5, f'  {text}', fill=True, align='L')
        pdf.set_y(pdf.get_y() + 9)

    # ---------- 各模块绘制 (子类可覆盖) ----------

    def draw_header(self):
        """绘制头部：姓名 + 个人信息 + 求职意向"""
        pdf = self.pdf
        data = self.data

        # 头部背景条
        pdf.set_fill_color(*self.color_light_bg)
        pdf.rect(0, 0, 210, 36, 'F')

        # 姓名
        pdf.set_y(12)
        pdf.set_font('YaHei', 'B', 22)
        pdf.set_text_color(*self.color_dark)
        pdf.cell(0, 9, data['name'], align='C')

        # 求职意向
        pdf.set_y(24)
        pdf.set_font('YaHei', '', 10)
        pdf.set_text_color(*self.color_primary)
        job_text = data.get('job_intent', '')
        if job_text:
            pdf.cell(0, 5.5, f'求职意向：{job_text}' if '求职意向' not in job_text else job_text, align='C')

        # 个人信息
        pdf.set_y(38)
        pdf.set_font('YaHei', '', 8.5)
        pdf.set_text_color(*self.color_gray)
        info = data.get('info', '')
        pdf.cell(0, 5, info, align='C')

    def draw_summary(self):
        """绘制个人总结"""
        data = self.data
        if not data.get('summary'):
            return

        self.section_title('个人总结')

        # ★ 与其他模块一致的 y 偏移，防止与标题重叠
        self.pdf.set_y(self.pdf.get_y() + 3)

        summary = data['summary'].strip()
        self.pdf.set_x(27)
        self.pdf.set_font('YaHei', '', 9)
        self.pdf.set_text_color(60, 60, 60)
        self.pdf.multi_cell(163, 5.5, summary, align='L')

    def draw_education(self):
        """绘制教育经历"""
        data = self.data
        if not data.get('education'):
            return

        self.section_title('教育经历')

        for item in data['education']:
            # 判断是否包含管道符的标题行
            if '|' in item:
                parts = [p.strip() for p in re.split(r'[|｜]', item)]
                school = parts[0] if len(parts) >= 1 else ''
                date = parts[-1] if len(parts) >= 2 else ''

                # 第一行：学校名（粗体左）+ 日期（普通右）
                self.pdf.set_y(self.pdf.get_y() + 4)
                self.pdf.set_x(27)
                self.pdf.set_font('YaHei', 'B', 10.5)
                self.pdf.set_text_color(*self.color_dark)
                self.pdf.cell(130, 6, school, align='L')
                self.pdf.set_font('YaHei', '', 9)
                self.pdf.set_text_color(*self.color_gray)
                self.pdf.cell(33, 6, date, align='R')
                # ★ cell() 不换行，手动推进到第二行
                self.pdf.set_y(self.pdf.get_y() + 7)

                # 第二行：专业 | 学历（副标题，灰色小字）
                if len(parts) >= 4:
                    subtitle = ' | '.join(parts[1:-1])
                elif len(parts) == 3:
                    subtitle = parts[1]
                else:
                    subtitle = ''
                if subtitle:
                    self.pdf.set_x(27)
                    self.pdf.set_font('YaHei', '', 9)
                    self.pdf.set_text_color(*self.color_gray)
                    self.pdf.cell(163, 5, subtitle, align='L')
                    self.pdf.set_y(self.pdf.get_y() + 5.5)
            else:
                self.bullet_text(item)

    def draw_internship(self):
        """绘制实习经历"""
        data = self.data
        if not data.get('internship'):
            return

        self.section_title('实习经历')

        for item in data['internship']:
            # 判断是否为包含管道符的标题行（公司 | 职位 | 日期）
            if '|' in item:
                parts = [p.strip() for p in re.split(r'[|｜]', item)]
                company = parts[0] if len(parts) >= 1 else ''
                date = parts[-1] if len(parts) >= 2 else ''

                # 第一行：公司名（粗体左）+ 日期（普通右）
                self.pdf.set_y(self.pdf.get_y() + 4)
                self.pdf.set_x(27)
                self.pdf.set_font('YaHei', 'B', 10.5)
                self.pdf.set_text_color(*self.color_dark)
                self.pdf.cell(130, 6, company, align='L')
                self.pdf.set_font('YaHei', '', 9)
                self.pdf.set_text_color(*self.color_gray)
                self.pdf.cell(33, 6, date, align='R')
                # ★ cell() 不换行，手动推进到第二行
                self.pdf.set_y(self.pdf.get_y() + 7)

                # 第二行：职位/方向（副标题，灰色小字）
                if len(parts) >= 3:
                    subtitle = ' | '.join(parts[1:-1])
                elif len(parts) == 2:
                    subtitle = parts[1]
                else:
                    subtitle = ''
                if subtitle:
                    self.pdf.set_x(27)
                    self.pdf.set_font('YaHei', '', 9)
                    self.pdf.set_text_color(*self.color_gray)
                    self.pdf.cell(163, 5, subtitle, align='L')
                    self.pdf.set_y(self.pdf.get_y() + 5.5)
            else:
                self.bullet_text(item)

    def draw_projects(self):
        """绘制项目经历"""
        data = self.data
        if not data.get('projects'):
            return

        self.section_title('项目经历')

        for proj in data['projects']:
            # 项目标题（粗体）
            self.pdf.set_y(self.pdf.get_y() + 3)
            self.pdf.set_x(27)
            self.pdf.set_font('YaHei', 'B', 10.5)
            self.pdf.set_text_color(*self.color_dark)

            title = proj.get('title', '')
            title = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', title)
            self.pdf.cell(0, 6, title, align='L')
            # ★ cell() 不会自动换行，手动推进 y
            self.pdf.set_y(self.pdf.get_y() + 6.5)

            # 项目内容
            for line in proj.get('lines', []):
                self.bullet_text(clean_md(line))

            # 项目间间距
            self.pdf.set_y(self.pdf.get_y() + 2)

    def draw_skills(self):
        """绘制专业技能 — 类别标签 + 内容分行，确保不重叠"""
        data = self.data
        if not data.get('skills'):
            return

        self.section_title('专业技能')

        for category, abilities in data['skills'].items():
            pdf = self.pdf

            # 类别标签（粗体带颜色，独立一行）
            pdf.set_y(pdf.get_y() + 2.5)
            pdf.set_x(27)
            pdf.set_font('YaHei', 'B', 9.5)
            pdf.set_text_color(*self.color_primary)
            pdf.cell(0, 5.5, category, align='L')
            # ★ cell() 不换行，手动推进 y
            pdf.set_y(pdf.get_y() + 6)

            # 内容（下一行，普通字体）
            pdf.set_x(27)
            pdf.set_font('YaHei', '', 9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(163, 5.5, abilities, align='L')
            pdf.set_y(pdf.get_y() + 1)

    def draw_self_eval(self):
        """绘制自我评价"""
        data = self.data
        if not data.get('self_eval'):
            return

        self.section_title('自我评价')

        for item in data['self_eval']:
            self.pdf.set_y(self.pdf.get_y() + 2.5)
            text = clean_md(item).lstrip('- ').strip()
            self.bullet_text(text)

    def draw_footer(self):
        """绘制页脚"""
        pdf = self.pdf
        pdf.set_y(pdf.get_y() + 4)
        pdf.set_draw_color(*self.color_divider)
        pdf.set_line_width(0.3)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.set_y(pdf.get_y() + 3)
        pdf.set_font('YaHei', '', 7.5)
        pdf.set_text_color(170, 170, 170)
        pdf.cell(0, 5, '感谢您花时间阅读我的简历，期待与您进一步交流！', align='C')

    # ---------- 主流程 ----------

    def build(self, output_path: str):
        """构建完整 PDF"""
        pdf = self.pdf
        pdf.add_page()

        self.draw_header()
        self.draw_summary()
        self.draw_education()
        self.draw_internship()
        self.draw_projects()
        self.draw_skills()
        self.draw_self_eval()
        self.draw_footer()

        pdf.output(output_path)
        print(f'  [OK] {output_path}')
        return output_path


# ============================================================
# 4. 模板样式一：互联网蓝 (BOSS直聘风格)
# ============================================================

class InternetBlueTemplate(ResumeTemplate):
    """BOSS直聘 / 拉勾风格 — 清爽蓝白，强调数据指标"""

    @property
    def color_primary(self):   return (23, 119, 255)     # #1777FF
    @property
    def color_dark(self):      return (33, 33, 33)       # #212121
    @property
    def color_gray(self):      return (128, 128, 128)    # #808080
    @property
    def color_light_bg(self):  return (240, 247, 255)    # #F0F7FF
    @property
    def color_accent(self):    return (255, 140, 0)      # #FF8C00
    @property
    def color_divider(self):   return (220, 230, 240)    # #DCE6F0


# ============================================================
# 5. 模板样式二：商务深灰 (猎聘风格)
# ============================================================

class BusinessDarkTemplate(ResumeTemplate):
    """猎聘 / 前程无忧风格 — 深色稳重，专业商务感"""

    @property
    def color_primary(self):   return (45, 52, 54)       # #2d3436
    @property
    def color_dark(self):      return (30, 30, 30)       # #1e1e1e
    @property
    def color_gray(self):      return (108, 117, 125)    # #6c757d
    @property
    def color_light_bg(self):  return (245, 246, 248)    # #F5F6F8
    @property
    def color_accent(self):    return (9, 132, 227)      # #0984e3
    @property
    def color_divider(self):   return (210, 215, 220)    # #D2D7DC

    def draw_header(self):
        """商务风头部 — 全宽深色背景条"""
        pdf = self.pdf
        data = self.data

        # 深色头部背景
        pdf.set_fill_color(*self.color_primary)
        pdf.rect(0, 0, 210, 38, 'F')

        # 姓名
        pdf.set_y(13)
        pdf.set_font('YaHei', 'B', 23)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 9, data['name'], align='C')

        # 求职意向
        pdf.set_y(25)
        pdf.set_font('YaHei', '', 10)
        pdf.set_text_color(200, 210, 220)
        job_text = data.get('job_intent', '')
        if job_text:
            pdf.cell(0, 5.5, job_text, align='C')

        # 个人信息 (头部下方)
        pdf.set_y(40)
        pdf.set_font('YaHei', '', 8.5)
        pdf.set_text_color(*self.color_gray)
        info = data.get('info', '')
        pdf.cell(0, 5, info, align='C')

    def section_title(self, title: str, y_offset: float = 3):
        """商务风 section 标题 — 顶部双线"""
        pdf = self.pdf
        y = pdf.get_y() + y_offset

        # 上细线
        pdf.set_draw_color(*self.color_divider)
        pdf.set_line_width(0.2)
        pdf.line(20, y, 190, y)

        # 标题
        pdf.set_y(y + 3)
        pdf.set_font('YaHei', 'B', 12)
        pdf.set_text_color(*self.color_primary)
        pdf.set_x(22)
        pdf.cell(0, 7, title.upper(), align='L')

        # 下粗线
        final_y = pdf.get_y() + 1
        pdf.set_draw_color(*self.color_primary)
        pdf.set_line_width(0.8)
        pdf.line(22, final_y, 70, final_y)
        pdf.set_y(final_y + 2.5)

    def metric_highlight(self, text: str, y_offset: float = 3):
        """商务风高亮 — 左侧边框条"""
        pdf = self.pdf
        pdf.set_y(pdf.get_y() + y_offset)
        pdf.set_fill_color(*self.color_light_bg)
        pdf.set_x(27)
        # 左侧 accent 色条
        pdf.set_draw_color(*self.color_accent)
        pdf.set_line_width(2)
        pdf.line(27, pdf.get_y() + 1, 27, pdf.get_y() + 7.5)
        pdf.set_font('YaHei', 'B', 9)
        pdf.set_text_color(*self.color_accent)
        pdf.set_x(31)
        pdf.cell(159, 7.5, text, fill=True, align='L')
        pdf.set_y(pdf.get_y() + 9)


# ============================================================
# 6. 模板样式三：现代卡片风 (超级简历/Canva风格)
# ============================================================

class ModernTealTemplate(ResumeTemplate):
    """超级简历 / Canva 风格 — 卡片圆角、青绿色调、信息层级清晰"""

    @property
    def color_primary(self):   return (13, 148, 136)     # #0d9488
    @property
    def color_dark(self):      return (30, 41, 59)       # #1e293b
    @property
    def color_gray(self):      return (100, 116, 139)    # #64748b
    @property
    def color_light_bg(self):  return (240, 253, 250)    # #F0FDFA
    @property
    def color_accent(self):    return (245, 158, 11)     # #F59E0B
    @property
    def color_divider(self):   return (203, 213, 225)    # #CBD5E1

    def draw_header(self):
        """卡片风头部 — 居中布局 + 底部色条"""
        pdf = self.pdf
        data = self.data

        # 顶部色条
        pdf.set_fill_color(*self.color_primary)
        pdf.rect(0, 0, 210, 3, 'F')

        # 姓名 (大字间距)
        pdf.set_y(13)
        pdf.set_font('YaHei', 'B', 23)
        pdf.set_text_color(*self.color_dark)
        pdf.cell(0, 9, data['name'], align='C')

        # 求职意向 + badge
        pdf.set_y(25)
        pdf.set_font('YaHei', '', 10)
        pdf.set_text_color(*self.color_primary)
        job_text = data.get('job_intent', '')
        pdf.cell(0, 5.5, job_text, align='C')

        # 个人信息
        pdf.set_y(40)
        pdf.set_font('YaHei', '', 8.5)
        pdf.set_text_color(*self.color_gray)
        info = data.get('info', '')
        pdf.cell(0, 5, info, align='C')

        # 底部分隔
        pdf.set_y(47)
        pdf.set_draw_color(*self.color_divider)
        pdf.set_line_width(0.3)
        pdf.line(30, pdf.get_y(), 180, pdf.get_y())

    def section_title(self, title: str, y_offset: float = 3):
        """卡片风 section 标题 — icon风格"""
        pdf = self.pdf
        y = pdf.get_y() + y_offset

        pdf.set_y(y)
        pdf.set_font('YaHei', 'B', 12)
        pdf.set_text_color(*self.color_dark)
        pdf.set_x(30)
        pdf.cell(0, 7, title, align='L')

        # 底部细线
        final_y = pdf.get_y() + 1
        pdf.set_draw_color(*self.color_divider)
        pdf.set_line_width(0.3)
        pdf.line(30, final_y, 190, final_y)
        pdf.set_y(final_y + 2.5)

    def metric_highlight(self, text: str, y_offset: float = 3):
        """卡片风高亮 — 圆角风格"""
        pdf = self.pdf
        pdf.set_y(pdf.get_y() + y_offset)
        pdf.set_fill_color(*self.color_light_bg)
        pdf.set_draw_color(*self.color_primary)
        pdf.set_line_width(0.3)
        # 模拟圆角矩形
        x, y, w, h = 27, pdf.get_y(), 163, 7.5
        pdf.rect(x, y, w, h, 'DF')
        pdf.set_font('YaHei', 'B', 9)
        pdf.set_text_color(*self.color_primary)
        pdf.set_xy(x + 3, y + 0.5)
        pdf.cell(w - 6, h - 1, text, align='C')
        pdf.set_y(y + h + 8)

    def draw_skills(self):
        """卡片风技能 — 标签式布局，防止重叠"""
        data = self.data
        if not data.get('skills'):
            return

        self.section_title('专业技能')

        for category, abilities in data['skills'].items():
            pdf = self.pdf

            # 标签（彩色小徽章，粗体白字）
            pdf.set_y(pdf.get_y() + 2.5)
            pdf.set_x(27)
            pdf.set_fill_color(*self.color_primary)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('YaHei', 'B', 8.5)
            cat_w = pdf.get_string_width(f' {category} ') + 2
            pdf.cell(cat_w, 5.5, f' {category} ', fill=True, align='C')
            # ★ cell() 不换行，手动推进 y
            pdf.set_y(pdf.get_y() + 6)

            # 内容（标签下方，普通字体）
            pdf.set_x(27)
            pdf.set_font('YaHei', '', 9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(163, 5.5, abilities, align='L')
            pdf.set_y(pdf.get_y() + 1)


# ============================================================
# 7. 主程序
# ============================================================

TEMPLATES = {
    'internet': ('互联网蓝', InternetBlueTemplate, '张冬阳_简历_互联网蓝.pdf'),
    'business': ('商务灰', BusinessDarkTemplate, '张冬阳_简历_商务灰.pdf'),
    'modern':   ('现代绿', ModernTealTemplate, '张冬阳_简历_现代卡片风.pdf'),
}


def main():
    parser = argparse.ArgumentParser(description='简历 PDF 生成器 — 多模板样式')
    parser.add_argument('--style', '-s', choices=['internet', 'business', 'modern', 'all'],
                        default='all', help='选择模板风格 (默认: all)')
    parser.add_argument('--input', '-i',
                        default=r'd:\xiangmu\JIANLI\张冬阳-通用简历-PM-AIPM.md',
                        help='Markdown 简历文件路径')
    parser.add_argument('--outdir', '-o',
                        default=r'd:\xiangmu\JIANLI',
                        help='输出目录')
    parser.add_argument('--validate', '-v', action='store_true',
                        help='生成后自动校验 PDF 排版')
    parser.add_argument('--no-validate', action='store_true',
                        help='跳过自动校验')
    args = parser.parse_args()

    print('=' * 60)
    print('  简历 PDF 生成器 v2 — 多模板样式')
    print('=' * 60)

    # 解析简历
    print(f'\n[1] 解析简历: {args.input}')
    data = parse_markdown_resume(args.input)

    print(f'    姓名: {data["name"]}')
    print(f'    项目经历: {len(data["projects"])} 个')
    print(f'    技能类别: {len(data["skills"])} 类')
    print(f'    自我评价: {len(data["self_eval"])} 条')

    # 选择模板
    if args.style == 'all':
        selected = TEMPLATES
    else:
        selected = {args.style: TEMPLATES[args.style]}

    # 生成 PDF
    generated_files = []
    print(f'\n[2] 生成 PDF ({len(selected)} 套模板)...\n')
    for key, (name, template_cls, filename) in selected.items():
        output_path = os.path.join(args.outdir, filename)
        print(f'  [{name}] 正在生成...')
        template = template_cls(data)
        template.build(output_path)
        generated_files.append(output_path)

    print(f'\n{"=" * 60}')
    print(f'  完成！共生成 {len(selected)} 份简历 PDF')
    print(f'  输出目录: {args.outdir}')
    print(f'{"=" * 60}')

    # 自动校验
    if args.validate or (not args.no_validate):
        print(f'\n[3] 自动校验 PDF 排版...')
        try:
            from validate_resume_pdf import validate_pdf, print_result as print_val
            all_passed = True
            for fpath in generated_files:
                result = validate_pdf(fpath)
                print_val(result)
                if not result.get("passed"):
                    all_passed = False

            if all_passed:
                print(f'\n  所有 PDF 校验通过！')
            else:
                print(f'\n  存在排版错误，请检查上述报告并修复 generate_resume_pdf_v2.py')
                sys.exit(1)
        except ImportError:
            print(f'  [跳过] PyMuPDF (fitz) 未安装，无法自动校验')
            print(f'  安装: pip install PyMuPDF')
        except Exception as e:
            print(f'  [警告] 校验过程出错: {e}')


if __name__ == '__main__':
    main()
