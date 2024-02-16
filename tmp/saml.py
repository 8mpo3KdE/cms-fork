import argparse
import base64
import io
import urllib.parse
import zlib

def decode(args):
    print("---- query decode ----")
    req_dict = urllib.parse.parse_qs(f"request={args.req}")
    print(f"req: {req_dict}")
    print("---- base64 decode ----")
    v_1 = base64.b64decode(req_dict["request"][0])
    print(f"v_1 type: {type(v_1)}")
    print(f"v_1 value: {v_1}")
    print("---- decompress ----")
    v_2 = zlib.decompress(v_1, -8)
    print(f"v_2 type: {type(v_2)}")
    print(f"v_2 value: {v_2}")
    print("---- bytes decode to string ----")
    v_3 = v_2.decode('utf-8')
    print(f"v_3 type: {type(v_3)}")
    print(f"v_3 value: {v_3}")
    print("---")
    print("---")


    print("---- string encode to bytes ----")
    v4 = bytes(v_3, 'utf-8')
    print(f"v_4 type: {type(v4)}")
    print(f"v_4 value: {v4}")
    print("---- compress ----")
    c = zlib.compressobj(wbits=-9)
    v5 = c.compress(v4)
    v5 += c.flush()
    #v5 = zlib.compress(v4)
    print(f"v5 type: {type(v5)}")
    print(f"v5 value: {v5}")
    print("---- base64 encode ----")
    v6 = base64.b64encode(v5)
    print(f"v6 type: {type(v6)}")
    print(f"v6 value: {v6}")
    print("---- query encode ----")
    v7 = urllib.parse.quote_plus(v6)
    print(f"v7 type: {type(v7)}")
    print(f"v7 value: {v7}")

    #v10 = base64.b64decode(v6)
    #v11 = zlib.decompress(v10)
    #v12 = v11.decode('utf-8')
    #print(f"v11 type: {type(v11)}")
    #print(f"v11 value: {v11}")
    #print("---")

    #xml = zlib.decompress(base64.b64decode(v), -8).decode('utf-8')
    #buf = io.BytesIO(xml.encode('utf-8'))
    #print(buf.getvalue())
    #doc = etree.parse(buf)
    #print(etree.tostring(doc.getroot(), pretty_print=True).decode('utf-8'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decode SAML Requests")
    parser.add_argument(
        "req",
        action='store',
        help="The SAML request string.")
    args = parser.parse_args()
    decode(args)

