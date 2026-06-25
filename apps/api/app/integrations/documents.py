"""Document generators — Invoice PDF and Shipping Label PDF using fpdf2."""
from __future__ import annotations

import io
from datetime import datetime


def _header(pdf, title: str) -> None:
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "SellerMate", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, "Bangladesh F-Commerce OS", ln=True)
    pdf.ln(3)
    pdf.set_fill_color(37, 99, 235)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 9, f"  {title}", ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)


def _kv(pdf, key: str, val: str) -> None:
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(50, 7, key + ":", border=0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 7, str(val), ln=True, border=0)


def generate_invoice(order: dict, items: list[dict], merchant_name: str) -> bytes:
    from fpdf import FPDF  # type: ignore[import]

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)

    _header(pdf, "INVOICE / চালান")

    _kv(pdf, "Invoice No", f"INV-{order.get('order_number', 'N/A')}")
    _kv(pdf, "Date", datetime.utcnow().strftime("%d %b %Y"))
    _kv(pdf, "Merchant", merchant_name)
    pdf.ln(3)

    _kv(pdf, "Order #", order.get("order_number", ""))
    _kv(pdf, "Status", order.get("status", ""))
    _kv(pdf, "Customer", order.get("customer_name", ""))
    _kv(pdf, "Address", order.get("delivery_address") or "")
    _kv(pdf, "District", order.get("delivery_district") or "")
    _kv(pdf, "Payment", order.get("payment_method", "COD"))
    pdf.ln(5)

    # Items table header
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(80, 8, "Product", border=1, fill=True)
    pdf.cell(20, 8, "Qty", border=1, fill=True, align="C")
    pdf.cell(35, 8, "Unit Price", border=1, fill=True, align="R")
    pdf.cell(35, 8, "Total", border=1, fill=True, align="R")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    subtotal = 0.0
    for item in items:
        name = (item.get("product_name") or item.get("name", ""))[:40]
        qty = int(item.get("quantity", 1))
        unit = float(item.get("unit_price") or 0)
        total = float(item.get("total_price") or unit * qty)
        subtotal += total
        pdf.cell(80, 7, name, border=1)
        pdf.cell(20, 7, str(qty), border=1, align="C")
        pdf.cell(35, 7, f"Tk {unit:.0f}", border=1, align="R")
        pdf.cell(35, 7, f"Tk {total:.0f}", border=1, align="R")
        pdf.ln()

    pdf.ln(2)
    shipping = float(order.get("shipping_cost") or 0)
    discount = float(order.get("discount_amount") or 0)
    total_amt = float(order.get("total_amount") or subtotal + shipping - discount)

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(135, 7, "Subtotal", border=0, align="R")
    pdf.cell(35, 7, f"Tk {subtotal:.0f}", border=1, align="R"); pdf.ln()
    if discount > 0:
        pdf.cell(135, 7, "Discount", border=0, align="R")
        pdf.cell(35, 7, f"- Tk {discount:.0f}", border=1, align="R"); pdf.ln()
    pdf.cell(135, 7, "Shipping", border=0, align="R")
    pdf.cell(35, 7, f"Tk {shipping:.0f}", border=1, align="R"); pdf.ln()
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(135, 8, "TOTAL", border=0, align="R")
    pdf.cell(35, 8, f"Tk {total_amt:.0f}", border=1, align="R", fill=False); pdf.ln()

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "Thank you for your business! - SellerMate Bangladesh", align="C")

    return pdf.output(dest="S").encode("latin-1")


def generate_shipping_label(order: dict, tracking_id: str, courier: str, merchant_name: str) -> bytes:
    from fpdf import FPDF  # type: ignore[import]

    pdf = FPDF()
    pdf.add_page("P", "A6")
    pdf.set_margins(8, 8, 8)

    _header(pdf, "SHIPPING LABEL")

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "FROM:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, merchant_name, ln=True)
    pdf.cell(0, 5, "Bangladesh", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, "TO:", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, order.get("customer_name", "Customer"), ln=True)
    addr = order.get("delivery_address") or ""
    if addr:
        for line in [addr[i:i+35] for i in range(0, min(len(addr), 105), 35)]:
            pdf.cell(0, 5, line, ln=True)
    pdf.cell(0, 5, order.get("delivery_district") or "", ln=True)
    pdf.cell(0, 5, "Bangladesh", ln=True)
    pdf.ln(4)

    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Tracking: {tracking_id}", ln=True, fill=True, align="C")
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(0, 5, f"Courier: {courier.upper()}  |  Order: {order.get('order_number', '')}", ln=True, align="C")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    total = order.get("total_amount", 0)
    method = order.get("payment_method", "COD")
    pdf.cell(0, 7, f"Amount: Tk {float(total):.0f}  ({method})", ln=True, align="C")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 7)
    pdf.cell(0, 5, "Generated by SellerMate | sellermate.app", ln=True, align="C")

    return pdf.output(dest="S").encode("latin-1")
