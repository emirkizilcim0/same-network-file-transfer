import http.server
import socket
import os
from urllib.parse import unquote
import cgi

class FileServerHandler(http.server.SimpleHTTPRequestHandler):
    UPLOAD_DIR = "downloads"  # Specify the upload directory

    def do_GET(self):
        """Serve files and an HTML form for upload."""
        if self.path == "/":
            # Serve the main page
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>File Server</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            margin: 0;
                            padding: 0;
                            background-color: #f4f4f9;
                            color: #333;
                            animation: fadeIn 1.5s ease-in-out;
                        }
                        @keyframes fadeIn {
                            from { opacity: 0; }
                            to { opacity: 1; }
                        }
                        header {
                            background: linear-gradient(135deg, #007bff, #0056b3);
                            color: #fff;
                            padding: 20px;
                            text-align: center;
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        }
                        main {
                            margin: 20px;
                            padding: 20px;
                            background: #fff;
                            border-radius: 8px;
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                            animation: fadeIn 1.5s ease-in-out;
                        }
                        h1, h2 {
                            color: #444;
                        }
                        form {
                            margin: 20px 0;
                            padding: 15px;
                            background: #f9f9f9;
                            border: 1px solid #ddd;
                            border-radius: 8px;
                            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                        }
                        input[type="file"] {
                            margin: 10px 0;
                        }
                        button {
                            background: #28a745;
                            color: #fff;
                            border: none;
                            padding: 10px 20px;
                            font-size: 16px;
                            border-radius: 5px;
                            cursor: pointer;
                            transition: background 0.3s;
                        }
                        button:hover {
                            background: #218838;
                        }
                        ul {
                            list-style: none;
                            padding: 0;
                        }
                        li {
                            background: #fff;
                            margin: 5px 0;
                            padding: 10px;
                            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                            border-radius: 5px;
                        }
                        li a {
                            text-decoration: none;
                            color: #007bff;
                            transition: color 0.3s;
                        }
                        li a:hover {
                            color: #0056b3;
                        }
                    </style>
                </head>
                <body>
                    <header>
                        <h1>Modern File Server</h1>
                    </header>
                    <main>
                        <h2>Upload Files</h2>
                        <form method="post" enctype="multipart/form-data">
                            <input type="file" name="file" multiple>
                            <button type="submit">Upload</button>
                        </form>
                        <h2>Download Files</h2>
                        <ul>
            """)
            # List files in the downloads directory for download
            if not os.path.exists(self.UPLOAD_DIR):
                os.makedirs(self.UPLOAD_DIR)
            for file_name in os.listdir(self.UPLOAD_DIR):
                file_path = os.path.join(self.UPLOAD_DIR, file_name)
                if os.path.isfile(file_path):
                    self.wfile.write(f'<li><a href="{self.UPLOAD_DIR}/{file_name}">{file_name}</a></li>'.encode())
            self.wfile.write(b"""
                        </ul>
                    </main>
                </body>
                </html>
            """)
        else:
            # Serve files for download
            super().do_GET()

    def do_POST(self):
        """Handle file uploads."""
        content_type = self.headers.get("Content-Type")
        # "multipart/form-data" is used to get any type of files. It is more complicated compared to other formats.
        if not content_type or "multipart/form-data" not in content_type:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Invalid request, Content-Type must be multipart/form-data.")
            return

        _, params = cgi.parse_header(content_type)
        # The boundaries is specified according to html format that we've chosen. (Currently multipart/form-data)
        boundary = params["boundary"].encode()
        # We need the length to have acknowledge about how much bytes that we are going to upload.
        content_length = int(self.headers["Content-Length"])
        data = self.rfile.read(content_length)

        # Ensure the uploads directory exists
        if not os.path.exists(self.UPLOAD_DIR):
            os.makedirs(self.UPLOAD_DIR)

        # Process multipart form data
        parts = data.split(b"--" + boundary)
        for part in parts:
            if b"Content-Disposition" in part:
                headers, file_data = part.split(b"\r\n\r\n", 1)
                headers = headers.decode()
                filename = None
                for header in headers.split("\r\n"):
                    if "Content-Disposition" in header:
                        _, disposition_params = cgi.parse_header(header)
                        filename = disposition_params.get("filename")
                
                if filename:
                    filename = unquote(filename)
                    if filename.strip():  # Ensure filename is not empty
                        filepath = os.path.join(self.UPLOAD_DIR, filename)
                        with open(filepath, "wb") as f:
                            f.write(file_data.rstrip(b"\r\n--"))

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Upload successful.\n")


def get_local_ip():
    """Get the local IP address of the current machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to connect; it's used to find the local interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    port = 8080
    ip_address = get_local_ip()
    os.chdir(os.getcwd())
    httpd = http.server.HTTPServer((ip_address, port), FileServerHandler)
    print(f"Serving HTTP on {ip_address} port {port} (http://{ip_address}:{port}) ...")
    httpd.serve_forever()
