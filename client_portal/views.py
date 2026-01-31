from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from ledger.models import Account, LedgerEntry
from transfers.models import (
    Beneficiary,
    ExternalWireRequest
    )

from admin_panel.models import FundingInstruction

from django.utils.dateparse import parse_date
from django.http import HttpResponse
import csv

from django.utils import timezone
from datetime import datetime, time


from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfgen import canvas
from io import BytesIO

from django.contrib.staticfiles import finders
import os

from reportlab.lib.utils import ImageReader



@login_required
def dashboard(request):
    accounts = Account.objects.filter(customer=request.user)

    dashboard_accounts = []

    for acc in accounts:
        dashboard_accounts.append({
            "currency":acc.currency,
            "available":acc.available_balance,
            "transit": acc.transit_balance,
            "held": acc.held_balance,
            "total":acc.total_balance()
        })
    
    context ={
        "accounts" : dashboard_accounts
    }

    return render(request, "client/dashboard.html", context)




@login_required
def funding_instructions(request):
    instruction = FundingInstruction.objects.first()


    return render(request, "client/funding/instructions.html",{
        "instruction": instruction
    })



@login_required
def statement_view(request):
    entries = []
    start = end = None

    if request.method == "GET" and "from" in request.GET:
        start = parse_date(request.GET.get("from"))
        end = parse_date(request.GET.get("to"))


        entries = LedgerEntry.objects.filter(
            account__customer = request.user,
            created_at__date__gte = start,
            created_at__date__lte = end
        ).order_by('created_at')

    return render(request, "client/statements/index.html",{
        "entries":entries,
        "start":start,
        "end":end
    })


@login_required
def statement_csv(request):
    start = parse_date(request.GET.get("from"))
    end = parse_date(request.GET.get("to"))

    entries = LedgerEntry.objects.filter(
        account__customer=request.user,
        created_at__date__gte=start,
        created_at__date__lte=end
    ).order_by("created_at")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=statement.csv"

    writer = csv.writer(response)
    writer.writerow(["Date", "Type", "Amount", "Reference"])

    for e in entries:
        writer.writerow([
            e.created_at.strftime("%Y-%m-%d"),
            e.entry_type,
            e.amount,
            e.reference
        ])

    return response


#for generating pdf for client

# @login_required
# def statement_pdf(request):
#     start = parse_date(request.GET.get("from"))
#     end = parse_date(request.GET.get("to"))


#     entries = LedgerEntry.objects.filter(
#         account__customer = request.user,
#         created_at__date__gte = start,
#         created_at__date__lte = end
#     ).order_by("created_at")


#     buffer = BytesIO()
#     p = canvas.Canvas(buffer, pagesize=A4)

#     y = 800
#     p.setFont("Helvetica-Bold", 14)
#     p.drawString(50, y, "Prominence Bank - Account Statement")
#     y -= 30

#     p.setFont("Helvetica", 10)
#     p.drawString(50,y, f"Period: {start} to {end}")
#     y -=30

#     for e in entries:
#         if y< 50:
#             p.showPage()
#             y = 800

#         line = f"{e.created_at.date()} | {e.entry_type} | {e.amount} | {e.reference}"
#         p.drawString(50, y, line)
#         y -= 18

#     p.showPage()
#     p.save()

#     buffer.seek(0)
#     response = HttpResponse(buffer, content_type="application/pdf")
#     response["Content-Disposition"] = "attachment; filename=statement.pdf"
#     return response










#for testing



def _page_header_footer(canvas, doc, bank_name="Prominence Bank"):
    page_w, page_h = A4

    # --- WATERMARK (logo) ---
    watermark_path = getattr(doc, "watermark_path", None)
    if watermark_path and os.path.exists(watermark_path):
        canvas.saveState()
        try:
            canvas.setFillAlpha(0.08)  # faint
        except Exception:
            pass

        wm_size = 90 * mm
        canvas.translate(page_w / 2, page_h / 2)
        canvas.rotate(30)
        canvas.drawImage(
            watermark_path,
            -wm_size / 2, -wm_size / 2,
            wm_size, wm_size,
            preserveAspectRatio=True,
            mask="auto"
        )
        canvas.restoreState()

    # --- HEADER BAR ---
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#0B2A4A"))
    canvas.rect(0, page_h - 22*mm, page_w, 22*mm, stroke=0, fill=1)

    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(18*mm, page_h - 14*mm, bank_name)

    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(page_w - 18*mm, page_h - 14*mm, "Account Statement")

    # --- FOOTER ---
    canvas.setFillColor(colors.grey)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18*mm, 12*mm, "This is a system-generated statement and does not require a signature.")
    canvas.drawRightString(page_w - 18*mm, 12*mm, f"Page {doc.page}")
    canvas.restoreState()



def _fmt_money(amount):
    # customize currency formatting if you like
    return f"{amount:,.2f}"


def _entry_label(entry_type: str) -> str:
    # nicer labels
    return (entry_type or "").replace("_", " ").title()


def _page_header_footer(canvas, doc, bank_name="Prominence Bank"):
    page_w, page_h = A4

    # ONE saveState for the whole function
    canvas.saveState()
    try:
        # --- WATERMARK ---
        watermark_path = getattr(doc, "watermark_path", None)
        # if watermark_path and os.path.exists(watermark_path):
        #     try:
        #         wm_size = 110 * mm
        #         canvas.saveState()
        #         canvas.translate(page_w / 2, page_h / 2)
        #         canvas.rotate(30)

        #         img = ImageReader(watermark_path)
        #         canvas.drawImage(
        #             img,
        #             -wm_size / 2, -wm_size / 2,
        #             wm_size, wm_size,
        #             preserveAspectRatio=True,
        #             mask="auto"
        #         )
        #         canvas.restoreState()
        #     except Exception:
        #         # If watermark fails, don't break PDF generation
        #         pass
        if watermark_path and os.path.exists(watermark_path):
            try:
                img = ImageReader(watermark_path)
                wm_w = 150 * mm
                wm_h = 140 * mm

                x = (page_w - wm_w) / 2
                y = (page_h - wm_h) / 2

                angle = 0  # degrees (try 5–20)

                canvas.saveState()

                # Move origin to the watermark center, rotate, then draw centered at (0,0)
                cx = x + wm_w / 2
                cy = y + wm_h / 2
                canvas.translate(cx, cy)
                canvas.rotate(angle)

                canvas.drawImage(
                    img,
                    -wm_w / 2, -wm_h / 2,  # draw centered after transform
                    wm_w, wm_h,
                    mask="auto",
                    preserveAspectRatio=True
                )

                canvas.restoreState()
            except Exception:
                pass

        # --- HEADER BAR ---
        canvas.setFillColor(colors.HexColor("#0B2A4A"))
        canvas.rect(0, page_h - 22*mm, page_w, 22*mm, stroke=0, fill=1)

        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(18*mm, page_h - 14*mm, bank_name)

        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(page_w - 18*mm, page_h - 14*mm, "Account Statement")

        # --- FOOTER ---
        canvas.setFillColor(colors.grey)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(
            18*mm, 12*mm,
            "This is a system-generated statement and does not require a signature."
        )
        canvas.drawRightString(page_w - 18*mm, 12*mm, f"Page {doc.page}")

    finally:
        # ONE restoreState for the whole function
        canvas.restoreState()


@login_required
def statement_pdf(request):
    start = parse_date(request.GET.get("from"))
    end = parse_date(request.GET.get("to"))

    # sensible defaults if missing
    if not start or not end:
        # last 30 days by default
        today = timezone.localdate()
        end = end or today
        start = start or (today - timezone.timedelta(days=30))

    if start > end:
        start, end = end, start

    # Use datetime range (better than created_at__date__gte/lte)
    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(start, time.min), tz)
    end_dt = timezone.make_aware(datetime.combine(end, time.max), tz)

    entries = (LedgerEntry.objects
        .select_related("account")
        .filter(
            account__customer=request.user,
            created_at__range=(start_dt, end_dt),
        )
        .order_by("created_at", "id")
    )

    # Try to get account info (assuming all entries are for one account; if not, adapt)
    first_entry = entries.first()
    account = getattr(first_entry, "account", None)

    customer_name = (
        request.user.get_full_name().strip()
        or getattr(request.user, "username", "Customer")
    )
    account_no = getattr(account, "number", "—")
    currency = getattr(account, "currency", "—")

    # Build PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18*mm,
        rightMargin=18*mm,
        topMargin=30*mm,   # leave space for header bar
        bottomMargin=18*mm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="Small",
        parent=styles["Normal"],
        fontSize=9,
        leading=12
    ))
    styles.add(ParagraphStyle(
        name="Meta",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#1f2937"),
        leading=12
    ))
    styles.add(ParagraphStyle(
        name="Title2",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#0B2A4A"),
        spaceAfter=6
    ))

    story = []

    # Customer / statement metadata block
    story.append(Spacer(1, 8*mm))
    story.append(Paragraph("Statement Details", styles["Title2"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D1D5DB")))
    story.append(Spacer(1, 4*mm))

    meta_table = Table(
        [
            ["Customer Name:", customer_name, "Statement Period:", f"{start} to {end}"],
            ["Account No:", str(account_no), "Currency:", str(currency)],
            ["Generated On:", str(timezone.localtime().date()), "Generated By:", "Online Banking"],
        ],
        colWidths=[30*mm, 60*mm, 35*mm, 45*mm],
        hAlign="LEFT",
    )
    # meta_table.setStyle(TableStyle([
    #     ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
    #     ("FONTSIZE", (0,0), (-1,-1), 9),
    #     ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#111827")),
    #     ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F3F4F6")),
    #     ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
    #     ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
    #     ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    #     ("LEFTPADDING", (0,0), (-1,-1), 8),
    #     ("RIGHTPADDING", (0,0), (-1,-1), 8),
    #     ("TOPPADDING", (0,0), (-1,-1), 6),
    #     ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    # ]))

    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (-1,-1), colors.HexColor("#111827")),

        # removed BACKGROUND to allow watermark behind

        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))


    story.append(meta_table)
    story.append(Spacer(1, 6*mm))

    # Transactions table
    story.append(Paragraph("Transaction History", styles["Title2"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D1D5DB")))
    story.append(Spacer(1, 4*mm))

    rows = [["Date & Time", "Description", "Reference", "Amount"]]

    total_in = 0
    total_out = 0

    for e in entries:
        dt = timezone.localtime(e.created_at).strftime("%Y-%m-%d %H:%M")
        desc = _entry_label(getattr(e, "entry_type", ""))
        ref = getattr(e, "reference", "") or "—"
        amt = getattr(e, "amount", 0)

        # if your system uses negative for debits, this works.
        # If you use separate debit/credit, adjust accordingly.
        try:
            if amt >= 0:
                total_in += amt
            else:
                total_out += abs(amt)
        except Exception:
            pass

        rows.append([dt, desc, ref, _fmt_money(amt)])

    if len(rows) == 1:
        rows.append(["—", "No transactions found in this period.", "—", "—"])

    tx_table = Table(
        rows,
        colWidths=[35*mm, 55*mm, 50*mm, 30*mm],
        repeatRows=1
    )
    # tx_table.setStyle(TableStyle([
    #     ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    #     ("FONTSIZE", (0,0), (-1,0), 9),
    #     ("TEXTCOLOR", (0,0), (-1,0), colors.white),
    #     ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0B2A4A")),
    #     ("ALIGN", (-1,1), (-1,-1), "RIGHT"),
    #     ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    #     ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
    #     ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FAFB")]),
    #     ("LEFTPADDING", (0,0), (-1,-1), 6),
    #     ("RIGHTPADDING", (0,0), (-1,-1), 6),
    #     ("TOPPADDING", (0,0), (-1,-1), 6),
    #     ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    # ]))


    tx_table.setStyle(TableStyle([
        # Header row (keep solid)
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 9),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0B2A4A")),

        # Body row text
        ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,1), (-1,-1), 9),

        # Alignment
        ("ALIGN", (-1,1), (-1,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),

        # Borders
        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),

        # IMPORTANT: remove ROWBACKGROUNDS so body is transparent
        # ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FAFB")]),

        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(tx_table)
    story.append(Spacer(1, 6*mm))

    # Totals / summary
    summary = Table(
        [
            ["Summary", ""],
            ["Total Credits", _fmt_money(total_in)],
            ["Total Debits", _fmt_money(total_out)],
        ],
        colWidths=[50*mm, 30*mm],
        hAlign="RIGHT"
    )
    # summary.setStyle(TableStyle([
    #     ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#F3F4F6")),
    #     ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    #     ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
    #     ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
    #     ("FONTSIZE", (0,0), (-1,-1), 9),
    #     ("ALIGN", (1,1), (1,-1), "RIGHT"),
    #     ("LEFTPADDING", (0,0), (-1,-1), 8),
    #     ("RIGHTPADDING", (0,0), (-1,-1), 8),
    #     ("TOPPADDING", (0,0), (-1,-1), 6),
    #     ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    # ]))


    summary.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),

        # removed BACKGROUND to allow watermark behind
        # ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#F3F4F6")),

        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#D1D5DB")),
        ("INNERGRID", (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
        ("ALIGN", (1,1), (1,-1), "RIGHT"),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(summary)

    # logo_path = finders.find("images/logo.png")
    logo_path = finders.find("images/logo_outline.png")
    print(logo_path)
    doc.watermark_path = logo_path  # can be None safely

    doc.build(story, onFirstPage=_page_header_footer, onLaterPages=_page_header_footer)

    # doc.build(
    #     story,
    #     onFirstPage=_page_header_footer,
    #     onLaterPages=_page_header_footer
    # )

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=statement.pdf"
    return response