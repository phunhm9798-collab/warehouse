"""
Forecast Routes
API endpoints for demand forecasting and report generation
"""
from flask import Blueprint, render_template, request, jsonify, Response
from models import db
from models.product import Product
from models.category import Category
from services.forecast_service import ForecastService
from datetime import datetime
import csv
import io

forecast_bp = Blueprint('forecast', __name__, url_prefix='/forecast')


@forecast_bp.route('/')
def index():
    """Render the forecast dashboard page."""
    return render_template('forecast.html')


@forecast_bp.route('/api/products')
def get_all_forecasts():
    """Get forecasts for all products."""
    history_days = request.args.get('history_days', 90, type=int)
    forecast_days = request.args.get('forecast_days', 30, type=int)
    algorithm = request.args.get('algorithm', 'exponential')
    
    service = ForecastService(db.session)
    forecasts = service.get_all_products_forecast(
        history_days=history_days,
        forecast_days=forecast_days,
        algorithm=algorithm
    )
    
    return jsonify({
        'count': len(forecasts),
        'parameters': {
            'history_days': history_days,
            'forecast_days': forecast_days,
            'algorithm': algorithm
        },
        'forecasts': forecasts
    })


@forecast_bp.route('/api/products/<int:product_id>')
def get_product_forecast(product_id):
    """Get detailed forecast for a specific product."""
    history_days = request.args.get('history_days', 90, type=int)
    forecast_days = request.args.get('forecast_days', 30, type=int)
    algorithm = request.args.get('algorithm', 'exponential')
    
    service = ForecastService(db.session)
    forecast = service.get_product_forecast(
        product_id,
        history_days=history_days,
        forecast_days=forecast_days,
        algorithm=algorithm
    )
    
    if not forecast:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify(forecast)


@forecast_bp.route('/api/categories')
def get_category_forecasts():
    """Get aggregated forecasts by category."""
    history_days = request.args.get('history_days', 90, type=int)
    forecast_days = request.args.get('forecast_days', 30, type=int)
    
    service = ForecastService(db.session)
    forecasts = service.get_category_forecast(
        history_days=history_days,
        forecast_days=forecast_days
    )
    
    return jsonify({
        'count': len(forecasts),
        'forecasts': forecasts
    })


@forecast_bp.route('/api/report')
def get_full_report():
    """Get comprehensive forecast report data."""
    history_days = request.args.get('history_days', 90, type=int)
    forecast_days = request.args.get('forecast_days', 30, type=int)
    algorithm = request.args.get('algorithm', 'exponential')
    
    service = ForecastService(db.session)
    report = service.generate_forecast_report_data(
        history_days=history_days,
        forecast_days=forecast_days,
        algorithm=algorithm
    )
    
    return jsonify(report)


@forecast_bp.route('/api/export/csv')
def export_csv():
    """Export forecast data as CSV."""
    history_days = request.args.get('history_days', 90, type=int)
    forecast_days = request.args.get('forecast_days', 30, type=int)
    algorithm = request.args.get('algorithm', 'exponential')
    
    service = ForecastService(db.session)
    forecasts = service.get_all_products_forecast(
        history_days=history_days,
        forecast_days=forecast_days,
        algorithm=algorithm
    )
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow([
        'SKU', 'Product Name', 'Category', 'Current Stock', 'Min Stock', 'Max Stock',
        'Avg Daily Demand', 'Forecast Period (days)', 'Daily Forecast', 'Total Forecast',
        'Safety Stock', 'Projected Stock', 'Restock Needed', 'Optimal Restock',
        'Days Until Stockout', 'Stock Status', 'Algorithm'
    ])
    
    # Data rows
    for f in forecasts:
        writer.writerow([
            f['product_sku'],
            f['product_name'],
            f['category'],
            f['current_stock'],
            f['min_stock'],
            f['max_stock'],
            f['avg_daily_demand'],
            f['forecast_days'],
            f['daily_forecast'],
            f['total_forecast'],
            f['safety_stock'],
            f['projected_stock'],
            f['restock_needed'],
            f['optimal_restock'],
            f['days_until_stockout'],
            f['stock_status'],
            f['algorithm']
        ])
    
    output.seek(0)
    filename = f"demand_forecast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@forecast_bp.route('/api/export/pdf')
def export_pdf():
    """Export forecast report as a professional PDF."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph, 
                                         Spacer, PageBreak, Image, HRFlowable)
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.graphics.shapes import Drawing, Rect, String
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.charts.barcharts import VerticalBarChart
    except ImportError:
        return jsonify({'error': 'PDF generation requires reportlab. Please install it with: pip install reportlab'}), 500
    
    history_days = request.args.get('history_days', 90, type=int)
    forecast_days = request.args.get('forecast_days', 30, type=int)
    algorithm = request.args.get('algorithm', 'exponential')
    
    service = ForecastService(db.session)
    report = service.generate_forecast_report_data(
        history_days=history_days,
        forecast_days=forecast_days,
        algorithm=algorithm
    )
    
    # Colors
    PRIMARY = colors.HexColor('#4f46e5')
    PRIMARY_LIGHT = colors.HexColor('#e0e7ff')
    SUCCESS = colors.HexColor('#10b981')
    SUCCESS_LIGHT = colors.HexColor('#d1fae5')
    WARNING = colors.HexColor('#f59e0b')
    WARNING_LIGHT = colors.HexColor('#fef3c7')
    DANGER = colors.HexColor('#ef4444')
    DANGER_LIGHT = colors.HexColor('#fee2e2')
    GRAY = colors.HexColor('#6b7280')
    GRAY_LIGHT = colors.HexColor('#f3f4f6')
    DARK = colors.HexColor('#1f2937')
    WHITE = colors.white
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        leftMargin=0.75*inch, 
        rightMargin=0.75*inch,
        topMargin=0.75*inch, 
        bottomMargin=0.75*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=32,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=GRAY,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=DARK,
        spaceBefore=20,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        borderPadding=(0, 0, 5, 0)
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=DARK,
        leading=14
    )
    
    # ========== COVER PAGE ==========
    elements.append(Spacer(1, 1.5*inch))
    
    # Company logo placeholder (decorative header)
    header_drawing = Drawing(500, 60)
    header_drawing.add(Rect(0, 20, 500, 40, fillColor=PRIMARY, strokeColor=None))
    header_drawing.add(String(250, 35, "WMS Pro", fontSize=24, fillColor=WHITE, textAnchor='middle', fontName='Helvetica-Bold'))
    elements.append(header_drawing)
    
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Demand Forecast Report", title_style))
    elements.append(Paragraph("Inventory Stocking & Replenishment Analysis", subtitle_style))
    
    elements.append(Spacer(1, 0.5*inch))
    
    # Report metadata box
    meta_data = [
        ['Report Generated', datetime.now().strftime('%B %d, %Y at %H:%M')],
        ['Analysis Period', f'Last {history_days} days of historical data'],
        ['Forecast Horizon', f'Next {forecast_days} days'],
        ['Forecasting Algorithm', algorithm.replace('_', ' ').title()],
        ['Total Products Analyzed', str(report['summary']['total_products'])]
    ]
    
    meta_table = Table(meta_data, colWidths=[2.5*inch, 4*inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), GRAY_LIGHT),
        ('TEXTCOLOR', (0, 0), (0, -1), DARK),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(meta_table)
    
    elements.append(Spacer(1, 1*inch))
    
    # Key findings summary on cover
    summary = report['summary']
    
    findings_title = ParagraphStyle('FindingsTitle', parent=section_title, alignment=TA_CENTER)
    elements.append(Paragraph("Key Findings at a Glance", findings_title))
    elements.append(Spacer(1, 0.2*inch))
    
    # KPI cards row
    kpi_data = [[
        f"📦\n{summary['total_products']}\nTotal Products",
        f"⚠️\n{summary['products_needing_restock']}\nNeed Restock",
        f"🚨\n{summary['critical_stockout_items']}\nCritical Risk",
        f"⏰\n{summary['warning_items']}\nWarning Items"
    ]]
    
    kpi_table = Table(kpi_data, colWidths=[1.6*inch, 1.6*inch, 1.6*inch, 1.6*inch])
    kpi_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (0, 0), PRIMARY_LIGHT),
        ('BACKGROUND', (1, 0), (1, 0), WARNING_LIGHT),
        ('BACKGROUND', (2, 0), (2, 0), DANGER_LIGHT),
        ('BACKGROUND', (3, 0), (3, 0), WARNING_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(kpi_table)
    
    # Footer on cover
    elements.append(Spacer(1, 1*inch))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=GRAY, alignment=TA_CENTER)
    elements.append(Paragraph("This report was automatically generated by the WMS Pro Forecasting Module", footer_style))
    elements.append(Paragraph("Confidential - For Internal Use Only", footer_style))
    
    # ========== PAGE 2: EXECUTIVE SUMMARY ==========
    elements.append(PageBreak())
    
    elements.append(Paragraph("Executive Summary", section_title))
    elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceBefore=5, spaceAfter=15))
    
    # Summary paragraph
    critical_pct = round(summary['critical_stockout_items'] / max(summary['total_products'], 1) * 100)
    restock_pct = round(summary['products_needing_restock'] / max(summary['total_products'], 1) * 100)
    
    exec_summary_text = f"""
    Based on analysis of <b>{history_days} days</b> of historical transaction data, this report provides 
    demand forecasts for the next <b>{forecast_days} days</b> using the <b>{algorithm.replace('_', ' ').title()}</b> 
    forecasting algorithm.
    <br/><br/>
    <b>Key Observations:</b><br/>
    • <b>{summary['total_products']}</b> products were analyzed across all categories<br/>
    • <b>{summary['products_needing_restock']}</b> products ({restock_pct}%) require restocking to meet forecasted demand<br/>
    • <b>{summary['critical_stockout_items']}</b> products ({critical_pct}%) are at critical stockout risk (≤7 days of inventory)<br/>
    • <b>{summary['warning_items']}</b> products are at warning level (≤14 days of inventory)
    """
    elements.append(Paragraph(exec_summary_text, body_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Recommendation box
    if summary['critical_stockout_items'] > 0:
        rec_box_color = DANGER_LIGHT
        rec_border = DANGER
        rec_text = f"""
        <b>⚠️ IMMEDIATE ACTION REQUIRED</b><br/><br/>
        {summary['critical_stockout_items']} products are at critical risk of stockout within the next 7 days. 
        Recommended actions:<br/>
        • Review the Critical Items section on the next page<br/>
        • Initiate emergency purchase orders for critical SKUs<br/>
        • Consider expedited shipping options to prevent stockouts
        """
    elif summary['products_needing_restock'] > 0:
        rec_box_color = WARNING_LIGHT
        rec_border = WARNING
        rec_text = f"""
        <b>📋 ACTION RECOMMENDED</b><br/><br/>
        {summary['products_needing_restock']} products need restocking to maintain optimal inventory levels.
        Recommended actions:<br/>
        • Schedule regular purchase orders based on restock quantities<br/>
        • Review reorder points for frequently flagged items
        """
    else:
        rec_box_color = SUCCESS_LIGHT
        rec_border = SUCCESS
        rec_text = """
        <b>✅ INVENTORY STATUS: HEALTHY</b><br/><br/>
        All products have adequate stock levels for the forecast period. 
        Continue monitoring with regular forecast reviews.
        """
    
    rec_data = [[Paragraph(rec_text, body_style)]]
    rec_table = Table(rec_data, colWidths=[6.5*inch])
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), rec_box_color),
        ('BOX', (0, 0), (-1, -1), 2, rec_border),
        ('PADDING', (0, 0), (-1, -1), 15),
    ]))
    elements.append(rec_table)
    
    # ========== PAGE 3: CRITICAL ITEMS ==========
    if report['critical_items']:
        elements.append(PageBreak())
        elements.append(Paragraph("🚨 Critical Items - Immediate Action Required", section_title))
        elements.append(HRFlowable(width="100%", thickness=2, color=DANGER, spaceBefore=5, spaceAfter=15))
        
        elements.append(Paragraph(
            f"The following {len(report['critical_items'])} products have less than 7 days of inventory remaining "
            "based on current demand patterns. Immediate restocking is recommended.",
            body_style
        ))
        elements.append(Spacer(1, 0.2*inch))
        
        critical_headers = ['SKU', 'Product Name', 'Current\nStock', 'Daily\nDemand', 'Days\nLeft', 'Recommended\nRestock']
        critical_data = [critical_headers]
        
        for item in report['critical_items']:
            days_left = item['days_until_stockout']
            urgency = '🔴' if days_left <= 3 else '🟠'
            critical_data.append([
                item['product_sku'],
                item['product_name'][:35],
                str(item['current_stock']),
                str(item['avg_daily_demand']),
                f"{urgency} {days_left}",
                str(item['restock_needed'])
            ])
        
        critical_table = Table(critical_data, colWidths=[1*inch, 2.5*inch, 0.7*inch, 0.7*inch, 0.7*inch, 1*inch])
        critical_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), DANGER),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -1), DANGER_LIGHT),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, DANGER_LIGHT]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#fca5a5')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(critical_table)
    
    # ========== PAGE 4: CATEGORY ANALYSIS ==========
    elements.append(PageBreak())
    elements.append(Paragraph("Category Analysis", section_title))
    elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceBefore=5, spaceAfter=15))
    
    elements.append(Paragraph(
        "Forecast demand aggregated by product category. Use this data to prioritize purchasing by category.",
        body_style
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    cat_headers = ['Category', 'Products', 'Historical\nDemand', 'Forecasted\nDemand', 'Current\nStock', 'Restock\nNeeded']
    cat_data = [cat_headers]
    
    for cat in report['by_category']:
        cat_data.append([
            cat['category_name'],
            str(cat['product_count']),
            str(int(cat['total_historical_demand'])),
            str(int(cat['total_forecast'])),
            str(cat['total_current_stock']),
            str(int(cat['total_restock_needed']))
        ])
    
    # Add totals row
    total_historical = sum(c['total_historical_demand'] for c in report['by_category'])
    total_forecast = sum(c['total_forecast'] for c in report['by_category'])
    total_stock = sum(c['total_current_stock'] for c in report['by_category'])
    total_restock = sum(c['total_restock_needed'] for c in report['by_category'])
    cat_data.append(['TOTAL', str(len(report['by_category'])), str(int(total_historical)), 
                     str(int(total_forecast)), str(total_stock), str(int(total_restock))])
    
    cat_table = Table(cat_data, colWidths=[1.5*inch, 0.8*inch, 1*inch, 1*inch, 0.9*inch, 0.9*inch])
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, -1), (-1, -1), PRIMARY_LIGHT),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [WHITE, GRAY_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c7d2fe')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(cat_table)
    
    # ========== PAGE 5: ALL PRODUCTS ==========
    elements.append(PageBreak())
    elements.append(Paragraph("Complete Product Forecast", section_title))
    elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceBefore=5, spaceAfter=15))
    
    elements.append(Paragraph(
        f"Detailed forecast for all {len(report['all_products'])} products, sorted by stockout urgency.",
        body_style
    ))
    elements.append(Spacer(1, 0.2*inch))
    
    detail_headers = ['SKU', 'Product', 'Category', 'Stock', 'Demand', 'Forecast', 'Days', 'Restock', 'Status']
    detail_data = [detail_headers]
    
    # Track status for color coding
    row_statuses = []
    
    for item in report['all_products']:
        # Status indicator
        days = item['days_until_stockout']
        if days <= 7:
            status = 'Critical'
            row_statuses.append('critical')
        elif days <= 14:
            status = 'Warning'
            row_statuses.append('warning')
        elif days <= 30:
            status = 'Monitor'
            row_statuses.append('monitor')
        else:
            status = 'OK'
            row_statuses.append('ok')
        
        detail_data.append([
            item['product_sku'],
            item['product_name'][:22],
            item['category'][:12],
            str(item['current_stock']),
            str(item['avg_daily_demand']),
            str(item['daily_forecast']),
            str(days) if days < 999 else '∞',
            str(item['restock_needed']) if item['restock_needed'] > 0 else '-',
            status
        ])
    
    detail_table = Table(detail_data, colWidths=[0.75*inch, 1.6*inch, 0.9*inch, 0.5*inch, 0.6*inch, 0.6*inch, 0.5*inch, 0.6*inch, 0.7*inch])
    
    # Base table style
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (8, 1), (8, -1), 'Helvetica-Bold'),  # Bold status column
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c7d2fe')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    
    # Add alternating row backgrounds (excluding status column)
    for row_idx in range(1, len(detail_data)):
        bg_color = WHITE if row_idx % 2 == 1 else GRAY_LIGHT
        table_style.append(('BACKGROUND', (0, row_idx), (7, row_idx), bg_color))
    
    # Add color-coded status cell backgrounds
    status_colors = {
        'critical': (DANGER, WHITE),       # Red background, white text
        'warning': (WARNING, DARK),         # Orange background, dark text
        'monitor': (colors.HexColor('#fef08a'), DARK),  # Yellow background, dark text
        'ok': (SUCCESS, WHITE)              # Green background, white text
    }
    
    for row_idx, status in enumerate(row_statuses, start=1):
        bg_color, text_color = status_colors[status]
        table_style.append(('BACKGROUND', (8, row_idx), (8, row_idx), bg_color))
        table_style.append(('TEXTCOLOR', (8, row_idx), (8, row_idx), text_color))
    
    detail_table.setStyle(TableStyle(table_style))
    elements.append(detail_table)
    
    # ========== FINAL PAGE: METHODOLOGY ==========
    elements.append(PageBreak())
    elements.append(Paragraph("Methodology & Definitions", section_title))
    elements.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceBefore=5, spaceAfter=15))
    
    method_text = f"""
    <b>Forecasting Algorithm: {algorithm.replace('_', ' ').title()}</b><br/><br/>
    
    <b>Algorithm Descriptions:</b><br/>
    • <b>Exponential Smoothing:</b> Applies decreasing weights to older observations, ideal for general-purpose forecasting<br/>
    • <b>Simple Moving Average (SMA):</b> Averages the last N days of demand, best for stable patterns<br/>
    • <b>Weighted Moving Average (WMA):</b> Gives higher weight to recent data, good for trending products<br/>
    • <b>Linear Regression:</b> Projects trend lines, suitable for growing or declining demand<br/>
    • <b>Holt-Winters:</b> Captures both level and trend, handles seasonal patterns<br/><br/>
    
    <b>Key Metrics:</b><br/>
    • <b>Daily Demand:</b> Average units sold per day (historical)<br/>
    • <b>Daily Forecast:</b> Predicted units to be sold per day (future)<br/>
    • <b>Days Until Stockout:</b> Current stock ÷ Daily forecast<br/>
    • <b>Safety Stock:</b> Buffer inventory calculated at 95% service level<br/>
    • <b>Restock Needed:</b> Minimum quantity to prevent stockout
    """
    elements.append(Paragraph(method_text, body_style))
    
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Status Color Legend:</b>", body_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Visual color legend table
    legend_data = [
        ['Status', 'Days of Inventory', 'Action Required'],
        ['Critical', '≤ 7 days', 'Immediate action - initiate emergency purchase order'],
        ['Warning', '8-14 days', 'Plan reorder soon - schedule purchase order'],
        ['Monitor', '15-30 days', 'Monitor closely - include in next order cycle'],
        ['OK', '> 30 days', 'No action needed - healthy stock levels']
    ]
    
    legend_table = Table(legend_data, colWidths=[1.2*inch, 1.3*inch, 4*inch])
    legend_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#c7d2fe')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        # Color-coded status cells
        ('BACKGROUND', (0, 1), (0, 1), DANGER),
        ('TEXTCOLOR', (0, 1), (0, 1), WHITE),
        ('BACKGROUND', (0, 2), (0, 2), WARNING),
        ('TEXTCOLOR', (0, 2), (0, 2), DARK),
        ('BACKGROUND', (0, 3), (0, 3), colors.HexColor('#fef08a')),
        ('TEXTCOLOR', (0, 3), (0, 3), DARK),
        ('BACKGROUND', (0, 4), (0, 4), SUCCESS),
        ('TEXTCOLOR', (0, 4), (0, 4), WHITE),
        # Light backgrounds for other cells
        ('BACKGROUND', (1, 1), (-1, 1), DANGER_LIGHT),
        ('BACKGROUND', (1, 2), (-1, 2), WARNING_LIGHT),
        ('BACKGROUND', (1, 3), (-1, 3), colors.HexColor('#fefce8')),
        ('BACKGROUND', (1, 4), (-1, 4), SUCCESS_LIGHT),
    ]))
    elements.append(legend_table)
    
    elements.append(Spacer(1, 0.5*inch))
    
    # Disclaimer
    disclaimer_style = ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=8, textColor=GRAY, alignment=TA_CENTER)
    elements.append(Paragraph(
        "This forecast is based on historical data and statistical modeling. Actual demand may vary due to factors not captured in the model. "
        "Review forecasts regularly and adjust for known events, promotions, or market changes.",
        disclaimer_style
    ))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"demand_forecast_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

