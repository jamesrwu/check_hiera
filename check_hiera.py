#!/usr/bin/env python
from collections import OrderedDict
import argparse
import os
import pprint
import re
import sys
import yaml


pp = pprint.PrettyPrinter(width=80)


def get_args():
    parser = argparse.ArgumentParser(description='check_hiera.py')
    subparsers = parser.add_subparsers(help='Action', dest='action')

    read = subparsers.add_parser('read', help='Read existing hiera structure')
    read.add_argument('hiera', help='Hiera.yaml file path')
    read.add_argument('root_path', help='Root directory of hiera hierarchy folder')
    read.add_argument('-k', '--key', help='Print only optional key value')
    read.add_argument('-o', '--output', help='Output the existing hiera structure into a yaml file')

    generate = subparsers.add_parser('generate', help='Generate existing structure defined in yaml file into a hiera '
                                                      'tree')
    generate.add_argument('input', help='Path of existing structure in yaml file')
    generate.add_argument('root_path', help='Root directory of hiera hierarchy folder. Must not exist.')
    return parser.parse_args()


def get_hierarchy(filename):
    with open(filename, 'r') as root_hiera:
        root_hiera_yaml = yaml.load(root_hiera)
    return root_hiera_yaml[':hierarchy']


def get_filepath_regex(hierarchy):
    """
    Returns matching list of regex which will be used to match file path is in which hierarchy
    """
    find_pattern = "\%\{\w*\}"
    replace_pattern = "[\w[\.]*]*"
    regex_list = []
    for item in hierarchy:
        pattern = re.sub(find_pattern, replace_pattern, item) + '.yaml$'
        regex_list.append(pattern)
    return regex_list


def build_hiera_hierarchy(root_path, hierarchy_regex):
    """
    Walks through the hiera root path to find files that are defined in the hiera hierarchy and catalogues all their key
    values
    """
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
    """
    Fancy print function that prints out a key in the global dictionary with the hierarchy ordered as defined in
    hiera.yaml
    """
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
    """
    Sort function that returns the numerical order of a key in the hierarchy
    """
    for order in range(0, len(hierachy_regex)):
        if re.findall(hierarchy_regex[order], item):
            return order
    else:
        return len(hierarchy_regex) + 1

if __name__ == "__main__":
    args = get_args()

    if args.action == 'read':
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

        if args.output:
            with open(args.output, 'w') as outfile:
                outfile.write(yaml.dump(global_dict, default_flow_style=False))
                print("File generated at %s" % args.output)
        else:
            if args.key is not None:
                output_yaml_key(global_dict, args.key, hierarchy_regex)
            else:
                for yaml_key in sorted(global_dict.keys()):
                    output_yaml_key(global_dict, yaml_key, hierarchy_regex)

    elif args.action == 'generate':
        if os.path.exists(args.root_path):
            sys.exit("Root path must not exist!")
        else:
            os.makedirs(args.root_path)
            os.chdir(args.root_path)
            with open(args.input, 'r') as input_file:
                global_dict = yaml.load(input_file)
            #{ file: {yaml_key: value}}
            yaml_files = {}
            for yaml_key in global_dict.keys():
                for filepath in global_dict[yaml_key].keys():
                    if filepath not in yaml_files:
                        yaml_files[filepath] = {yaml_key: global_dict[yaml_key][filepath]}
                    else:
                        yaml_files[filepath][yaml_key] = global_dict[yaml_key][filepath]
            for yaml_file in yaml_files.keys():
                parent_dir = "/".join(yaml_file.split('/')[0:-1])
                try:
                    os.makedirs(parent_dir)
                except FileExistsError:
                    pass
                finally:
                    with open(yaml_file, 'w') as outfile:
                        outfile.write(yaml.dump(yaml_files[yaml_file], default_flow_style=False, indent=4))
            print("Generated hiera structure at %s" % args.root_path)
