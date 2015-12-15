# check_hiera
Tool for outputting your hiera hierarchies and (hopefully) help you organize your key values. Only supports yaml.

If you've ever worked with a somewhat large puppet repository, you may often have had to troubleshoot issues related to
redundant key/values being in places you did not expect. This tool helps you make sense of your hiera structure so that you can hopefully start keeping it more organized.

It parses your hiera.yaml to discover your hierarchy and will output keys and their location in the order of highest to lowest priority as defined in the hiera.yaml.

You can also use this to output all your hiera keys into a single file that you can then edit, and use as an input to regenerate a new hiera structure.

#### Requirements
1. Python3+ (python2 should work but is untested)
2. PyYaml (http://pyyaml.org)
3. Puppet repository with hiera using yaml


#### Example
```bash
usage: check_hiera.py read [-h] [-k KEY] [-o OUTPUT] hiera root_path

./check_hiera.py read puppet/hiera.yaml puppet/hiera/

keyA:
{'./environment/prod.yaml': 'running',
 './environment/qa.yaml': 'stopped',
 './defaults.yaml': 'stopped'}

keyB:
{'./nodeclass/webapp.yaml': 'abcd',
 './companyenv/qa.yaml': 'bcde',
 './companyenv/qa2.yaml': 'cdef',
 './companyenv/dev.yaml': 'defg',
 './defaults.yaml': 'abcd'}

packages:
{'./nodeclass/webapp.yaml': ['apache2', 'nginx'],
 './nodeclass/db.yaml': ['mysql-server', 'mysql'],
 './environment/prod.yaml': ['htop3',
                             'iotop',
                             'tcpdump'],
 './environment/qa.yaml': ['kvm'],
 './defaults.yaml': ['ssh-server', 'screen', 'puppet', 'curl']}


(If you toggle the -o yaml output, it will output into a yaml file)

 ```

#### Known bug(s):
1. Output of master.yaml does not maintain hierarchy ordering vs. regular output. This is a known issue in pyyaml and was marked as won't fix (http://pyyaml.org/ticket/29). 
