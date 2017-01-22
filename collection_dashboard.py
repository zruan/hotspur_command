#!/eppec/storage/sw/cky-tools/site/bin/python

import argparse
import http.server
import socketserver
import os

DATA_DIR = os.getcwd()
DATA_PREFIX = "/data"
ASSET_DIR = os.path.join(os.path.dirname(__file__), "collection_dashboard")


def arguments():
    def floatlist(string):
        return list(map(float, string.split(',')))

    parser = argparse.ArgumentParser(
        description='Serves Dashboard fom scratch directory')

    parser.add_argument(
        '--port', default=38010, help='Port to run webserver on')

    return parser.parse_args()


args = arguments()
print(args)


class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        print(path)
        if self.path.startswith(DATA_PREFIX):
            print(DATA_DIR + path[len(DATA_PREFIX):].split('?')[0])
            return DATA_DIR + path[len(DATA_PREFIX):].split('?')[0]
        else:
            if self.path == "" or self.path == '/':
                return ASSET_DIR + '/index.html'
            else:
                return ASSET_DIR + path.split('?')[0]


Handler = MyRequestHandler

httpd = socketserver.TCPServer(("", args.port), Handler)
print("serving at port", args.port)
httpd.serve_forever()
