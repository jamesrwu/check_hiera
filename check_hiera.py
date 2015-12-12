#!/usr/bin/env python
from collections import OrderedDict
import argparse
import os
import pprint
import re
import yaml

pp = pprint.PrettyPrinter(width=80)

def get_args():
    parser = argparse.ArgumentParser(description='check_hiera.py')
    parser.add_argument('hiera', help='Hiera.yaml file path')
    parser.add_argument('root_path', help='Root directory of hiera hierarchy folder')
    parser.add_argument('-k', '--key', help='Print only optional key value')
    return parser.parse_args()


def get_hierarchy(filename):
    with open(filename, 'r') as root_hiera:
        root_hiera_yaml = yaml.load(root_hiera)
    return root_hiera_yaml[':hierarchy']


def get_filepath_regex(hierarchy):
    find_pattern = "\%\{\w*\}"
    replace_pattern = "[\w[\.]*]*"
    regex_list = []
    for item in hierarchy:
        pattern = re.sub(find_pattern, replace_pattern, item) + '.yaml$'
        regex_list.append(pattern)
    return regex_list


def build_hiera_hierarchy(root_path, hierarchy_regex):
    hiera_hierarchy = OrderedDict()
    # Initialize
    for regex in hierarchy_regex:
        hiera_hierarchy[regex] = []

    os.chdir(str(root_path))
    for path, dirs, files in os.walk('.'):
        for filename in files:
            path_file = "%s/%s" % (path, filename)
            for regex in hiera_hierarchy.keys():
                if re.findall(regex, path_file):
                    hiera_hierarchy[regex].append(path_file)
    return hiera_hierarchy


def output_yaml_key(dictionary, yaml_key, hierarchy_regex):
    print("%s:" % yaml_key)
    if len(dictionary[yaml_key]) > 1:
        ordered_dict = OrderedDict()
        ordered_keys = sorted(dictionary[yaml_key].keys(), key=lambda x: get_regex_order(x, hierarchy_regex))
        for key in ordered_keys:
            ordered_dict[key] = dictionary[yaml_key][key]
        pp.pprint(ordered_dict)
    else:
        pp.pprint(dictionary[yaml_key])
    print()


def get_regex_order(item, hierachy_regex):
    for order in range(0, len(hierachy_regex)):
        if re.findall(hierarchy_regex[order], item):
            return order
    else:
        return len(hierarchy_regex) + 1

if __name__ == "__main__":
    args = get_args()

    hierarchy = get_hierarchy(args.hiera)
    hierarchy_regex = get_filepath_regex(hierarchy)
    hierarchy_dict = build_hiera_hierarchy(args.root_path, hierarchy_regex)

    # format: {hiera_key: {hostname: value}}
    global_dict = {}
    for key in reversed(hierarchy_dict):
        for filename in hierarchy_dict[key]:
            with open(filename, 'r') as yaml_file:
                yaml_dict = yaml.load(yaml_file)
                if yaml_dict is None:
                    print("Found empty file at %s" % filename)
                else:
                    for yaml_key in yaml_dict:
                        if yaml_key in global_dict:
                            global_dict[yaml_key][filename] = yaml_dict[yaml_key]
                        else:
                            global_dict[yaml_key] = {filename: yaml_dict[yaml_key]}

    if args.key is not None:
        output_yaml_key(global_dict, args.key, hierarchy_regex)
    else:
        for yaml_key in sorted(global_dict.keys()):
            output_yaml_key(global_dict, yaml_key, hierarchy_regex)
