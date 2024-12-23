from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from requests import get, put
import os
import urllib.parse
import json


def run(handler_class=BaseHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


class HttpGetHandler(BaseHTTPRequestHandler):
    def get_uploaded_files(self):
        uploaded_files = set()
        if os.path.exists("uploaded_files.txt"):
            with open("uploaded_files.txt", "r") as file:
                uploaded_files = set(line.strip() for line in file)
        return uploaded_files

    def do_GET(self):
        def fname2html(fname, is_uploaded):
            background_color = "rgba(0, 200, 0, 0.25)" if is_uploaded else "transparent"
            return f"""
                <li onclick="fetch('/upload', {{'method': 'POST', 'body': '{fname}'}})" style="background-color: {background_color};">
                    {fname}
                </li>
            """
        uploaded_files = self.get_uploaded_files()

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("""
            <html>
                <head>
                </head>
                <body>
                    <ul>
                      {files} 
                    </ul>
                </body>
            </html>
        """.format(
            files="\n".join([fname2html(fname, fname in uploaded_files) for fname in os.listdir("pdfs")])
        ).encode())

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length'))
        fname = self.rfile.read(content_len).decode("utf-8")
        local_path = f"pdfs/{fname}"
        ya_path = f"upload/{urllib.parse.quote(fname)}"
        resp = get(f"https://cloud-api.yandex.net/v1/disk/resources/upload?path={ya_path}",
                   headers={"Authorization": "OAuth y0_AgAAAAA_flGQAADLWwAAAAEdWbZ3AADhs_ntCIFArIRLOg1RC4K8Vamf_A"})
        print(resp.text)
        upload_url = json.loads(resp.text)["href"]
        print(upload_url)
        resp = put(upload_url, files={'file': (fname, open(local_path, 'rb'))})
        print(resp.status_code)

        if resp.status_code == 201:
            with open("uploaded_files.txt", "a") as file:
                file.write(f"{fname}\n")

        self.send_response(200)
        self.end_headers()


run(handler_class=HttpGetHandler)
