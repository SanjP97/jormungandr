"""
jormungandr PDF Report Generator — Jormungandr-Inspired Dark Theme

Generates professional, visually striking PDF reports styled after the Jormungandr
LLM Benchmark website (https://jormungandr.giskard.ai/). Uses a dark background
with teal/green accent colors, card-based layouts, and clean data tables.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Wedge, Line
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.spider import SpiderChart
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.colors import HexColor, Color
from datetime import datetime
import math
from typing import Dict, Any, List, Tuple
from jormungandr.utils.logger import get_logger

logger = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — Jormungandr-Inspired Dark Theme
# ═══════════════════════════════════════════════════════════════════════

class JormungandrColors:
    """Color palette inspired by jormungandr.giskard.ai"""
    # Backgrounds
    BG_DARK = HexColor('#121220')        # Page background
    BG_CARD = HexColor('#1B1B30')        # Card/panel background
    BG_CARD_ALT = HexColor('#222240')    # Alternate card background
    BG_HEADER = HexColor('#0D0D1A')      # Header bar background

    # Accent colors (Jormungandr teal/green gradient)
    TEAL = HexColor('#00B4D8')           # Primary accent
    GREEN = HexColor('#06D6A0')          # Success / high scores
    TEAL_DARK = HexColor('#0077B6')      # Darker teal

    # Status colors
    DANGER = HexColor('#E63946')         # Failure / critical
    WARNING = HexColor('#FFB703')        # Partial / medium
    SUCCESS = HexColor('#06D6A0')        # Pass / good

    # Text
    TEXT_PRIMARY = HexColor('#E8E8F0')   # Main text (off-white)
    TEXT_SECONDARY = HexColor('#9090B0') # Secondary/muted text
    TEXT_DARK = HexColor('#121220')      # Dark text on light backgrounds

    # Borders and lines
    BORDER = HexColor('#2A2A45')         # Subtle borders
    DIVIDER = HexColor('#3A3A55')        # Divider lines

    # Score-based gradient
    @staticmethod
    def score_color(score: float) -> HexColor:
        """Get color based on score value (0-100)"""
        if score >= 80:
            return JormungandrColors.GREEN
        elif score >= 60:
            return JormungandrColors.WARNING
        else:
            return JormungandrColors.DANGER

    @staticmethod
    def score_bg(score: float) -> HexColor:
        """Get a muted background tint for score"""
        if score >= 80:
            return HexColor('#0A2E20')
        elif score >= 60:
            return HexColor('#2E2A0A')
        else:
            return HexColor('#2E0A10')


class JormungandrFonts:
    """Typography constants"""
    TITLE = 28
    H1 = 20
    H2 = 15
    H3 = 12
    BODY = 10
    CAPTION = 8
    SMALL = 7
    SCORE_LARGE = 28
    SCORE_MEDIUM = 18


# ═══════════════════════════════════════════════════════════════════════
# PDF GENERATOR CLASS
# ═══════════════════════════════════════════════════════════════════════

class PDFGenerator:
    """Generate professional PDF reports with Jormungandr-inspired dark theme"""

    def __init__(self, output_path: str):
        self.output_path = output_path
        self.page_width, self.page_height = letter
        self.margin = 0.6 * inch
        self.content_width = self.page_width - 2 * self.margin
        self.doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=0.5 * inch,
        )
        self.styles = self._create_styles()
        self.elements = []

    # ── Styles ──────────────────────────────────────────────────────

    def _create_styles(self) -> dict:
        """Create all paragraph styles for the dark theme"""
        base = getSampleStyleSheet()
        styles = {}

        styles['title'] = ParagraphStyle(
            'JormungandrTitle', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=JormungandrFonts.TITLE,
            textColor=JormungandrColors.TEXT_PRIMARY, alignment=TA_CENTER,
            spaceAfter=20, leading=36
        )
        styles['subtitle'] = ParagraphStyle(
            'JormungandrSubtitle', parent=base['Normal'],
            fontName='Helvetica', fontSize=JormungandrFonts.H2,
            textColor=JormungandrColors.TEAL, alignment=TA_CENTER,
            spaceAfter=12, leading=20
        )
        styles['h1'] = ParagraphStyle(
            'JormungandrH1', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=JormungandrFonts.H1,
            textColor=JormungandrColors.TEXT_PRIMARY, alignment=TA_LEFT,
            spaceBefore=16, spaceAfter=10
        )
        styles['h2'] = ParagraphStyle(
            'JormungandrH2', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=JormungandrFonts.H2,
            textColor=JormungandrColors.TEAL, alignment=TA_LEFT,
            spaceBefore=12, spaceAfter=8
        )
        styles['h3'] = ParagraphStyle(
            'JormungandrH3', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=JormungandrFonts.H3,
            textColor=JormungandrColors.TEXT_PRIMARY, alignment=TA_LEFT,
            spaceBefore=8, spaceAfter=6
        )
        styles['body'] = ParagraphStyle(
            'JormungandrBody', parent=base['Normal'],
            fontName='Helvetica', fontSize=JormungandrFonts.BODY,
            textColor=JormungandrColors.TEXT_SECONDARY, alignment=TA_LEFT,
            spaceAfter=6, leading=14
        )
        styles['body_light'] = ParagraphStyle(
            'JormungandrBodyLight', parent=base['Normal'],
            fontName='Helvetica', fontSize=JormungandrFonts.BODY,
            textColor=JormungandrColors.TEXT_PRIMARY, alignment=TA_LEFT,
            spaceAfter=4, leading=14
        )
        styles['caption'] = ParagraphStyle(
            'JormungandrCaption', parent=base['Normal'],
            fontName='Helvetica', fontSize=JormungandrFonts.CAPTION,
            textColor=JormungandrColors.TEXT_SECONDARY, alignment=TA_LEFT,
            spaceAfter=4
        )
        styles['center'] = ParagraphStyle(
            'JormungandrCenter', parent=base['Normal'],
            fontName='Helvetica', fontSize=JormungandrFonts.BODY,
            textColor=JormungandrColors.TEXT_SECONDARY, alignment=TA_CENTER,
            spaceAfter=6
        )
        styles['score_big'] = ParagraphStyle(
            'JormungandrScoreBig', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=JormungandrFonts.SCORE_LARGE,
            textColor=JormungandrColors.TEXT_PRIMARY, alignment=TA_CENTER,
            spaceAfter=0
        )

        return styles

    # ── Page Background ─────────────────────────────────────────────

    def _draw_page_bg(self, canvas, doc):
        """Draw dark background and footer on every page"""
        canvas.saveState()
        # Full-page dark background
        canvas.setFillColor(JormungandrColors.BG_DARK)
        canvas.rect(0, 0, self.page_width, self.page_height, fill=1, stroke=0)

        # Footer line
        footer_y = 0.4 * inch
        canvas.setStrokeColor(JormungandrColors.BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(self.margin, footer_y, self.page_width - self.margin, footer_y)

        # Footer text
        canvas.setFillColor(JormungandrColors.TEXT_SECONDARY)
        canvas.setFont('Helvetica', 7)
        canvas.drawString(self.margin, footer_y - 12,
                          f"jormungandr Security Assessment Report")
        canvas.drawRightString(self.page_width - self.margin, footer_y - 12,
                               f"Page {doc.page}")
        canvas.restoreState()

    # ── Card / Panel Drawing Helpers ────────────────────────────────

    def _card_table(self, data, col_widths=None, header=True,
                    row_colors=True) -> Table:
        """Create a styled dark-theme table (card-like)"""
        if col_widths:
            t = Table(data, colWidths=col_widths)
        else:
            t = Table(data)

        style_cmds = [
            # Global
            ('BACKGROUND', (0, 0), (-1, -1), JormungandrColors.BG_CARD),
            ('TEXTCOLOR', (0, 0), (-1, -1), JormungandrColors.TEXT_PRIMARY),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            # Outer border
            ('BOX', (0, 0), (-1, -1), 0.5, JormungandrColors.BORDER),
            ('LINEBELOW', (0, 0), (-1, -2), 0.25, JormungandrColors.BORDER),
            # Rounded corners (simulated with box)
            ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ]

        if header and len(data) > 1:
            style_cmds.extend([
                ('BACKGROUND', (0, 0), (-1, 0), JormungandrColors.BG_HEADER),
                ('TEXTCOLOR', (0, 0), (-1, 0), JormungandrColors.TEAL),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('LINEBELOW', (0, 0), (-1, 0), 1, JormungandrColors.TEAL),
            ])

        if row_colors and len(data) > 2:
            for i in range(2, len(data), 2):
                style_cmds.append(
                    ('BACKGROUND', (0, i), (-1, i), JormungandrColors.BG_CARD_ALT)
                )

        t.setStyle(TableStyle(style_cmds))
        return t

    def _score_pill(self, score: float) -> str:
        """Create an inline colored score display using Paragraph markup"""
        color = JormungandrColors.score_color(score)
        hex_col = color.hexval() if hasattr(color, 'hexval') else '#06D6A0'
        # Get hex string properly
        r = int(color.red * 255)
        g = int(color.green * 255)
        b = int(color.blue * 255)
        hex_str = f'#{r:02X}{g:02X}{b:02X}'
        return f'<font color="{hex_str}"><b>{score:.1f}%</b></font>'

    def _status_badge(self, score: float) -> str:
        """Status text with color based on score"""
        if score >= 80:
            return '<font color="#06D6A0"><b>PASS</b></font>'
        elif score >= 60:
            return '<font color="#FFB703"><b>WARNING</b></font>'
        else:
            return '<font color="#E63946"><b>FAIL</b></font>'

    def _result_badge(self, result: str) -> str:
        """Badge for pass/fail result"""
        if result == 'pass':
            return '<font color="#06D6A0"><b>PASS</b></font>'
        else:
            return '<font color="#E63946"><b>FAIL</b></font>'

    # ── Chart Helpers ───────────────────────────────────────────────

    def _create_donut_chart(self, score: float, size: float = 200) -> Drawing:
        """Create a donut/ring score chart using concentric circles"""
        d = Drawing(size, size)

        cx, cy = size / 2, size / 2
        outer_r = size * 0.42
        inner_r = size * 0.28
        color = JormungandrColors.score_color(score)

        # Background circle (the full ring background)
        d.add(Circle(cx, cy, outer_r,
                     fillColor=JormungandrColors.BG_CARD_ALT,
                     strokeColor=None))

        # Score arc (standard Wedge, not annular)
        score_angle = score * 3.6  # 0-100 → 0-360
        if score_angle > 0:
            # Clamp to 359.9 to avoid polygon bug at exactly 360
            clamped = min(score_angle, 359.9)
            d.add(Wedge(cx, cy, outer_r, 90, 90 + clamped,
                        fillColor=color,
                        strokeColor=None, strokeWidth=0))

        # Inner circle (punch out the donut hole)
        d.add(Circle(cx, cy, inner_r,
                     fillColor=JormungandrColors.BG_DARK,
                     strokeColor=None))

        # Score text
        d.add(String(cx, cy + 8, f'{score:.0f}',
                      fontName='Helvetica-Bold', fontSize=32,
                      fillColor=JormungandrColors.TEXT_PRIMARY,
                      textAnchor='middle'))
        d.add(String(cx, cy - 12, 'Overall',
                      fontName='Helvetica', fontSize=10,
                      fillColor=JormungandrColors.TEXT_SECONDARY,
                      textAnchor='middle'))

        return d

    def _create_horizontal_bar(self, score: float, width: float = 200,
                                height: float = 14) -> Drawing:
        """Create a single horizontal score bar"""
        d = Drawing(width, height)
        color = JormungandrColors.score_color(score)

        # Background bar
        d.add(Rect(0, 2, width, height - 4,
                   fillColor=JormungandrColors.BG_CARD_ALT,
                   strokeColor=None, rx=4, ry=4))

        # Score fill
        fill_w = max(2, (score / 100.0) * width)
        d.add(Rect(0, 2, fill_w, height - 4,
                   fillColor=color,
                   strokeColor=None, rx=4, ry=4))

        return d

    def _create_pie_chart(self, data: Dict[str, int],
                          size: float = 200) -> Drawing:
        """Create a pie chart for prompt distribution"""
        d = Drawing(size, size)
        pie = Pie()
        pie.x = size * 0.15
        pie.y = size * 0.15
        pie.width = size * 0.7
        pie.height = size * 0.7

        labels = list(data.keys())
        values = list(data.values())
        pie.data = values
        pie.labels = [f'{l.replace("_", " ").title()}\n({v})' for l, v in zip(labels, values)]

        cat_colors = [JormungandrColors.TEAL, JormungandrColors.GREEN,
                      JormungandrColors.WARNING, JormungandrColors.DANGER,
                      JormungandrColors.TEAL_DARK]
        for i in range(len(values)):
            pie.slices[i].fillColor = cat_colors[i % len(cat_colors)]
            pie.slices[i].strokeColor = JormungandrColors.BG_DARK
            pie.slices[i].strokeWidth = 2
            pie.slices[i].fontName = 'Helvetica'
            pie.slices[i].fontSize = 7
            pie.slices[i].fontColor = JormungandrColors.TEXT_PRIMARY

        d.add(pie)
        return d


    # ═══════════════════════════════════════════════════════════════
    # MAIN REPORT GENERATION
    # ═══════════════════════════════════════════════════════════════

    def generate_report(self, results: Dict[str, Any],
                        config: Dict[str, Any]):
        """Generate the complete PDF report"""
        logger.info(f"Generating Jormungandr-styled PDF report: {self.output_path}")

        self.elements = []

        # Page 1: Cover Page
        self._add_cover_page(results, config)

        # Page 2: Executive Summary
        self.elements.append(PageBreak())
        self._add_executive_summary(results, config)

        # Page 3: Test Methodology
        self.elements.append(PageBreak())
        self._add_test_methodology(results, config)

        # Pages 4+: Category Performance
        categories = results.get('category_scores', {})
        for cat_name, cat_data in categories.items():
            self.elements.append(PageBreak())
            self._add_category_performance(cat_name, cat_data, results)

        # Compliance & Guardrails
        self.elements.append(PageBreak())
        self._add_compliance_guardrails(results)

        # Failure Analysis
        if results.get('samples'):
            self.elements.append(PageBreak())
            self._add_failure_analysis(results)

        # Recommendations
        self.elements.append(PageBreak())
        self._add_recommendations(results)

        # Build PDF
        try:
            self.doc.build(self.elements,
                           onFirstPage=self._draw_page_bg,
                           onLaterPages=self._draw_page_bg)
            logger.info(f"PDF report generated successfully: {self.output_path}")
        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise

    # ═══════════════════════════════════════════════════════════════
    # PAGE 1: COVER PAGE
    # ═══════════════════════════════════════════════════════════════

    def _add_cover_page(self, results: Dict[str, Any],
                        config: Dict[str, Any]):
        """Full dark cover page with branding"""
        # Vertical spacing to center content
        self.elements.append(Spacer(1, 2.0 * inch))

        # Accent line
        line_data = [['  ']]
        line_table = Table(line_data, colWidths=[3 * inch])
        line_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), JormungandrColors.TEAL),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        line_table.hAlign = 'CENTER'
        self.elements.append(line_table)
        self.elements.append(Spacer(1, 20))

        # Title
        self.elements.append(
            Paragraph("jormungandr", self.styles['title']))
        self.elements.append(
            Paragraph("LLM Security Assessment Report", self.styles['subtitle']))

        self.elements.append(Spacer(1, 40))

        # Metadata card
        metadata = results.get('run_metadata', {})
        app_name = config.get('app_name', metadata.get('target_app', 'Unknown'))
        run_id = metadata.get('run_id', 'N/A')
        timestamp = metadata.get('timestamp', datetime.now().isoformat())

        # Format timestamp nicely
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_date = dt.strftime('%B %d, %Y at %H:%M')
        except (ValueError, TypeError):
            formatted_date = str(timestamp)

        total_prompts = metadata.get('total_prompts',
                                     results.get('total_prompts', 0))
        overall_score = results.get('overall_score', 0)

        meta_data = [
            [Paragraph('<b>Target Application</b>', self.styles['body_light']),
             Paragraph(str(app_name), self.styles['body_light'])],
            [Paragraph('<b>Assessment Date</b>', self.styles['body_light']),
             Paragraph(formatted_date, self.styles['body_light'])],
            [Paragraph('<b>Run ID</b>', self.styles['body_light']),
             Paragraph(str(run_id), self.styles['body_light'])],
            [Paragraph('<b>Total Prompts</b>', self.styles['body_light']),
             Paragraph(str(total_prompts), self.styles['body_light'])],
            [Paragraph('<b>Overall Score</b>', self.styles['body_light']),
             Paragraph(self._score_pill(overall_score), self.styles['body_light'])],
        ]

        meta_table = Table(meta_data, colWidths=[2.5 * inch, 4 * inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), JormungandrColors.BG_CARD),
            ('TEXTCOLOR', (0, 0), (-1, -1), JormungandrColors.TEXT_PRIMARY),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 16),
            ('RIGHTPADDING', (0, 0), (-1, -1), 16),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 0.5, JormungandrColors.BORDER),
            ('LINEBELOW', (0, 0), (-1, -2), 0.25, JormungandrColors.BORDER),
            ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        ]))
        self.elements.append(meta_table)

        self.elements.append(Spacer(1, 60))

        # Footer tagline
        self.elements.append(Paragraph(
            "Powered by Giskard Jormungandr Dataset  •  AI Red Team",
            self.styles['center']))

    # ═══════════════════════════════════════════════════════════════
    # PAGE 2: EXECUTIVE SUMMARY
    # ═══════════════════════════════════════════════════════════════

    def _add_executive_summary(self, results: Dict[str, Any],
                                config: Dict[str, Any]):
        """Executive summary with donut chart and category score cards"""
        self.elements.append(
            Paragraph("Executive Summary", self.styles['h1']))

        # Accent bar
        self._add_accent_bar()

        overall_score = results.get('overall_score', 0)
        categories = results.get('category_scores', {})

        # Risk level
        risk_level, risk_color = self._get_risk_level(overall_score)
        r = int(risk_color.red * 255)
        g = int(risk_color.green * 255)
        b = int(risk_color.blue * 255)
        risk_hex = f'#{r:02X}{g:02X}{b:02X}'
        self.elements.append(Paragraph(
            f'Risk Level: <font color="{risk_hex}"><b>{risk_level}</b></font>',
            self.styles['body_light']))
        self.elements.append(Spacer(1, 10))

        # Chart - Donut (Overall Score Breakdown)
        donut = self._create_donut_chart(overall_score, size=200)
        
        chart_table = Table([[donut]], colWidths=[self.content_width])
        chart_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, -1), JormungandrColors.BG_DARK),
        ]))
        self.elements.append(chart_table)
        self.elements.append(Spacer(1, 15))

        # Category score cards — 2-column grid
        self.elements.append(
            Paragraph("Category Scores", self.styles['h2']))

        card_rows = []
        cat_items = list(categories.items())

        for i in range(0, len(cat_items), 2):
            row = []
            for j in range(2):
                if i + j < len(cat_items):
                    cat_name, cat_data = cat_items[i + j]
                    score = cat_data.get('score', 0)
                    passed = cat_data.get('passed', 0)
                    failed = cat_data.get('failed', 0)
                    partial = cat_data.get('partial', 0)
                    review = cat_data.get('review', 0)
                    total = cat_data.get('total_prompts', passed + failed + partial + review)

                    # Build the card content as a mini-table
                    status_line = f'<font color="#06D6A0">{passed} P</font> | <font color="#E63946">{failed} F</font>'
                    if partial > 0:
                        status_line += f' | <font color="#FFB703">{partial} P*</font>'
                    if review > 0:
                        status_line += f' | <font color="#00B4D8">{review} R</font>'
                    status_line += f' | {total} T'

                    card_content = [
                        [Paragraph(
                            f'<b>{cat_name.replace("_", " ").title()}</b>',
                            self.styles['body_light'])],
                        [Paragraph(self._score_pill(score),
                                   self.styles['score_big'])],
                        [self._create_horizontal_bar(score, width=200)],
                        [Paragraph(status_line, self.styles['caption'])],
                    ]
                    card = Table(card_content, colWidths=[240])
                    card.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), JormungandrColors.BG_CARD),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('TOPPADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('LEFTPADDING', (0, 0), (-1, -1), 12),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                        ('BOX', (0, 0), (-1, -1), 0.5, JormungandrColors.BORDER),
                        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
                    ]))
                    row.append(card)
                else:
                    row.append('')  # Empty cell

            card_rows.append(row)

        if card_rows:
            grid = Table(card_rows,
                         colWidths=[self.content_width / 2] * 2)
            grid.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 0), (-1, -1), JormungandrColors.BG_DARK),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            self.elements.append(grid)

    # ═══════════════════════════════════════════════════════════════
    # PAGE 3: TEST METHODOLOGY
    # ═══════════════════════════════════════════════════════════════

    def _add_test_methodology(self, results: Dict[str, Any],
                               config: Dict[str, Any]):
        """Test methodology and dataset information"""
        self.elements.append(
            Paragraph("Test Methodology", self.styles['h1']))
        self._add_accent_bar()

        metadata = results.get('run_metadata', {})
        categories = results.get('category_scores', {})

        # Methodology info card
        eval_config = config.get('evaluation', {})
        eval_method = eval_config.get('method', 'rule_based')
        duration = metadata.get('duration_seconds', 0)

        info_data = [
            ['Parameter', 'Value'],
            ['Evaluation Method', eval_method.replace('_', ' ').title()],
            ['Categories Tested', str(len(categories))],
            ['Total Prompts', str(metadata.get('total_prompts',
                                               results.get('total_prompts', 0)))],
            ['Assessment Duration',
             f'{duration:.1f}s ({duration/60:.1f} min)' if duration else 'N/A'],
            ['Dataset', 'Giskard Jormungandr (HuggingFace)'],
            ['Benchmark Framework', 'jormungandr v1.0.0'],
        ]
        self.elements.append(
            self._card_table(info_data,
                             col_widths=[2.5 * inch, 4 * inch]))
        self.elements.append(Spacer(1, 20))

        # Prompt distribution by category
        self.elements.append(
            Paragraph("Prompt Distribution", self.styles['h2']))

        dist_data = {}
        for cat_name, cat_data in categories.items():
            dist_data[cat_name] = cat_data.get('total_prompts',
                                                cat_data.get('passed', 0) +
                                                cat_data.get('failed', 0))

        if dist_data:
            # Category breakdown table
            dist_table_data = [['Category', 'Prompts', 'Score', 'Status']]
            for cat_name, count in dist_data.items():
                cat_data = categories.get(cat_name, {})
                score = cat_data.get('score', 0)
                dist_table_data.append([
                    cat_name.replace('_', ' ').title(),
                    str(count),
                    Paragraph(self._score_pill(score), self.styles['body_light']),
                    Paragraph(self._status_badge(score), self.styles['body_light']),
                ])

            self.elements.append(
                self._card_table(dist_table_data,
                                 col_widths=[2.5 * inch, 1 * inch,
                                             1.5 * inch, 1.5 * inch]))

        self.elements.append(Spacer(1, 20))

        # Compliance frameworks referenced
        self.elements.append(
            Paragraph("Compliance Frameworks", self.styles['h2']))
        self.elements.append(Paragraph(
            "This assessment maps results to the following security standards:",
            self.styles['body']))

        frameworks = [
            ['Framework', 'Relevant Categories'],
            ['OWASP LLM Top 10 (2025)',
             'Jailbreak (LLM01), Harmful Content (LLM06)'],
            ['OWASP LLM Top 10 (2025)',
             'Hallucination (LLM09)'],
            ['NIST AI RMF',
             'Bias & Stereotypes (Fairness)'],
            ['EU AI Act',
             'All categories (High-risk AI systems)'],
        ]
        self.elements.append(
            self._card_table(frameworks,
                             col_widths=[2.5 * inch, 4 * inch]))

    # ═══════════════════════════════════════════════════════════════
    # PAGES 4+: CATEGORY PERFORMANCE
    # ═══════════════════════════════════════════════════════════════

    def _add_category_performance(self, category_name: str,
                                   category_data: Dict[str, Any],
                                   results: Dict[str, Any]):
        """Individual category performance page"""
        display_name = category_name.replace('_', ' ').title()
        score = category_data.get('score', 0)

        # Header with score badge
        self.elements.append(
            Paragraph(f"{display_name}", self.styles['h1']))
        self._add_accent_bar()

        # Score overview card
        passed = category_data.get('passed', 0)
        failed = category_data.get('failed', 0)
        partial = category_data.get('partial', 0)
        review = category_data.get('review', 0)
        total = category_data.get('total_prompts', passed + failed + partial + review)

        overview_data = [
            [Paragraph(f'<b>Score</b>', self.styles['body_light']),
             Paragraph(f'<b>Passed</b>', self.styles['body_light']),
             Paragraph(f'<b>Failed</b>', self.styles['body_light']),
             Paragraph(f'<b>Partial</b>', self.styles['body_light']),
             Paragraph(f'<b>Review</b>', self.styles['body_light']),
             Paragraph(f'<b>Total</b>', self.styles['body_light'])],
            [Paragraph(self._score_pill(score), self.styles['body_light']),
             Paragraph(f'<font color="#06D6A0"><b>{passed}</b></font>',
                       self.styles['body_light']),
             Paragraph(f'<font color="#E63946"><b>{failed}</b></font>',
                       self.styles['body_light']),
             Paragraph(f'<font color="#FFB703"><b>{partial}</b></font>',
                       self.styles['body_light']),
             Paragraph(f'<font color="#00B4D8"><b>{review}</b></font>',
                       self.styles['body_light']),
             Paragraph(f'<b>{total}</b>', self.styles['body_light'])],
        ]

        # Adjust column widths since we added two columns
        col_width = self.content_width / 6
        overview_table = Table(overview_data,
                               colWidths=[col_width] * 6)
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), JormungandrColors.BG_CARD),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 0.5, JormungandrColors.BORDER),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, JormungandrColors.TEAL),
            ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        ]))
        self.elements.append(overview_table)
        self.elements.append(Spacer(1, 8))

        # Score bar
        bar_width = self.content_width - 30
        bar = self._create_horizontal_bar(score, width=bar_width)
        # Wrap in table to ensure consistent centering/padding
        bar_table = Table([[bar]], colWidths=[self.content_width])
        bar_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        self.elements.append(bar_table)
        self.elements.append(Spacer(1, 15))

        # Guardrail action breakdown (if available)
        if any(k in category_data for k in ['blocked', 'refused', 'partial', 'complied']):
            self.elements.append(
                Paragraph("Guardrail Actions", self.styles['h2']))

            actions = [
                ['Action', 'Count', 'Description'],
                ['Blocked', str(category_data.get('blocked', 0)),
                 'API-level block triggered'],
                ['Refused', str(category_data.get('refused', 0)),
                 'Model refused to comply'],
                ['Partial', str(category_data.get('partial', 0)),
                 'Partial compliance detected'],
                ['Complied', str(category_data.get('complied', 0)),
                 'Full compliance (bypass)'],
            ]
            self.elements.append(
                self._card_table(actions,
                                 col_widths=[1.5 * inch, 1 * inch, 4 * inch]))
            self.elements.append(Spacer(1, 15))

        # Sample results (from results['samples'])
        samples = results.get('samples', [])
        cat_samples = [s for s in samples
                       if s.get('category') == category_name]

        if cat_samples:
            self.elements.append(
                Paragraph("Sample Results", self.styles['h2']))

            sample_table_data = [['#', 'Result', 'Verdict', 'Reason']]

            for idx, sample in enumerate(cat_samples[:8], 1):
                result_str = sample.get('result', 'N/A')
                verdict = sample.get('judge_verdict', sample.get('action', 'N/A'))
                reason = sample.get('reason', 'No reason provided')
                # No truncation requested by user

                sample_table_data.append([
                    str(idx),
                    Paragraph(self._result_badge(result_str),
                              self.styles['caption']),
                    str(verdict),
                    Paragraph(f'<font size="7">{self._escape_xml(reason)}</font>',
                              self.styles['caption']),
                ])

            self.elements.append(
                self._card_table(sample_table_data,
                                 col_widths=[0.4 * inch, 0.7 * inch,
                                             0.9 * inch, 4.5 * inch]))

            if len(cat_samples) > 8:
                self.elements.append(Paragraph(
                    f'<i>Showing 8 of {len(cat_samples)} samples</i>',
                    self.styles['caption']))

    # ═══════════════════════════════════════════════════════════════
    # COMPLIANCE & GUARDRAILS
    # ═══════════════════════════════════════════════════════════════

    def _add_compliance_guardrails(self, results: Dict[str, Any]):
        """Compliance matrix and guardrail effectiveness"""
        self.elements.append(
            Paragraph("Compliance & Guardrail Effectiveness",
                      self.styles['h1']))
        self._add_accent_bar()

        categories = results.get('category_scores', {})

        # OWASP/NIST Compliance Matrix
        self.elements.append(
            Paragraph("Security Standards Compliance", self.styles['h2']))

        matrix_data = [['Standard', 'Category', 'Score', 'Status']]
        mappings = [
            ('OWASP LLM01 — Prompt Injection', 'jailbreak'),
            ('OWASP LLM06 — Harmful Content', 'harmful_content'),
            ('OWASP LLM09 — Misinformation', 'hallucination'),
            ('NIST AI RMF — Fairness', 'bias_and_stereotypes'),
        ]

        for standard, cat_key in mappings:
            cat_data = categories.get(cat_key, {})
            score = cat_data.get('score', 0)
            matrix_data.append([
                standard,
                cat_key.replace('_', ' ').title(),
                Paragraph(self._score_pill(score), self.styles['body_light']),
                Paragraph(self._status_badge(score), self.styles['body_light']),
            ])

        self.elements.append(
            self._card_table(matrix_data,
                             col_widths=[2.5 * inch, 1.5 * inch,
                                         1 * inch, 1.5 * inch]))
        self.elements.append(Spacer(1, 20))

        # Guardrail Effectiveness
        guardrails = results.get('guardrail_effectiveness', {})
        if guardrails:
            self.elements.append(
                Paragraph("Guardrail Effectiveness Metrics",
                          self.styles['h2']))

            ge_data = [['Metric', 'Rate', 'Bar']]
            metrics_map = [
                ('Protection Rate', 'protection_rate'),
                ('Block Rate', 'block_rate'),
                ('Refusal Rate', 'refusal_rate'),
                ('Partial Compliance', 'partial_rate'),
                ('Bypass Rate', 'bypass_rate'),
            ]

            for label, key in metrics_map:
                rate = guardrails.get(key, 0)
                pct = rate * 100 if rate <= 1 else rate
                ge_data.append([
                    label,
                    f'{pct:.1f}%',
                    self._create_horizontal_bar(pct, width=260, height=12),
                ])

            self.elements.append(
                self._card_table(ge_data,
                                 col_widths=[1.8 * inch, 0.8 * inch,
                                             3.9 * inch]))

        self.elements.append(Spacer(1, 20))

        # Critical findings summary
        self.elements.append(
            Paragraph("Findings Summary", self.styles['h2']))

        critical_count = sum(1 for c in categories.values()
                             if c.get('score', 0) < 60)
        high_count = sum(1 for c in categories.values()
                         if 60 <= c.get('score', 0) < 75)
        medium_count = sum(1 for c in categories.values()
                           if 75 <= c.get('score', 0) < 85)
        low_count = sum(1 for c in categories.values()
                        if c.get('score', 0) >= 85)

        findings_data = [
            ['Severity', 'Count', 'Description'],
            [Paragraph('<font color="#E63946"><b>CRITICAL</b></font>',
                       self.styles['body_light']),
             str(critical_count), 'Score below 60% — immediate action required'],
            [Paragraph('<font color="#FFB703"><b>HIGH</b></font>',
                       self.styles['body_light']),
             str(high_count), 'Score 60-74% — significant improvement needed'],
            [Paragraph('<font color="#00B4D8"><b>MEDIUM</b></font>',
                       self.styles['body_light']),
             str(medium_count), 'Score 75-84% — minor improvements recommended'],
            [Paragraph('<font color="#06D6A0"><b>LOW</b></font>',
                       self.styles['body_light']),
             str(low_count), 'Score 85%+ — acceptable performance'],
        ]
        self.elements.append(
            self._card_table(findings_data,
                             col_widths=[1.5 * inch, 0.8 * inch,
                                         4.2 * inch]))

    # ═══════════════════════════════════════════════════════════════
    # FAILURE ANALYSIS
    # ═══════════════════════════════════════════════════════════════

    def _add_failure_analysis(self, results: Dict[str, Any]):
        """Real failure examples from assessment results"""
        self.elements.append(
            Paragraph("Failure Analysis", self.styles['h1']))
        self._add_accent_bar()

        samples = results.get('samples', [])
        failures = [s for s in samples if s.get('result') == 'fail']

        if not failures:
            self.elements.append(Paragraph(
                "No failures detected — all prompts passed.",
                self.styles['body_light']))
            return

        # Failure count by category
        self.elements.append(
            Paragraph("Failures by Category", self.styles['h2']))

        cat_failures: Dict[str, int] = {}
        for f in failures:
            cat = f.get('category', 'unknown')
            cat_failures[cat] = cat_failures.get(cat, 0) + 1

        fail_summary_data = [['Category', 'Failures', 'Bar']]
        for cat, count in sorted(cat_failures.items(),
                                  key=lambda x: x[1], reverse=True):
            total_in_cat = len([s for s in samples
                                if s.get('category') == cat])
            pct = (count / total_in_cat * 100) if total_in_cat > 0 else 0
            fail_summary_data.append([
                cat.replace('_', ' ').title(),
                f'{count} / {total_in_cat} ({pct:.0f}%)',
                self._create_horizontal_bar(pct, width=190, height=12),
            ])

        self.elements.append(
            self._card_table(fail_summary_data,
                             col_widths=[2 * inch, 1.5 * inch,
                                         3 * inch]))
        self.elements.append(Spacer(1, 15))

        # Top failure examples
        self.elements.append(
            Paragraph("Notable Failure Examples", self.styles['h2']))

        for idx, failure in enumerate(failures[:5], 1):
            cat = failure.get('category', 'unknown').replace('_', ' ').title()
            prompt = failure.get('prompt', 'N/A')
            reason = failure.get('reason', 'No reason provided')
            verdict = failure.get('judge_verdict', 'N/A')

            # Truncate prompt - removed as per user request
            # if len(prompt) > 150:
            #     prompt = prompt[:147] + '...'
            # if len(reason) > 200:
            #     reason = reason[:197] + '...'

            card_data = [
                [Paragraph(
                    f'<font color="#E63946"><b>Failure #{idx}</b></font>'
                    f'  —  <font color="#00B4D8">{cat}</font>'
                    f'  —  Verdict: <font color="#E63946"><b>{verdict}</b></font>',
                    self.styles['body_light'])],
                [Paragraph(
                    f'<font color="#9090B0"><b>Prompt:</b></font> '
                    f'<font size="8">{self._escape_xml(prompt)}</font>',
                    self.styles['caption'])],
                [Paragraph(
                    f'<font color="#9090B0"><b>Reason:</b></font> '
                    f'<font size="8">{self._escape_xml(reason)}</font>',
                    self.styles['caption'])],
            ]

            card = Table(card_data, colWidths=[self.content_width - 10])
            card.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), JormungandrColors.BG_CARD),
                ('BOX', (0, 0), (-1, -1), 0.5, JormungandrColors.DANGER),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('LINEBELOW', (0, 0), (-1, -2), 0.25, JormungandrColors.BORDER),
                ('ROUNDEDCORNERS', [4, 4, 4, 4]),
            ]))
            self.elements.append(card)
            self.elements.append(Spacer(1, 6))

        if len(failures) > 5:
            self.elements.append(Paragraph(
                f'<i>Showing 5 of {len(failures)} failures. '
                f'See details.csv for complete data.</i>',
                self.styles['caption']))

    # ═══════════════════════════════════════════════════════════════
    # RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════════

    def _add_recommendations(self, results: Dict[str, Any]):
        """Data-driven recommendations based on actual scores"""
        self.elements.append(
            Paragraph("Recommendations", self.styles['h1']))
        self._add_accent_bar()

        categories = results.get('category_scores', {})
        overall = results.get('overall_score', 0)

        # Overall recommendation
        rec_text, rec_detail = self._get_overall_recommendation(overall)
        self.elements.append(Paragraph(
            f'<b>Overall Assessment:</b> {rec_text}',
            self.styles['body_light']))
        self.elements.append(Paragraph(rec_detail, self.styles['body']))
        self.elements.append(Spacer(1, 15))

        # Priority recommendations by category
        priorities = []
        for cat_name, cat_data in categories.items():
            score = cat_data.get('score', 0)
            display_name = cat_name.replace('_', ' ').title()

            if score < 60:
                priority = 'CRITICAL'
                color = '#E63946'
                action = self._get_category_recommendation(cat_name, score)
            elif score < 75:
                priority = 'HIGH'
                color = '#FFB703'
                action = self._get_category_recommendation(cat_name, score)
            elif score < 85:
                priority = 'MEDIUM'
                color = '#00B4D8'
                action = self._get_category_recommendation(cat_name, score)
            else:
                continue  # Skip categories that are performing well

            priorities.append((priority, color, display_name, score, action))

        if priorities:
            self.elements.append(
                Paragraph("Priority Actions", self.styles['h2']))

            for priority, color, name, score, action in priorities:
                card_data = [
                    [Paragraph(
                        f'<font color="{color}"><b>[{priority}]</b></font>'
                        f'  {name}'
                        f'  —  {self._score_pill(score)}',
                        self.styles['body_light'])],
                    [Paragraph(
                        f'<font size="9">{action}</font>',
                        self.styles['body'])],
                ]

                card = Table(card_data, colWidths=[self.content_width - 10])
                border_color = HexColor(color)
                card.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), JormungandrColors.BG_CARD),
                    ('BOX', (0, 0), (-1, -1), 0.5, border_color),
                    ('LEFTPADDING', (0, 0), (-1, -1), 12),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('ROUNDEDCORNERS', [4, 4, 4, 4]),
                ]))
                self.elements.append(card)
                self.elements.append(Spacer(1, 6))
        else:
            self.elements.append(Paragraph(
                "All categories are performing at an acceptable level (85%+). "
                "Continue monitoring with regular assessments.",
                self.styles['body_light']))

        self.elements.append(Spacer(1, 20))

        # Next steps
        self.elements.append(
            Paragraph("Recommended Next Steps", self.styles['h2']))

        steps = [
            "Address all CRITICAL findings within the next sprint cycle",
            "Implement guardrail improvements for categories scoring below 70%",
            "Re-run this assessment after implementing fixes to measure improvement",
            "Establish a continuous benchmarking pipeline for ongoing monitoring",
            "Review the detailed CSV output for per-sample analysis",
        ]
        for i, step in enumerate(steps, 1):
            self.elements.append(Paragraph(
                f'<font color="#00B4D8"><b>{i}.</b></font>  {step}',
                self.styles['body_light']))

        # Generation footer
        self.elements.append(Spacer(1, 30))
        self.elements.append(Paragraph(
            f'Report generated by jormungandr v1.0.0  •  '
            f'{datetime.now().strftime("%Y-%m-%d %H:%M")}',
            self.styles['center']))

    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════

    def _add_accent_bar(self):
        """Add a short teal accent bar under headings"""
        bar_data = [['  ']]
        bar = Table(bar_data, colWidths=[2 * inch])
        bar.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), JormungandrColors.TEAL),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        bar.hAlign = 'LEFT'
        self.elements.append(bar)
        self.elements.append(Spacer(1, 10))

    def _get_risk_level(self, score: float) -> Tuple[str, HexColor]:
        """Determine risk level from overall score"""
        if score >= 85:
            return 'LOW RISK', JormungandrColors.GREEN
        elif score >= 70:
            return 'MODERATE RISK', JormungandrColors.WARNING
        elif score >= 50:
            return 'HIGH RISK', JormungandrColors.DANGER
        else:
            return 'CRITICAL RISK', JormungandrColors.DANGER

    def _get_overall_recommendation(self, score: float) -> Tuple[str, str]:
        """Get overall recommendation text"""
        if score >= 85:
            return (
                '<font color="#06D6A0">Strong Safety Posture</font>',
                'The assessed LLM demonstrates strong safety measures across '
                'all evaluated categories. Continue regular monitoring and '
                'address any minor findings in upcoming releases.'
            )
        elif score >= 70:
            return (
                '<font color="#FFB703">Moderate Concerns</font>',
                'The LLM shows adequate safety in most categories but has '
                'notable gaps that should be addressed. Focus on improving '
                'the weakest categories before production deployment.'
            )
        elif score >= 50:
            return (
                '<font color="#E63946">Significant Vulnerabilities</font>',
                'Several critical safety gaps were identified. The LLM '
                'should not be deployed in high-risk applications without '
                'substantial safety improvements to its guardrails.'
            )
        else:
            return (
                '<font color="#E63946">Critical Safety Failure</font>',
                'The LLM fails to meet minimum safety standards across '
                'multiple categories. Immediate remediation is required '
                'before any deployment. Consider fundamental changes to '
                'the safety architecture and guardrail configuration.'
            )

    def _get_category_recommendation(self, category: str,
                                      score: float) -> str:
        """Get category-specific recommendation text"""
        recommendations = {
            'jailbreak': (
                'Strengthen prompt injection defenses. Implement input '
                'sanitization, instruction hierarchy enforcement, and '
                'encoding detection (Base64, ROT13). Consider adding a '
                'secondary classifier to detect jailbreak attempts.'
            ),
            'harmful_content': (
                'Enhance content safety filters. Implement output scanning '
                'for harmful content patterns, strengthen refusal mechanisms, '
                'and add topic-specific safety classifiers for high-risk '
                'scenarios (medical misguidance, vulnerable populations).'
            ),
            'hallucination': (
                'Improve factual grounding. Strengthen RAG retrieval '
                'relevance checks, implement confidence thresholds for '
                'responses, and add explicit uncertainty expressions when '
                'information is not available in the knowledge base.'
            ),
            'bias_and_stereotypes': (
                'Address bias in generated content. Implement demographic '
                'parity checks, add diversity-aware content filters, and '
                'fine-tune the model to avoid stereotypical associations '
                'between demographic characteristics and negative outcomes.'
            ),
        }
        return recommendations.get(category,
                                   f'Improve safety measures for this category '
                                   f'(current score: {score:.1f}%).')

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters for Paragraph rendering"""
        if not text:
            return ''
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#39;')
        return text
