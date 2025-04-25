# gauge_app/routes/anomalies.py
from flask import Blueprint, send_file
import io, statistics
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from gauge_app.services.mqtt_service import sensor_history, anomaly_log

bp = Blueprint('anomalies', __name__)

@bp.route('/anomalies/pdf')
def anomalies_pdf():
    buf = io.BytesIO()
    p   = canvas.Canvas(buf, pagesize=letter)
    width, height = letter

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Anomaly Log Summary")

    # Summary: for each topic, avg & peak
    y = height - 80
    p.setFont("Helvetica", 12)
    for topic, readings in sensor_history.items():
        if not readings: continue
        values = [v for (_, v) in readings]
        avg    = statistics.mean(values)
        peak   = max(values)
        trough = min(values)
        p.drawString(50, y, f"{topic}: avg={avg:.1f}, peak={peak}, low={trough}")
        y -= 20

    # Detailed anomalies
    y -= 10
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Anomalies:")
    y -= 20
    p.setFont("Helvetica", 10)
    for entry in anomaly_log[-50:]:   # last 50
        time_str = entry['time'].strftime("%Y-%m-%d %H:%M:%S")
        p.drawString(60, y,
            f"{time_str} | {entry['topic']} = {entry['value']}"
        )
        y -= 15
        if y < 50:
            p.showPage()
            y = height - 50

    p.save()
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="anomaly_log.pdf",
        mimetype="application/pdf"
    )
