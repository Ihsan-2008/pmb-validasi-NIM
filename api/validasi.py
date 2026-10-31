import json
import os
import uuid
from http.server import BaseHTTPRequestHandler

EKSTENSI_DIIZINKAN = {"pdf", "jpg", "jpeg", "png"}
ID_INSTANCE = uuid.uuid4().hex[:8]


def batas_kb():
    return int(os.environ.get("BATAS_KB", "2048"))


def periksa_berkas(nama_berkas, ukuran_kb):
    masalah = []
    ekstensi = ""
    if "." in nama_berkas:
        ekstensi = nama_berkas.rsplit(".", 1)[-1].lower()
    if ekstensi not in EKSTENSI_DIIZINKAN:
        label = ekstensi or "tanpa ekstensi"
        masalah.append("format " + label + " tidak diizinkan")
    if ukuran_kb > batas_kb():
        masalah.append("ukuran melebihi batas " + str(batas_kb()) + " KB")
    return masalah


def validasi(event):
    nomor = event.get("nomor_pendaftaran")
    berkas = event.get("berkas", [])
    if not nomor or not berkas:
        pesan = "nomor_pendaftaran dan berkas wajib diisi"
        return 400, {"pesan": pesan}
    laporan = []
    for item in berkas:
        nama = item.get("nama", "")
        masalah = periksa_berkas(nama, int(item.get("ukuran_kb", 0)))
        laporan.append(
            {"nama": nama, "valid": not masalah, "masalah": masalah}
        )
    semua_valid = all(x["valid"] for x in laporan)
    print(json.dumps(
        {"nomor": nomor, "semua_valid": semua_valid, "instance": ID_INSTANCE}
    ))
    body = {
        "nomor_pendaftaran": nomor,
        "semua_valid": semua_valid,
        "rincian": laporan,
        "id_instance": ID_INSTANCE,
    }
    return 200, body


class handler(BaseHTTPRequestHandler):
    def kirim(self, status, body):
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        info = {
            "pesan": "Kirim POST berisi JSON nomor_pendaftaran dan berkas",
            "batas_kb": batas_kb(),
            "id_instance": ID_INSTANCE,
        }
        self.kirim(200, info)

    def do_POST(self):
        panjang = int(self.headers.get("Content-Length", 0))
        mentah = self.rfile.read(panjang)
        try:
            event = json.loads(mentah or b"{}")
        except json.JSONDecodeError:
            self.kirim(400, {"pesan": "badan permintaan bukan JSON yang sah"})
            return
        status, body = validasi(event)
        self.kirim(status, body)
