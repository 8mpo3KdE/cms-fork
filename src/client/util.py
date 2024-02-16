import uuid
import json
import logging

log = logging.getLogger("cms")


def is_uuid(s):
    try:
        uuid.UUID(s)
        return True
    except:
        return False


def parser_init(res_sub_p, parents, schema):
    for res in schema.keys():
        res_p = res_sub_p.add_parser(res, help = res)
        res_p.set_defaults(res_class=schema[res]["res-class"])
        op_sub_p = res_p.add_subparsers(title="Operation",
                metavar="<operation>")
        for op in schema[res].keys():
            if op == "res-class":
                continue
            op_p = op_sub_p.add_parser(op, parents=parents, help=op)
            op_p.set_defaults(op=op)
            for arg in schema[res][op]:
                if not "attr" in arg:
                    arg["attr"] = {}
                op_p.add_argument(arg["name"], **arg["attr"])


def import_param(param_list, args):
    data = {}
    for p in param_list:
        if getattr(args, p) is not None:
            data[p] = getattr(args, p)
    return data


def output(args, data):
    if not data:
        return
    if args.format == "json":
        print(json.dumps(data))
    else:
        if type(data) == list:
            col_list = data[0].keys()
            if args.column:
                col_list = args.column
            print("\t".join(col_list))
            for i in data:
                l = []
                for c in col_list:
                    if c in i:
                        l.append(str(i[c]))
                    else:
                        l.append("None")
                print("\t".join(l))
        elif type(data) == dict:
            col_list = data.keys()
            if args.column:
                col_list = args.column
            for c in col_list:
                if c in data:
                    print(f"{c}: {data[c]}")
                else:
                    print(f"{c}: None")


def parse_kvs(s):
    kvs = s.split(",")
    d = {}
    for i in kvs:
        k = i.split("=")[0]
        v = i.split("=")[1]
        d[k] = v
    return d

