"""Reproduce FINN's explicitly fictional PDFs for offline UI testing."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch

OUT = Path(__file__).resolve().parent.parent / 'examples'
OUT.mkdir(exist_ok=True)
st = getSampleStyleSheet()
st.add(ParagraphStyle(name='ReportTitle2', parent=st['Heading1'], fontSize=18, leading=23, textColor=colors.HexColor('#1C4C35'), spaceAfter=15))
st.add(ParagraphStyle(name='ReportBody2', parent=st['BodyText'], fontSize=10, leading=16, spaceAfter=12))
st.add(ParagraphStyle(name='SmallNote2', parent=st['BodyText'], fontSize=9, leading=13, textColor=colors.HexColor('#5C6D61'), spaceAfter=9))

def P(text, sty='ReportBody2'):return Paragraph(text,st[sty])
def write(name, heading, sections):
    dest=OUT/name
    doc=SimpleDocTemplate(str(dest),pagesize=(595,842),rightMargin=54,leftMargin=54,topMargin=62,bottomMargin=58,
                          title='FICTIONAL TRAINING MATERIAL - NOT A REAL COMPANY FILING')
    elements=[P('SYNTHETIC TRAINING CASE / NOT A REAL LISTED COMPANY','SmallNote2'),P(heading,'ReportTitle2'),
              P('<b>Asterra Devices Ltd. (DEMOCO)</b> is entirely fictional. Every number and management quote in this PDF is invented solely for demonstrating retrieval and traceability. This is NOT an NSE/BSE filing.','SmallNote2')]
    for title,paras,table in sections:
        elements.append(P(title,'Heading2'))
        for para in paras:elements.append(P(para))
        if table:
            t=Table(table,hAlign='LEFT',colWidths=[210]+[125]*(len(table[0])-1))
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8F3EB')),('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#1C4C35')),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#CDDCD0')),('PADDING',(0,0),(-1,-1),8),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9)]))
            elements.append(t);elements.append(Spacer(1,14))
    def stamp(canv,doc):
        canv.setFont('Helvetica',8);canv.setFillColor(colors.HexColor('#7C9684'))
        canv.drawString(54,38,'FINN / fictional practice corpus / never cite as an actual company disclosure')
        canv.drawRightString(540,38,f'Page {doc.page}')
    doc.build(elements,onFirstPage=stamp,onLaterPages=stamp)
    print(dest)

write('DEMOCO_Annual_Report_EXTRACT_FICTIONAL.pdf','FY2025 Annual Report - Training Extract',[
    ('Business overview',['Asterra Devices manufactures industrial sensors and sells maintenance subscriptions to fictional enterprise clients. Manufacturing represents 65% of FY2025 revenue and services 35%, compared with 70% and 30% respectively in FY2024.','The principal investment risk identified by management is a possible rise in component costs and a longer inventory holding period.'],None),
    ('Selected FY2025 financial figures',['Financial values below are invented and expressed in INR crore. They are for retrieval testing, not decision-making.'],[
        ['Metric (INR crore)','FY2024','FY2025'],['Revenue','1,000','1,210'],['EBITDA','170','205'],['Profit before tax','132','153'],['Profit after tax','95','110'],['Operating cash flow','130','82'],['Capital expenditure','70','110'],['Free cash flow','60','-28'],['Gross debt','180','260']]),
    ('Liquidity and working capital',['Inventory days increased from 45 in FY2024 to 58 in FY2025. Management attributed the increase to longer component lead times and pre-purchases. Operating cash flow declined from INR 130 crore to INR 82 crore even though net profit rose from INR 95 crore to INR 110 crore.','Free cash flow, defined for this exercise as operating cash flow less capital expenditure, was negative INR 28 crore in FY2025. This is an illustrative profit-versus-cash mismatch.'],None),
])
write('DEMOCO_Earnings_Call_Transcript_FICTIONAL.pdf','June 2025 Earnings Call - Training Transcript',[
    ('Opening - Chief Executive Officer',['CEO: For the fictional FY2026, we are guiding for 18% to 20% full-year revenue growth. This is management guidance and not a guaranteed result.','CEO: We are targeting an FY2026 EBITDA margin of 17% to 18%. We expect the services mix to support profitability, but input cost volatility remains a risk.'],None),
    ('Questions - Chief Financial Officer',['Analyst: FY2025 operating cash flow fell even though reported PAT rose. How should investors assess the cash conversion gap?','CFO: Inventory increased because we pre-bought components for expected customer orders. We expect operating cash conversion to recover during FY2026, although we are not giving a numerical cash-flow target.','Analyst: Is this cash-flow recovery embedded in the revenue growth guidance?','CFO: The full-year revenue guidance assumes execution of our order pipeline. Cash conversion is being managed separately, and the guidance does not guarantee a particular cash-flow outcome.'],None),
])
write('DEMOCO_Q2_Results_FICTIONAL.pdf','Q2 FY2026 Results - Training Extract',[
    ('Quarterly performance',['All values below are invented INR crore and correspond to the fictional periods shown. Q2 FY2026 means the quarter ended 30 September 2025 in this exercise.'],[
        ['Metric (INR crore)','Q2 FY2025','Q1 FY2026','Q2 FY2026'],['Revenue','270','300','321'],['EBITDA','46','52','53'],['Profit before tax','31','34','30'],['Profit after tax','24','26','23'],['Operating cash flow','32','19','12']]),
    ('Commentary and limitations',['Q2 FY2026 revenue grew 18.9% year on year and 7.0% quarter on quarter. Q2 FY2026 EBITDA margin was approximately 16.5%, versus approximately 17.3% in Q1 FY2026.','Management\'s 18% to 20% revenue growth and 17% to 18% EBITDA margin statements are full-year FY2026 guidance. A single quarter cannot conclusively determine whether full-year guidance will be met.','The operating cash flow of INR 12 crore in Q2 FY2026 was below both Q1 FY2026 and Q2 FY2025 in this fictional data, so the analyst should investigate management\'s expected cash recovery rather than presume it occurred.'],None),
])
