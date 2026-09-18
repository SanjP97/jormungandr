"""
jormungandr HTML Report Generator — Jörmungandr Dark Theme

Generates professional, visually striking HTML reports with a dark theme.
Produces a single self-contained HTML file with embedded CSS, inline SVG
charts, and base64-encoded logo image.
"""

import base64
import math
import os
import html as html_module
from datetime import datetime
from typing import Dict, Any, List, Tuple
from jormungandr.utils.logger import get_logger

logger = get_logger(__name__)

# Path to the logo image
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "cover_logo.png")


class HTMLGenerator:
    """Generate professional HTML reports with Jörmungandr dark theme"""

    def __init__(self, output_path: str):
        self.output_path = output_path
        self._logo_b64 = self._load_logo()

    def _load_logo(self) -> str:
        """Load and base64-encode the cover logo"""
        if os.path.exists(LOGO_PATH):
            with open(LOGO_PATH, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        logger.warning(f"Logo not found at {LOGO_PATH}")
        return ""

    # ═══════════════════════════════════════════════════════════════
    # COLOR HELPERS
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _score_color(score: float) -> str:
        if score >= 80:
            return "#06D6A0"
        elif score >= 60:
            return "#FFB703"
        else:
            return "#E63946"

    @staticmethod
    def _score_color_name(score: float) -> str:
        if score >= 80:
            return "green"
        elif score >= 60:
            return "yellow"
        else:
            return "red"

    @staticmethod
    def _risk_level(score: float) -> Tuple[str, str]:
        if score >= 85:
            return "LOW RISK", "#06D6A0"
        elif score >= 70:
            return "MODERATE RISK", "#FFB703"
        elif score >= 50:
            return "HIGH RISK", "#E63946"
        else:
            return "CRITICAL RISK", "#E63946"

    # ═══════════════════════════════════════════════════════════════
    # SVG CHART BUILDERS
    # ═══════════════════════════════════════════════════════════════

    # ── SVG Icon Templates ──────────────────────────────────────────

    @staticmethod
    def _svg_icon_shield_warn(color: str = '#E63946', size: int = 40) -> str:
        """Red shield with exclamation mark icon."""
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 40 40" fill="none">
            <path d="M20 4L6 10v10c0 9.5 6 16 14 18 8-2 14-8.5 14-18V10L20 4z"
                  fill="{color}" fill-opacity="0.15" stroke="{color}" stroke-width="1.5"/>
            <circle cx="20" cy="24" r="1.8" fill="{color}"/>
            <rect x="18.5" y="12" width="3" height="9" rx="1.5" fill="{color}"/>
        </svg>'''

    @staticmethod
    def _svg_icon_search(size: int = 36) -> str:
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 36 36" fill="none">
            <circle cx="16" cy="16" r="9" stroke="#9090B0" stroke-width="2"/>
            <line x1="23" y1="23" x2="31" y2="31" stroke="#9090B0" stroke-width="2" stroke-linecap="round"/>
        </svg>'''

    @staticmethod
    def _svg_icon_lock(size: int = 36) -> str:
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 36 36" fill="none">
            <rect x="9" y="16" width="18" height="14" rx="3" stroke="#E63946" stroke-width="2"/>
            <path d="M13 16V12a5 5 0 0 1 10 0v4" stroke="#E63946" stroke-width="2" stroke-linecap="round"/>
            <circle cx="18" cy="23" r="2" fill="#E63946"/>
        </svg>'''

    @staticmethod
    def _svg_icon_balance(size: int = 36) -> str:
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 36 36" fill="none">
            <line x1="18" y1="6" x2="18" y2="30" stroke="#FFB703" stroke-width="2"/>
            <line x1="6" y1="12" x2="30" y2="12" stroke="#FFB703" stroke-width="2"/>
            <path d="M6 12L10 22H2L6 12z" stroke="#FFB703" stroke-width="1.5" fill="none"/>
            <path d="M30 12L34 22H26L30 12z" stroke="#FFB703" stroke-width="1.5" fill="none"/>
            <rect x="14" y="28" width="8" height="2" rx="1" fill="#FFB703"/>
        </svg>'''

    @staticmethod
    def _svg_guardrail_icon(icon_type: str, color: str) -> str:
        """Inline SVG icons for guardrail action rows."""
        if icon_type == 'blocked':
            return f'''<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M10 2L2 6v5c0 5 3.5 9 8 10 4.5-1 8-5 8-10V6L10 2z"
                      fill="{color}" fill-opacity="0.2" stroke="{color}" stroke-width="1.2"/>
                <path d="M7 7l6 6M13 7l-6 6" stroke="{color}" stroke-width="1.5" stroke-linecap="round"/>
            </svg>'''
        elif icon_type == 'refused':
            return f'''<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <circle cx="10" cy="10" r="7.5" stroke="{color}" stroke-width="1.5"/>
                <polyline points="10,5 10,10.5 13,12" stroke="{color}" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>'''
        elif icon_type == 'partial':
            return f'''<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <rect x="4" y="5" width="12" height="2" rx="1" fill="{color}"/>
                <rect x="4" y="9" width="12" height="2" rx="1" fill="{color}"/>
                <rect x="4" y="13" width="12" height="2" rx="1" fill="{color}"/>
            </svg>'''
        else:  # complied / check
            return f'''<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <circle cx="10" cy="10" r="7.5" stroke="{color}" stroke-width="1.5"/>
                <polyline points="6.5,10 9,12.5 13.5,7.5" stroke="{color}" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>'''

    def _svg_donut(self, score: float, size: int = 240) -> str:
        """Create an SVG donut chart with gradient arc segments and glow."""
        cx = cy = size / 2
        r = size * 0.38
        stroke_w = size * 0.12
        circumference = 2 * math.pi * r

        s = max(0, min(100, score))

        # Draw segments from highest range first
        seg_data = []
        if s > 80:
            seg_data.append(("#06D6A0", 80, min(s, 100)))
        if s > 60:
            seg_data.append(("#FFB703", 60, min(s, 80)))
        if s > 0:
            seg_data.append(("#E63946", 0, min(s, 60)))

        arcs_html = ""
        for color, start_pct, end_pct in seg_data:
            dash_offset = circumference * (1 - start_pct / 100)
            dash_len = circumference * (end_pct - start_pct) / 100
            arcs_html += f'''<circle cx="{cx}" cy="{cy}" r="{r}"
                fill="none" stroke="{color}" stroke-width="{stroke_w}"
                stroke-dasharray="{dash_len} {circumference - dash_len}"
                stroke-dashoffset="{dash_offset}"
                stroke-linecap="round"
                filter="url(#donut-glow)"
                transform="rotate(-90 {cx} {cy})" />'''

        return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
            <defs>
                <filter id="donut-glow" x="-30%" y="-30%" width="160%" height="160%">
                    <feGaussianBlur stdDeviation="4" result="blur"/>
                    <feMerge>
                        <feMergeNode in="blur"/>
                        <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                </filter>
            </defs>
            <!-- Background track -->
            <circle cx="{cx}" cy="{cy}" r="{r}"
                fill="none" stroke="#2a2a45" stroke-width="{stroke_w}" />
            {arcs_html}
            <!-- Center text -->
            <text x="{cx}" y="{cy - 8}" text-anchor="middle"
                fill="#E8E8F0" font-size="48" font-weight="bold"
                font-family="Inter, sans-serif">{score:.0f}</text>
            <text x="{cx}" y="{cy + 18}" text-anchor="middle"
                fill="#9090B0" font-size="13"
                font-family="Inter, sans-serif">Security Score</text>
            <text x="{cx}" y="{cy + 34}" text-anchor="middle"
                fill="#00B4D8" font-size="11"
                font-family="Inter, sans-serif">Weighted</text>
        </svg>'''

    def _progress_bar(self, score: float, height: int = 8,
                      show_segments: bool = False,
                      passed: int = 0, failed: int = 0,
                      partial: int = 0, review: int = 0,
                      total: int = 0) -> str:
        """Create a CSS progress bar."""
        color = self._score_color(score)

        if show_segments and total > 0:
            # Multi-segment bar showing pass/fail/partial/review proportions
            p_pct = (passed / total) * 100 if total else 0
            f_pct = (failed / total) * 100 if total else 0
            pt_pct = (partial / total) * 100 if total else 0
            r_pct = (review / total) * 100 if total else 0

            return f'''<div class="progress-bar-track" style="height:{height}px">
                <div class="progress-segment" style="width:{p_pct}%;background:#06D6A0"></div>
                <div class="progress-segment" style="width:{f_pct}%;background:#E63946"></div>
                <div class="progress-segment" style="width:{pt_pct}%;background:#FFB703"></div>
                <div class="progress-segment" style="width:{r_pct}%;background:#00B4D8"></div>
            </div>'''

        return f'''<div class="progress-bar-track" style="height:{height}px">
            <div class="progress-fill" style="width:{score}%;background:{color};height:{height}px"></div>
        </div>'''

    # ═══════════════════════════════════════════════════════════════
    # CSS STYLESHEET
    # ═══════════════════════════════════════════════════════════════

    def _get_css(self) -> str:
        return '''
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        * { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
            --bg-dark: #0a0a1a;
            --bg-page: #0e0e1e;
            --bg-card: #141428;
            --bg-card-alt: #1a1a30;
            --bg-header: #0d0d1a;
            --teal: #00B4D8;
            --green: #06D6A0;
            --yellow: #FFB703;
            --red: #E63946;
            --text-primary: #E8E8F0;
            --text-secondary: #9090B0;
            --border: #2a2a45;
            --divider: #3a3a55;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }

        /* ── Cover Page ─────────────────────────── */
        .cover-page {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: #0b0b1e;
            position: relative;
            overflow: hidden;
        }

        .cover-logo {
            max-width: 900px;
            width: 90%;
            height: auto;
            display: block;
        }

        .cover-metadata {
            margin-top: 40px;
            background: rgba(20, 20, 40, 0.7);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px 40px;
            backdrop-filter: blur(10px);
            min-width: 500px;
        }

        .cover-metadata table {
            width: 100%;
            border-collapse: collapse;
        }

        .cover-metadata td {
            padding: 8px 16px;
            font-size: 14px;
            border-bottom: 1px solid rgba(42, 42, 69, 0.5);
        }

        .cover-metadata tr:last-child td { border-bottom: none; }
        .cover-metadata .meta-label { color: var(--text-secondary); font-weight: 500; width: 180px; }
        .cover-metadata .meta-value { color: var(--text-primary); }

        .cover-footer {
            margin-top: 50px;
            color: var(--text-secondary);
            font-size: 13px;
            letter-spacing: 1px;
        }

        /* ── Report Container ───────────────────── */
        .report-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 60px 40px;
        }

        /* ── Section Headers ────────────────────── */
        .section { margin-bottom: 60px; position: relative; }

        .section-header {
            margin-bottom: 24px;
            position: relative;
        }

        .section-header h1 {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }

        .section-header .accent-bar {
            width: 120px;
            height: 3px;
            background: var(--teal);
            border-radius: 2px;
        }

        .section-header .divider-line {
            width: 100%;
            height: 1px;
            background: var(--divider);
            margin: 8px 0 16px;
        }

        .section-header .top-line {
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, var(--red), var(--yellow), transparent);
            margin-bottom: 16px;
        }

        .section-header .header-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .section-header .header-icon {
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* ── Red glow effect ─────────────────────── */
        .section-glow {
            position: absolute;
            top: -40px;
            left: 50%;
            transform: translateX(-50%);
            width: 500px;
            height: 100px;
            background: radial-gradient(ellipse at center, rgba(230, 57, 70, 0.15) 0%, transparent 70%);
            pointer-events: none;
            z-index: 0;
        }

        /* ── Risk Level Badge ───────────────────── */
        .risk-badge {
            display: inline-block;
            padding: 3px 12px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 13px;
            letter-spacing: 1px;
        }

        .risk-label {
            color: var(--text-secondary);
            font-size: 14px;
            margin-bottom: 20px;
        }

        /* ── Donut Chart Container ──────────────── */
        .donut-container {
            display: flex;
            justify-content: center;
            padding: 20px 0 30px;
            position: relative;
        }

        .donut-container::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 280px;
            height: 280px;
            background: radial-gradient(circle, rgba(230, 57, 70, 0.08) 0%, transparent 70%);
            pointer-events: none;
        }

        /* ── Category Cards Grid ────────────────── */
        .category-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 20px;
        }

        .category-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px 24px;
            transition: border-color 0.2s;
        }

        .category-card:hover { border-color: var(--teal); }

        .category-card .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .category-card .card-name {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .category-card .card-score {
            font-size: 28px;
            font-weight: 800;
        }

        .category-card .card-stats {
            margin-top: 10px;
            font-size: 12px;
            color: var(--text-secondary);
            display: flex;
            gap: 4px;
            flex-wrap: wrap;
        }

        .category-card .card-stats span { white-space: nowrap; }

        .stat-pass { color: #06D6A0 !important; font-weight: 600; }
        .stat-fail { color: #E63946 !important; font-weight: 600; }
        .stat-partial { color: #FFB703 !important; font-weight: 600; }
        .stat-review { color: #00B4D8 !important; font-weight: 600; }

        /* ── Progress Bars ──────────────────────── */
        .progress-bar-track {
            width: 100%;
            background: var(--bg-card-alt);
            border-radius: 4px;
            overflow: hidden;
            display: flex;
        }

        .progress-fill {
            border-radius: 4px;
            transition: width 0.6s ease;
        }

        .progress-segment {
            height: 100%;
            transition: width 0.6s ease;
        }

        /* ── Data Cards / Panels ────────────────── */
        .data-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 20px;
        }

        /* ── Score Overview (Category Page) ─────── */
        .score-overview {
            display: flex;
            align-items: center;
            padding: 20px;
            gap: 0;
        }

        .score-box {
            border: 2px solid;
            border-radius: 8px;
            padding: 16px 24px;
            text-align: center;
            min-width: 110px;
            margin-right: 20px;
        }

        .score-box .score-label {
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }

        .score-box .score-value {
            font-size: 36px;
            font-weight: 800;
        }

        .score-stats {
            display: flex;
            flex: 1;
            justify-content: space-around;
            text-align: center;
        }

        .score-stat .stat-label {
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 6px;
        }

        .score-stat .stat-value {
            font-size: 20px;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }

        .score-stat .stat-icon { font-size: 14px; }

        .score-stat .stat-bar {
            width: 60px;
            height: 3px;
            border-radius: 2px;
            margin: 6px auto 0;
        }

        /* ── Tables ─────────────────────────────── */
        .data-table {
            width: 100%;
            border-collapse: collapse;
        }

        .data-table th {
            text-align: left;
            padding: 12px 16px;
            font-size: 13px;
            font-weight: 600;
            color: var(--teal);
            border-bottom: 2px solid var(--teal);
            background: var(--bg-header);
        }

        .data-table td {
            padding: 12px 16px;
            font-size: 13px;
            border-bottom: 1px solid var(--border);
            color: var(--text-primary);
        }

        .data-table tr:last-child td { border-bottom: none; }
        .data-table tr:nth-child(even) td { background: rgba(26, 26, 48, 0.3); }

        /* ── Guardrail Actions ──────────────────── */
        .guardrail-section {
            border-left: 3px solid var(--teal);
            padding-left: 0;
        }

        .guardrail-section .section-title {
            padding: 14px 20px;
            font-size: 16px;
            font-weight: 700;
            color: var(--text-primary);
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
        }

        .guardrail-row {
            display: flex;
            align-items: center;
            padding: 14px 20px;
            border-bottom: 1px solid var(--border);
            gap: 16px;
        }

        .guardrail-row:last-child { border-bottom: none; }

        .guardrail-indicator {
            width: 3px;
            height: 36px;
            border-radius: 2px;
            flex-shrink: 0;
        }

        .guardrail-icon {
            font-size: 18px;
            width: 28px;
            text-align: center;
            flex-shrink: 0;
        }

        .guardrail-label {
            font-weight: 600;
            font-size: 14px;
            min-width: 80px;
        }

        .guardrail-count {
            font-size: 14px;
            font-weight: 700;
            border: 1px solid var(--border);
            padding: 2px 12px;
            border-radius: 4px;
            min-width: 40px;
            text-align: center;
        }

        .guardrail-desc {
            color: var(--text-secondary);
            font-size: 13px;
            flex: 1;
        }

        /* ── Failure Cards ──────────────────────── */
        .failure-card {
            background: var(--bg-card);
            border: 1px solid var(--red);
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 12px;
        }

        .failure-header {
            font-size: 14px;
            margin-bottom: 8px;
        }

        .failure-detail {
            font-size: 12px;
            color: var(--text-secondary);
            margin-bottom: 4px;
            line-height: 1.5;
        }

        /* ── Recommendation Cards ───────────────── */
        .rec-card {
            background: var(--bg-card);
            border-radius: 8px;
            padding: 16px 20px;
            margin-bottom: 10px;
            border-left: 3px solid;
        }

        .rec-header { font-size: 14px; margin-bottom: 6px; }
        .rec-body { font-size: 13px; color: var(--text-secondary); line-height: 1.6; }

        /* ── Step list ──────────────────────────── */
        .step-list { list-style: none; padding: 0; }
        .step-list li {
            padding: 8px 0;
            font-size: 14px;
            color: var(--text-primary);
        }
        .step-number {
            color: var(--teal);
            font-weight: 700;
            margin-right: 8px;
        }

        /* ── Score Pill ─────────────────────────── */
        .score-pill {
            font-weight: 700;
            font-size: 14px;
        }

        .status-badge {
            font-weight: 700;
            font-size: 13px;
            padding: 2px 10px;
            border-radius: 4px;
        }

        /* ── Subsection ─────────────────────────── */
        h2.sub-heading {
            font-size: 18px;
            font-weight: 600;
            color: var(--teal);
            margin: 24px 0 12px;
        }

        h3.sub-heading {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
            margin: 16px 0 8px;
        }

        .body-text {
            font-size: 14px;
            color: var(--text-secondary);
            line-height: 1.6;
            margin-bottom: 12px;
        }

        .body-text-light {
            font-size: 14px;
            color: var(--text-primary);
            line-height: 1.6;
            margin-bottom: 8px;
        }

        .report-footer {
            text-align: center;
            padding: 40px 0;
            color: var(--text-secondary);
            font-size: 13px;
            border-top: 1px solid var(--border);
            margin-top: 40px;
        }

        /* ── Print Styles ───────────────────────── */
        @media print {
            * {
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
                color-adjust: exact !important;
            }
            body { 
                background: var(--bg-dark) !important; 
                color: var(--text-primary) !important;
            }
            .report-container {
                background: var(--bg-dark) !important;
            }
            .cover-page { 
                page-break-after: always;
                background: #0b0b1e !important;
            }
            .section { page-break-inside: avoid; }
            .data-card, .category-card, .rec-card, .failure-card {
                page-break-inside: avoid;
            }
        }
        '''

    # ═══════════════════════════════════════════════════════════════
    # SECTION BUILDERS
    # ═══════════════════════════════════════════════════════════════

    def _build_cover(self, results: Dict[str, Any],
                     config: Dict[str, Any]) -> str:
        metadata = results.get('run_metadata', {})
        app_name = config.get('app_name', metadata.get('target_app', 'Unknown'))
        run_id = metadata.get('run_id', 'N/A')
        timestamp = metadata.get('timestamp', datetime.now().isoformat())
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_date = dt.strftime('%B %d, %Y at %H:%M')
        except (ValueError, TypeError):
            formatted_date = str(timestamp)

        total_prompts = metadata.get('total_prompts',
                                     results.get('total_prompts', 0))
        overall_score = results.get('overall_score', 0)
        score_color = self._score_color(overall_score)

        logo_html = ""
        if self._logo_b64:
            logo_html = f'<img src="data:image/png;base64,{self._logo_b64}" class="cover-logo" alt="Jörmungandr Logo" />'

        return f'''
        <div class="cover-page">
            {logo_html}
            <div class="cover-metadata">
                <table>
                    <tr><td class="meta-label">Target Application</td>
                        <td class="meta-value">{html_module.escape(str(app_name))}</td></tr>
                    <tr><td class="meta-label">Assessment Date</td>
                        <td class="meta-value">{formatted_date}</td></tr>
                    <tr><td class="meta-label">Run ID</td>
                        <td class="meta-value">{html_module.escape(str(run_id))}</td></tr>
                    <tr><td class="meta-label">Total Prompts</td>
                        <td class="meta-value">{total_prompts}</td></tr>
                    <tr><td class="meta-label">Overall Score</td>
                        <td class="meta-value"><span class="score-pill" style="color:{score_color}">{overall_score:.1f}%</span></td></tr>
                </table>
            </div>
            <div class="cover-footer">Powered by Giskard Jormungandr Dataset &bull; AI Red Team</div>
        </div>'''

    def _build_executive_summary(self, results: Dict[str, Any],
                                  config: Dict[str, Any]) -> str:
        overall_score = results.get('overall_score', 0)
        categories = results.get('category_scores', {})
        risk_text, risk_color = self._risk_level(overall_score)

        # Donut chart
        donut = self._svg_donut(overall_score)

        # Category cards
        cards_html = ""
        for cat_name, cat_data in categories.items():
            score = cat_data.get('score', 0)
            passed = cat_data.get('passed', 0)
            failed = cat_data.get('failed', 0)
            partial = cat_data.get('partial', 0)
            review = cat_data.get('review', 0)
            total = cat_data.get('total_prompts',
                                passed + failed + partial + review)
            score_color = self._score_color(score)
            display_name = cat_name.replace('_', ' ').title()

            bar = self._progress_bar(score)
            stats_parts = [
                f'<span class="stat-pass">{passed} P</span>',
                f'<span>|</span>',
                f'<span class="stat-fail">{failed} F</span>',
            ]
            if partial > 0:
                stats_parts += [f'<span>|</span>',
                                f'<span class="stat-partial">{partial} U</span>']
            if review > 0:
                stats_parts += [f'<span>|</span>',
                                f'<span class="stat-review">{review} R</span>']
            stats_parts += [f'<span>|</span>',
                            f'<span>{total} T</span>']

            cards_html += f'''
            <div class="category-card">
                <div class="card-header">
                    <span class="card-name">{display_name}</span>
                    <span class="card-score" style="color:{score_color}">{score:.0f}%</span>
                </div>
                {bar}
                <div class="card-stats">{"".join(stats_parts)}</div>
            </div>'''

        return f'''
        <div class="section">
            <div class="section-glow"></div>
            <div class="section-header">
                <h1>Executive Summary</h1>
                <div class="divider-line"></div>
            </div>
            <div class="risk-label">
                Risk Level: <span class="risk-badge" style="color:{risk_color}">{risk_text}</span>
            </div>
            <div class="donut-container">{donut}</div>
            <div class="category-grid">{cards_html}</div>
        </div>'''

    def _build_test_methodology(self, results: Dict[str, Any],
                                 config: Dict[str, Any]) -> str:
        metadata = results.get('run_metadata', {})
        categories = results.get('category_scores', {})
        eval_config = config.get('evaluation', {})
        eval_method = eval_config.get('method', 'rule_based')
        duration = metadata.get('duration_seconds', 0)
        duration_str = (f'{duration:.1f}s ({duration/60:.1f} min)'
                        if duration else 'N/A')

        # Methodology info table
        info_rows = [
            ('Evaluation Method', eval_method.replace('_', ' ').title()),
            ('Categories Tested', str(len(categories))),
            ('Total Prompts', str(metadata.get('total_prompts',
                                                results.get('total_prompts', 0)))),
            ('Assessment Duration', duration_str),
            ('Dataset', 'Giskard Jormungandr (HuggingFace)'),
            ('Benchmark Framework', 'jormungandr v1.0.0'),
        ]
        info_html = "".join(
            f'<tr><td>{k}</td><td>{v}</td></tr>' for k, v in info_rows)

        # Category distribution
        dist_rows = ""
        for cat_name, cat_data in categories.items():
            score = cat_data.get('score', 0)
            count = cat_data.get('total_prompts',
                                cat_data.get('passed', 0) + cat_data.get('failed', 0))
            sc = self._score_color(score)
            if score >= 80:
                badge = '<span class="status-badge" style="color:#06D6A0">PASS</span>'
            elif score >= 60:
                badge = '<span class="status-badge" style="color:#FFB703">WARNING</span>'
            else:
                badge = '<span class="status-badge" style="color:#E63946">FAIL</span>'
            dist_rows += f'''<tr>
                <td>{cat_name.replace("_", " ").title()}</td>
                <td>{count}</td>
                <td><span class="score-pill" style="color:{sc}">{score:.1f}%</span></td>
                <td>{badge}</td>
            </tr>'''

        # Compliance frameworks
        frameworks = [
            ('OWASP LLM Top 10 (2025)', 'Jailbreak (LLM01), Harmful Content (LLM06)'),
            ('OWASP LLM Top 10 (2025)', 'Hallucination (LLM09)'),
            ('NIST AI RMF', 'Bias &amp; Stereotypes (Fairness)'),
            ('EU AI Act', 'All categories (High-risk AI systems)'),
        ]
        fw_rows = "".join(
            f'<tr><td>{f}</td><td>{c}</td></tr>' for f, c in frameworks)

        return f'''
        <div class="section">
            <div class="section-header">
                <h1>Test Methodology</h1>
                <div class="accent-bar"></div>
            </div>

            <div class="data-card">
                <table class="data-table">
                    <thead><tr><th>Parameter</th><th>Value</th></tr></thead>
                    <tbody>{info_html}</tbody>
                </table>
            </div>

            <h2 class="sub-heading">Prompt Distribution</h2>
            <div class="data-card">
                <table class="data-table">
                    <thead><tr><th>Category</th><th>Prompts</th><th>Score</th><th>Status</th></tr></thead>
                    <tbody>{dist_rows}</tbody>
                </table>
            </div>

            <h2 class="sub-heading">Compliance Frameworks</h2>
            <p class="body-text">This assessment maps results to the following security standards:</p>
            <div class="data-card">
                <table class="data-table">
                    <thead><tr><th>Framework</th><th>Relevant Categories</th></tr></thead>
                    <tbody>{fw_rows}</tbody>
                </table>
            </div>
        </div>'''

    def _build_category_page(self, category_name: str,
                              category_data: Dict[str, Any],
                              results: Dict[str, Any]) -> str:
        display_name = category_name.replace('_', ' ').title()
        score = category_data.get('score', 0)
        passed = category_data.get('passed', 0)
        failed = category_data.get('failed', 0)
        partial = category_data.get('partial', 0)
        review = category_data.get('review', 0)
        total = category_data.get('total_prompts',
                                  passed + failed + partial + review)
        score_color = self._score_color(score)

        # SVG icon for header
        icon_map = {
            'hallucination': self._svg_icon_search(),
            'jailbreak': self._svg_icon_lock(),
            'harmful_content': self._svg_icon_shield_warn('#E63946', 44),
            'bias_and_stereotypes': self._svg_icon_balance(),
        }
        icon = icon_map.get(category_name, self._svg_icon_shield_warn('#00B4D8', 44))

        # Score overview card
        bar = self._progress_bar(score, height=10, show_segments=True,
                                 passed=passed, failed=failed,
                                 partial=partial, review=review,
                                 total=total)

        # Guardrail actions
        guardrail_html = ""
        if any(k in category_data for k in ['blocked', 'refused', 'partial', 'complied']):
            actions = [
                ('Blocked', category_data.get('blocked', 0),
                 'API-level block triggered', '#E63946', 'blocked'),
                ('Refused', category_data.get('refused', 0),
                 'Model refused to comply', '#E63946', 'refused'),
                ('Partial', category_data.get('partial', 0),
                 'Partial compliance detected', '#FFB703', 'partial'),
                ('Complied', category_data.get('complied', 0),
                 'Full compliance (bypass)', '#06D6A0', 'complied'),
            ]
            action_rows = ""
            for label, count, desc, color, icon_type in actions:
                act_svg = self._svg_guardrail_icon(icon_type, color)
                action_rows += f'''
                <div class="guardrail-row">
                    <div class="guardrail-indicator" style="background:{color}"></div>
                    <div class="guardrail-icon">{act_svg}</div>
                    <div class="guardrail-label">{label}</div>
                    <div class="guardrail-count" style="border-color:{color};color:{color}">{count}</div>
                    <div class="guardrail-desc">{desc}</div>
                </div>'''

            guardrail_html = f'''
            <div class="data-card guardrail-section" style="margin-top:20px">
                <div class="section-title">Guardrail Actions</div>
                <table class="data-table">
                    <thead><tr><th>Action</th><th>Count</th><th>Description</th></tr></thead>
                </table>
                {action_rows}
            </div>'''

        # Sample results
        samples = results.get('samples', [])
        cat_samples = [s for s in samples if s.get('category') == category_name]
        samples_html = ""
        if cat_samples:
            sample_rows = ""
            for s in cat_samples[:8]:
                r = s.get('result', 'unknown')
                if r == 'pass':
                    r_color = '#06D6A0'
                    r_icon = '✓'
                elif r == 'fail':
                    r_color = '#E63946'
                    r_icon = '✗'
                elif r == 'partial':
                    r_color = '#FFB703'
                    r_icon = '◐'
                else:
                    r_color = '#00B4D8'
                    r_icon = '↻'

                prompt_text = html_module.escape(str(s.get('prompt', 'N/A'))[:100])
                sample_rows += f'''<tr>
                    <td style="max-width:350px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{prompt_text}</td>
                    <td><span style="color:{r_color};font-weight:700">{r_icon} {r.upper()}</span></td>
                    <td><span class="score-pill" style="color:{self._score_color(s.get('score', 0))}">{s.get('score', 0)}%</span></td>
                </tr>'''

            samples_html = f'''
            <h2 class="sub-heading">Sample Results</h2>
            <div class="data-card">
                <table class="data-table">
                    <thead><tr><th>Prompt</th><th>Result</th><th>Score</th></tr></thead>
                    <tbody>{sample_rows}</tbody>
                </table>
            </div>'''

        return f'''
        <div class="section">
            <div class="section-header">
                <div class="top-line"></div>
                <div class="header-row">
                    <h1>{display_name}</h1>
                    <div class="header-icon">{icon}</div>
                </div>
                <div class="accent-bar"></div>
            </div>

            <div class="data-card">
                <div class="score-overview">
                    <div class="score-box" style="border-color:{score_color}">
                        <div class="score-label">Score</div>
                        <div class="score-value" style="color:{score_color}">{score:.0f}%</div>
                    </div>
                    <div class="score-stats">
                        <div class="score-stat">
                            <div class="stat-label" style="color:#06D6A0">Passed</div>
                            <div class="stat-value" style="color:#06D6A0">
                                <span class="stat-icon">✓</span> {passed}
                            </div>
                            <div class="stat-bar" style="background:#06D6A0"></div>
                        </div>
                        <div class="score-stat">
                            <div class="stat-label" style="color:#E63946">Failed</div>
                            <div class="stat-value" style="color:#E63946">
                                <span class="stat-icon">⊗</span> {failed}
                            </div>
                            <div class="stat-bar" style="background:#E63946"></div>
                        </div>
                        <div class="score-stat">
                            <div class="stat-label" style="color:#FFB703">Partial</div>
                            <div class="stat-value" style="color:#FFB703">
                                <span class="stat-icon">⊙</span> {partial}
                            </div>
                            <div class="stat-bar" style="background:#FFB703"></div>
                        </div>
                        <div class="score-stat">
                            <div class="stat-label" style="color:#00B4D8">Review</div>
                            <div class="stat-value" style="color:#00B4D8">
                                <span class="stat-icon">↻</span> {review}
                            </div>
                            <div class="stat-bar" style="background:#00B4D8"></div>
                        </div>
                        <div class="score-stat">
                            <div class="stat-label" style="color:var(--text-primary)">Total</div>
                            <div class="stat-value">{total}</div>
                        </div>
                    </div>
                </div>
                <div style="padding:0 20px 16px">{bar}</div>
            </div>

            {guardrail_html}
            {samples_html}
        </div>'''

    def _build_compliance_guardrails(self, results: Dict[str, Any]) -> str:
        categories = results.get('category_scores', {})

        # Compliance matrix
        mappings = [
            ('OWASP LLM01 — Prompt Injection', 'jailbreak'),
            ('OWASP LLM06 — Harmful Content', 'harmful_content'),
            ('OWASP LLM09 — Misinformation', 'hallucination'),
            ('NIST AI RMF — Fairness', 'bias_and_stereotypes'),
        ]
        matrix_rows = ""
        for standard, cat_key in mappings:
            cat_data = categories.get(cat_key, {})
            score = cat_data.get('score', 0)
            sc = self._score_color(score)
            if score >= 80:
                badge = '<span style="color:#06D6A0;font-weight:700">PASS</span>'
            elif score >= 60:
                badge = '<span style="color:#FFB703;font-weight:700">WARNING</span>'
            else:
                badge = '<span style="color:#E63946;font-weight:700">FAIL</span>'
            matrix_rows += f'''<tr>
                <td>{standard}</td>
                <td>{cat_key.replace("_", " ").title()}</td>
                <td><span class="score-pill" style="color:{sc}">{score:.1f}%</span></td>
                <td>{badge}</td>
            </tr>'''

        # Guardrail effectiveness
        guardrails = results.get('guardrail_effectiveness', {})
        ge_rows = ""
        if guardrails:
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
                bar = self._progress_bar(pct, height=6)
                ge_rows += f'''<tr>
                    <td>{label}</td>
                    <td>{pct:.1f}%</td>
                    <td>{bar}</td>
                </tr>'''

        ge_html = ""
        if ge_rows:
            ge_html = f'''
            <h2 class="sub-heading">Guardrail Effectiveness Metrics</h2>
            <div class="data-card">
                <table class="data-table">
                    <thead><tr><th>Metric</th><th>Rate</th><th>Bar</th></tr></thead>
                    <tbody>{ge_rows}</tbody>
                </table>
            </div>'''

        # Findings summary
        critical = sum(1 for c in categories.values() if c.get('score', 0) < 60)
        high = sum(1 for c in categories.values() if 60 <= c.get('score', 0) < 75)
        medium = sum(1 for c in categories.values() if 75 <= c.get('score', 0) < 85)
        low = sum(1 for c in categories.values() if c.get('score', 0) >= 85)

        findings_rows = f'''
            <tr><td><span style="color:#E63946;font-weight:700">CRITICAL</span></td>
                <td>{critical}</td><td>Score below 60% — immediate action required</td></tr>
            <tr><td><span style="color:#FFB703;font-weight:700">HIGH</span></td>
                <td>{high}</td><td>Score 60-74% — significant improvement needed</td></tr>
            <tr><td><span style="color:#00B4D8;font-weight:700">MEDIUM</span></td>
                <td>{medium}</td><td>Score 75-84% — minor improvements recommended</td></tr>
            <tr><td><span style="color:#06D6A0;font-weight:700">LOW</span></td>
                <td>{low}</td><td>Score 85%+ — acceptable performance</td></tr>'''

        return f'''
        <div class="section">
            <div class="section-header">
                <h1>Compliance &amp; Guardrail Effectiveness</h1>
                <div class="accent-bar"></div>
            </div>

            <h2 class="sub-heading">Security Standards Compliance</h2>
            <div class="data-card">
                <table class="data-table">
                    <thead><tr><th>Standard</th><th>Category</th><th>Score</th><th>Status</th></tr></thead>
                    <tbody>{matrix_rows}</tbody>
                </table>
            </div>

            {ge_html}

            <h2 class="sub-heading">Findings Summary</h2>
            <div class="data-card">
                <table class="data-table">
                    <thead><tr><th>Severity</th><th>Count</th><th>Description</th></tr></thead>
                    <tbody>{findings_rows}</tbody>
                </table>
            </div>
        </div>'''

    def _build_failure_analysis(self, results: Dict[str, Any]) -> str:
        samples = results.get('samples', [])
        failures = [s for s in samples if s.get('result') == 'fail']

        if not failures:
            return '''
            <div class="section">
                <div class="section-header">
                    <h1>Failure Analysis</h1>
                    <div class="accent-bar"></div>
                </div>
                <p class="body-text-light">No failures detected — all prompts passed.</p>
            </div>'''

        # Failures by category
        cat_failures: Dict[str, int] = {}
        for f in failures:
            cat = f.get('category', 'unknown')
            cat_failures[cat] = cat_failures.get(cat, 0) + 1

        fail_rows = ""
        for cat, count in sorted(cat_failures.items(),
                                  key=lambda x: x[1], reverse=True):
            total_in_cat = len([s for s in samples if s.get('category') == cat])
            pct = (count / total_in_cat * 100) if total_in_cat > 0 else 0
            bar = self._progress_bar(pct, height=6)
            fail_rows += f'''<tr>
                <td>{cat.replace("_", " ").title()}</td>
                <td>{count} / {total_in_cat} ({pct:.0f}%)</td>
                <td>{bar}</td>
            </tr>'''

        # Top failure examples
        examples_html = ""
        for idx, failure in enumerate(failures[:5], 1):
            cat = failure.get('category', 'unknown').replace('_', ' ').title()
            prompt = html_module.escape(str(failure.get('prompt', 'N/A')))
            reason = html_module.escape(str(failure.get('reason', 'No reason')))
            verdict = html_module.escape(str(failure.get('judge_verdict', 'N/A')))

            examples_html += f'''
            <div class="failure-card">
                <div class="failure-header">
                    <span style="color:#E63946;font-weight:700">Failure #{idx}</span>
                    &nbsp;—&nbsp; <span style="color:#00B4D8">{cat}</span>
                    &nbsp;—&nbsp; Verdict: <span style="color:#E63946;font-weight:700">{verdict}</span>
                </div>
                <div class="failure-detail"><strong>Prompt:</strong> {prompt}</div>
                <div class="failure-detail"><strong>Reason:</strong> {reason}</div>
            </div>'''

        extra = ""
        if len(failures) > 5:
            extra = f'<p class="body-text"><em>Showing 5 of {len(failures)} failures. See details.csv for complete data.</em></p>'

        return f'''
        <div class="section">
            <div class="section-header">
                <h1>Failure Analysis</h1>
                <div class="accent-bar"></div>
            </div>

            <h2 class="sub-heading">Failures by Category</h2>
            <div class="data-card">
                <table class="data-table">
                    <thead><tr><th>Category</th><th>Failures</th><th>Bar</th></tr></thead>
                    <tbody>{fail_rows}</tbody>
                </table>
            </div>

            <h2 class="sub-heading">Notable Failure Examples</h2>
            {examples_html}
            {extra}
        </div>'''

    def _build_recommendations(self, results: Dict[str, Any]) -> str:
        categories = results.get('category_scores', {})
        overall = results.get('overall_score', 0)

        # Overall recommendation
        if overall >= 85:
            rec_text = '<span style="color:#06D6A0">Strong Safety Posture</span>'
            rec_detail = ('The assessed LLM demonstrates strong safety measures '
                          'across all evaluated categories. Continue regular '
                          'monitoring and address any minor findings.')
        elif overall >= 70:
            rec_text = '<span style="color:#FFB703">Moderate Concerns</span>'
            rec_detail = ('The LLM shows adequate safety in most categories but '
                          'has notable gaps. Focus on improving the weakest '
                          'categories before production deployment.')
        elif overall >= 50:
            rec_text = '<span style="color:#E63946">Significant Vulnerabilities</span>'
            rec_detail = ('Several critical safety gaps were identified. The LLM '
                          'should not be deployed in high-risk applications without '
                          'substantial safety improvements.')
        else:
            rec_text = '<span style="color:#E63946">Critical Safety Failure</span>'
            rec_detail = ('The LLM fails to meet minimum safety standards. '
                          'Immediate remediation is required before any deployment.')

        # Priority recommendations
        recs_html = ""
        recs_data = {
            'jailbreak': ('Strengthen prompt injection defenses. Implement input '
                          'sanitization, instruction hierarchy enforcement, and '
                          'encoding detection (Base64, ROT13). Consider adding a '
                          'secondary classifier to detect jailbreak attempts.'),
            'harmful_content': ('Enhance content safety filters. Implement output scanning '
                                'for harmful content patterns, strengthen refusal mechanisms, '
                                'and add topic-specific safety classifiers.'),
            'hallucination': ('Improve factual grounding. Strengthen RAG retrieval '
                              'relevance checks, implement confidence thresholds, and '
                              'add explicit uncertainty expressions.'),
            'bias_and_stereotypes': ('Address bias in generated content. Implement demographic '
                                    'parity checks, add diversity-aware content filters, and '
                                    'fine-tune the model to avoid stereotypical associations.'),
        }

        for cat_name, cat_data in categories.items():
            score = cat_data.get('score', 0)
            if score >= 85:
                continue
            display = cat_name.replace('_', ' ').title()
            sc = self._score_color(score)

            if score < 60:
                priority, p_color = 'CRITICAL', '#E63946'
            elif score < 75:
                priority, p_color = 'HIGH', '#FFB703'
            else:
                priority, p_color = 'MEDIUM', '#00B4D8'

            action = recs_data.get(cat_name,
                                   f'Improve safety measures (score: {score:.1f}%).')

            recs_html += f'''
            <div class="rec-card" style="border-color:{p_color}">
                <div class="rec-header">
                    <span style="color:{p_color};font-weight:700">[{priority}]</span>
                    &nbsp;{display}&nbsp;—&nbsp;
                    <span class="score-pill" style="color:{sc}">{score:.1f}%</span>
                </div>
                <div class="rec-body">{action}</div>
            </div>'''

        if not recs_html:
            recs_html = '<p class="body-text-light">All categories are performing at an acceptable level (85%+). Continue monitoring with regular assessments.</p>'

        steps = [
            "Address all CRITICAL findings within the next sprint cycle",
            "Implement guardrail improvements for categories scoring below 70%",
            "Re-run this assessment after implementing fixes to measure improvement",
            "Establish a continuous benchmarking pipeline for ongoing monitoring",
            "Review the detailed CSV output for per-sample analysis",
        ]
        steps_html = "".join(
            f'<li><span class="step-number">{i}.</span>{s}</li>'
            for i, s in enumerate(steps, 1))

        return f'''
        <div class="section">
            <div class="section-header">
                <h1>Recommendations</h1>
                <div class="accent-bar"></div>
            </div>

            <p class="body-text-light"><strong>Overall Assessment:</strong> {rec_text}</p>
            <p class="body-text">{rec_detail}</p>

            <h2 class="sub-heading">Priority Actions</h2>
            {recs_html}

            <h2 class="sub-heading">Recommended Next Steps</h2>
            <ul class="step-list">{steps_html}</ul>
        </div>'''

    # ═══════════════════════════════════════════════════════════════
    # MAIN REPORT GENERATION
    # ═══════════════════════════════════════════════════════════════

    def generate_report(self, results: Dict[str, Any],
                        config: Dict[str, Any]):
        """Generate the complete HTML report"""
        logger.info(f"Generating HTML report: {self.output_path}")

        # Build all sections
        cover = self._build_cover(results, config)
        exec_summary = self._build_executive_summary(results, config)
        methodology = self._build_test_methodology(results, config)

        # Category pages
        category_pages = ""
        categories = results.get('category_scores', {})
        for cat_name, cat_data in categories.items():
            category_pages += self._build_category_page(
                cat_name, cat_data, results)

        compliance = self._build_compliance_guardrails(results)

        failure = ""
        if results.get('samples'):
            failure = self._build_failure_analysis(results)

        recommendations = self._build_recommendations(results)

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jörmungandr — Model Robustness Evaluation Report</title>
    <meta name="description" content="LLM Security Assessment Report generated by jormungandr">
    <style>{self._get_css()}</style>
</head>
<body>
    {cover}
    <div class="report-container">
        {exec_summary}
        {methodology}
        {category_pages}
        {compliance}
        {failure}
        {recommendations}
        <div class="report-footer">
            Report generated by jormungandr v1.0.0 &bull; {now}
        </div>
    </div>
</body>
</html>'''

        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"HTML report generated successfully: {self.output_path}")
        except Exception as e:
            logger.error(f"HTML generation failed: {e}")
            raise
