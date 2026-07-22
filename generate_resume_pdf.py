#!/usr/bin/env python3
"""
生成张冬阳的简历 PDF — 仿 BOSS 直聘招聘软件模版格式
结构：个人优势 → AI项目经历 → 实习经历 → 教育背景 → 技能专长
"""

from fpdf import FPDF
import os

class ChinesePDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'A4')
        font_dir = r'C:\Windows\Fonts'
        self.add_font('YaHei', '', os.path.join(font_dir, 'msyh.ttc'))
        self.add_font('YaHei', 'B', os.path.join(font_dir, 'msyhbd.ttc'))
        self.add_font('SimHei', '', os.path.join(font_dir, 'simhei.ttf'))
        self.set_auto_page_break(True, 15)

    def header(self):
        pass

    def footer(self):
        pass


def draw_section_line(pdf, y):
    pdf.set_draw_color(0, 120, 210)
    pdf.set_line_width(0.6)
    pdf.line(20, y, 190, y)


def draw_thin_line(pdf, y):
    pdf.set_draw_color(220, 220, 220)
    pdf.set_line_width(0.2)
    pdf.line(20, y, 190, y)


def section_header(pdf, title):
    """统一的模块标题 (与上方内容留足间距)"""
    curr_y = pdf.get_y() + 6
    draw_section_line(pdf, curr_y)
    pdf.set_y(curr_y + 5)
    pdf.set_font('YaHei', 'B', 13)
    pdf.set_text_color(0, 120, 210)
    pdf.cell(0, 7, title, align='L')


def project_subtitle_row(pdf, subtitle, tag, tag_color=(16, 185, 129)):
    """项目副标题行：项目名 + 标签"""
    pdf.set_font('YaHei', 'B', 10.5)
    pdf.set_text_color(33, 33, 33)
    pdf.set_x(22)
    pdf.cell(120, 6, subtitle, align='L')
    # 标签
    pdf.set_font('YaHei', '', 8.5)
    pdf.set_text_color(*tag_color)
    pdf.cell(50, 6, tag, align='R')


def bullet_lines(pdf, lines):
    """通用bullet列表"""
    pdf.set_font('YaHei', '', 9.5)
    pdf.set_text_color(60, 60, 60)
    for line in lines:
        pdf.set_y(pdf.get_y() + 6)
        pdf.set_x(26)
        pdf.multi_cell(164, 5.5, line, align='L')


def highlight_bar(pdf, text):
    """蓝色成果高亮条"""
    pdf.set_y(pdf.get_y() + 2)
    pdf.set_fill_color(240, 247, 255)
    pdf.set_x(26)
    pdf.set_font('YaHei', 'B', 9.5)
    pdf.set_text_color(0, 120, 210)
    pdf.cell(164, 7, text, fill=True, align='C')
    pdf.set_y(pdf.get_y() + 9)  # 高亮条后留足间距


def build_resume():
    pdf = ChinesePDF()
    pdf.set_margins(20, 12, 20)

    PRIMARY = (0, 120, 210)
    DARK = (33, 33, 33)
    GRAY = (102, 102, 102)
    GREEN_TAG = (16, 185, 129)
    ORANGE_TAG = (255, 140, 0)

    # ==================== PAGE 1 ====================
    pdf.add_page()

    # ----- 头部 -----
    pdf.set_fill_color(245, 248, 252)
    pdf.rect(0, 0, 210, 38, 'F')

    pdf.set_y(14)
    pdf.set_font('YaHei', 'B', 22)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 10, '张 冬 阳', align='C')

    pdf.set_y(28)
    pdf.set_font('YaHei', '', 11)
    pdf.set_text_color(*PRIMARY)
    pdf.cell(0, 6, '求职意向：AI Agent 产品经理', align='C')

    pdf.set_y(41)
    pdf.set_font('YaHei', '', 9.5)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 6, '北京  |  计算机科学与技术 · 本科 · 2026 届  |  电话 / 邮箱请填写', align='C')

    # ===== 个人优势 =====
    pdf.set_y(54)
    section_header(pdf, '▎个人优势')

    pdf.set_y(pdf.get_y() + 8)
    pdf.set_font('YaHei', '', 10)
    pdf.set_text_color(*DARK)
    pdf.set_x(22)

    advantage_text = (
        "计算机科学与技术专业背景，对 AI 技术有强烈热情与持续学习习惯。实习期间发现内容生产效率瓶颈后，"
        "自学 LLM / RAG / Agent 技术栈，利用业余时间独立从 0 到 1 完成 2 个 AI 产品项目："
        "电商内容生成 Agent 工作流（生产效率 ↑60%、素材采纳率 ↑30pp）与 RAG 智能知识库问答助手（查询效率 ↑10x、准确率 88%）。"
        "擅长用户行为分析与 A/B 实验驱动产品迭代，深度掌握 Prompt 工程、Agent 工作流设计与模型边界评估。"
        "具备高价值场景挖掘与跨角色协同推动产品落地的完整闭环能力，渴望在 AI Agent 方向持续深耕。"
    )
    pdf.multi_cell(170, 6, advantage_text, align='J')

    # ===== AI 项目经历 (C位) =====
    section_header(pdf, '▎AI 项目经历')

    # --- 项目一 ---
    pdf.set_y(pdf.get_y() + 9)
    project_subtitle_row(pdf,
        '● 电商内容生成 Agent — 智能体工作流从 0 到 1',
        '个人项目', GREEN_TAG)

    proj1_lines = [
        "• 发现电商内容生产中人工设计效率低、素材风格不一致的痛点，独立完成需求调研、PRD 撰写与交互流程设计",
        "• 设计 Agent 工作流（意图识别 → 参数提取 → 多模型调度生图 → 自动质检 → 输出），通过 15+ 版 Prompt A/B 实验验证，持续优化生成质量",
        "• 搭建「生成 → 人工反馈 → 模型调优」数据闭环，定义任务成功率、素材采纳率、人均产能作为核心追踪指标",
    ]
    bullet_lines(pdf, proj1_lines)
    highlight_bar(pdf, '生产效率 ↑60%  |  采纳率 45% → 75%  |  日均产出 300+ 素材')

    # --- 项目二 ---
    pdf.set_y(pdf.get_y() + 10)
    project_subtitle_row(pdf,
        '● RAG 智能知识库问答系统 — AI 助手产品落地',
        '个人项目', GREEN_TAG)

    proj2_lines = [
        "• 洞察企业内部知识检索效率低下的痛点，主导产品方向与技术选型：文档解析 → jieba 分词 → TF-IDF 向量检索 → 余弦相似度 Top-K 召回 → 大模型生成回答",
        "• 深度理解 LLM 原理与模型边界，对接评测 DeepSeek / 通义千问 / Claude 三种主流大模型的输出质量，产出模型选型评估报告",
        "• 设计多轮对话交互流程（上下文追问 + 答案溯源原文片段），提升用户信任度与使用粘性",
        "• 借助 AI 编程工具高效完成系统开发，通过用户行为分析（查询频次、满意度、采纳率）持续优化检索策略与 Prompt 模板",
    ]
    bullet_lines(pdf, proj2_lines)
    highlight_bar(pdf, '查询耗时 20min → 2min（效率 ↑10x）  |  准确率 88%  |  周活覆盖 80%+ 使用场景')

    # ===== 实习经历 =====
    section_header(pdf, '▎实习经历')

    pdf.set_y(pdf.get_y() + 9)
    pdf.set_font('YaHei', 'B', 11)
    pdf.set_text_color(*DARK)
    pdf.set_x(22)
    pdf.cell(125, 6, '美域高（北京）咨询顾问有限公司', align='L')
    pdf.set_font('YaHei', '', 10)
    pdf.set_text_color(*GRAY)
    pdf.cell(45, 6, '新媒体运营', align='R')

    pdf.set_y(pdf.get_y() + 6)
    pdf.set_x(22)
    pdf.set_font('YaHei', '', 9)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, '2025.10 – 2026.01（4 个月）', align='L')

    intern_lines = [
        "• 负责公司新媒体矩阵的日常内容策划与运营，熟练运用数据分析工具追踪播放量、完播率、互动转化等核心指标",
        "• 主动引入 AI 工具辅助内容生产，利用大模型完成视频脚本自动生成与短视频智能剪辑，将单条视频制作周期从 3 天压缩至 1 天以内",
        "• 这段实习经历让我深入理解了内容生产 pipeline 的效率瓶颈，激发了我对 AI 驱动内容自动化的强烈兴趣，进而自学 Agent/RAG 技术栈并完成了上述 2 个 AI 产品项目",
    ]
    bullet_lines(pdf, intern_lines)

    # ===== 教育背景 =====
    section_header(pdf, '▎教育背景')

    pdf.set_y(pdf.get_y() + 9)
    pdf.set_font('YaHei', 'B', 11)
    pdf.set_text_color(*DARK)
    pdf.set_x(22)
    pdf.cell(130, 6, '大连工业大学艺术与信息工程学院', align='L')
    pdf.set_font('YaHei', '', 10)
    pdf.set_text_color(*GRAY)
    pdf.cell(40, 6, '2022.09 – 2026.06', align='R')

    edu_lines = [
        "• 计算机科学与技术 · 本科  |  核心课程：数据结构与算法、机器学习导论、NLP、数据库原理、软件工程",
        "• 在校期间自学 LLM / RAG / Agent 技术栈，独立完成 2 个 AI 产品项目",
        "• 毕业设计：《短视频素材管理与智能分发平台》— 基于 Spring Boot 全栈开发，涵盖素材标签体系、检索引擎与用户行为追踪模块",
    ]
    bullet_lines(pdf, edu_lines)

    # ===== 技能专长 =====
    section_header(pdf, '▎技能专长')

    pdf.set_y(pdf.get_y() + 8)
    skills = [
        ('AI/LLM',   'Prompt 工程 · RAG 架构 · Agent 工作流设计 · 熟悉 DeepSeek / 通义千问 / Claude 模型能力与边界'),
        ('编程语言',  'Python · Java · SQL'),
        ('产品工具',  'PRD 撰写 · 交互流程设计 · A/B 实验设计 · 指标体系搭建 · Figma · 墨刀 · XMind'),
        ('开发框架',  'Spring Boot · Vue.js · MySQL · Redis'),
        ('AI 实战',   'AI 辅助开发（借助大模型完成从技术选型到代码实现，具备 AI Native 产品构建能力）'),
    ]

    for label, content in skills:
        pdf.set_x(22)
        pdf.set_font('YaHei', 'B', 9.5)
        pdf.set_text_color(*PRIMARY)
        label_w = pdf.get_string_width(label) + 6
        pdf.cell(label_w, 6, label, align='L')
        pdf.set_font('YaHei', '', 9.5)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(170 - label_w, 6, content, align='L')
        pdf.set_y(pdf.get_y() + 1.5)

    # ===== 底部 =====
    pdf.set_y(pdf.get_y() + 6)
    draw_thin_line(pdf, pdf.get_y())
    pdf.set_y(pdf.get_y() + 3)
    pdf.set_font('YaHei', '', 8)
    pdf.set_text_color(180, 180, 180)
    pdf.cell(0, 5, '感谢您花时间阅读我的简历，期待与您进一步交流！', align='C')

    # ===== 保存 =====
    output_path = r'd:\xiangmu\JIANLI\张冬阳_AI产品经理_简历_v3.pdf'
    pdf.output(output_path)
    print(f'[OK] PDF resume generated: {output_path}')
    return output_path


if __name__ == '__main__':
    build_resume()
