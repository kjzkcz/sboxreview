#!/usr/bin/python3
# =============================================================================
# Author: Ashkan Mirzaee
# Organization: University of Missouri RCSS
# License: GPL-3.0
# Date: 2021/07/09
# Source: https://github.com/ashki23/sbox
# =============================================================================

import os
import sys
import json
import pathlib
import argparse

with open(f'{pathlib.Path(__file__).parent.absolute()}/config') as cfg:
    config = json.load(cfg)

jupyter_partition = list(config['jupyter_partition_timelimit'].keys())
jupyter_timelimt = max(list(config['jupyter_partition_timelimit'].values()))
interactive_partition = list(config['interactive_partition_timelimit'].keys())
interactive_timelimt = max(list(config['interactive_partition_timelimit'].values()))
user = os.getenv('USER')
home = os.getenv('HOME')
host_name = os.popen('hostname').read().strip()

parser = argparse.ArgumentParser(description = 'An alias for using cluster interactively', formatter_class = lambda prog: argparse.HelpFormatter(prog,max_help_position = 56), epilog = 'Command should be run from the login node.')
parser.add_argument('-A', '--account', default = 'general', help = 'account name', metavar = '')
parser.add_argument('-n', '--ntasks', type = int, default = 1, help = 'number of tasks (cpus)', metavar = '')
parser.add_argument('-N', '--nodes', type = int, default = 1, help = 'number of nodes', metavar = '')
if 'jupyter' in sys.argv:
    parser.add_argument('-p', '--partition', choices = jupyter_partition, default = jupyter_partition[0], help = 'partition name', metavar = '')
    parser.add_argument('-t', '--time', type = int, choices = range(1, jupyter_timelimt + 1), default = 2, help = f'number of hours (up to {jupyter_timelimt})', metavar = '')
    parser.add_argument('-k', '--kernel', choices = ['R','Python'], default = 'Python', help = 'Jupyter kernel (R/Python)', metavar = '')
else:
    parser.add_argument('-p', '--partition', choices = interactive_partition, default = interactive_partition[0], help = 'partition name', metavar = '')
    parser.add_argument('-t', '--time', type = int, choices = range(1, interactive_timelimt + 1), default = 2, help = f'number of hours (up to {interactive_timelimt})', metavar = '')
    parser.add_argument('-l', '--license', help = 'license', metavar = '')
parser.add_argument('-m', '--mem', type = int, default = 2, help = 'amount of memory per GB', metavar = '')
parser.add_argument('-g', '--gpu', type = int, default = 0, choices = range(3), help = 'number of gpus', metavar = '')
parser.add_argument('jupyter', nargs = '?', help = 'Starting Jupyter server on the cluster')
args = parser.parse_args()

if args.partition in config['partition_qos'].keys():
    qos = config['partition_qos'][args.partition]
else:
    qos = 'normal'

if args.account == 'general' and args.partition in config['partition_general_account_deny']:
    print(f"General account not allowed to use partitions {', '.join(config['partition_general_account_deny'])}. Use another account or change the partiton.")
    sys.exit(1)

if args.partition not in config['gpu_partition'] and args.gpu > 0:
    print(f"For using gpu resources select one of the gpu partitions ({', '.join(config['gpu_partition'])}).")
    sys.exit(1)

if args.partition in config['gpu_partition'] and args.gpu == 0:
    args.gpu = 1

if args.partition in config['gpu_partition']:
    announce = f"Logging into {args.partition} partition with {args.gpu} gpu, {args.mem}G memory, {args.ntasks} cpu and using account {args.account} for {args.time} hours ..."
else:
    announce = f"Logging into {args.partition} partition with {args.mem}G memory, {args.ntasks} cpu and using account {args.account} for {args.time} hours ..."

## INTERACTIVE
if not args.jupyter:
    partition_timelimit = config['interactive_partition_timelimit'][args.partition]
    if args.time > partition_timelimit:
        print(f"Partition time limit. Max time for {args.partition} partition is {partition_timelimit} hours.")
        sys.exit(1)
    
    if 'login' not in host_name:
        print('Command should be run from the login node')
        sys.exit(1)
    
    if args.license:
        print(announce)
        os.system(f"srun --partition {args.partition} --qos {qos} --gres gpu:{args.gpu} --ntasks {args.ntasks} --nodes {args.nodes} --mem {args.mem}G --time {args.time}:00:00 --account {args.account} --licenses {args.license}:1 --pty /bin/bash")
    
    if not args.license:
        print(announce)
        os.system(f"srun --partition {args.partition} --qos {qos} --gres gpu:{args.gpu} --ntasks {args.ntasks}  --nodes {args.nodes} --mem {args.mem}G --time {args.time}:00:00 --account {args.account} --pty /bin/bash")

## JUPYTER
if args.jupyter:
    partition_timelimit = config['jupyter_partition_timelimit'][args.partition]
    if args.time > partition_timelimit:
        print(f"Partition time limit. Max time for {args.partition} partition is {partition_timelimit} hours.")
        sys.exit(1)
    
    if args.kernel == 'R':
        kernel = 'r'
        module = 'r-essentials'
    else:
        kernel = 'py'
        module = 'anaconda'
    
    ml_test = os.popen(f"if [ -z `module load {module} > /dev/null 2>&1 && which jupyter-lab 2> /dev/null` ]; then echo 'no-module-found'; fi").read().strip()
    if ml_test == 'no-module-found':
        print(f"No {module} module found!")
        sys.exit(1)
    
    os.system(f"install -d ~/.jupyter/job")
    with open(f"{home}/.jupyter/job/{kernel}-jupyter-job",'w') as jb:
        jb.write(f"""#!/bin/bash
#SBATCH --job-name jupyter-{kernel}
#SBATCH --account {args.account}
#SBATCH --partition {args.partition}
#SBATCH --ntasks {args.ntasks}
#SBATCH --nodes {args.nodes}
#SBATCH --mem {args.mem}G
#SBATCH --gres gpu:{args.gpu}
#SBATCH --qos {qos}
#SBATCH --time {args.time}:00:00
#SBATCH --output {home}/.jupyter/job/{kernel}-%j.out
module load {module}
jupyter-lab --no-browser --ip 0.0.0.0
        """)
    
    os.system(f"""
cd ~
rm -f ~/.jupyter/job/{kernel}-*.out
jid=$(sbatch --parsable ~/.jupyter/job/{kernel}-jupyter-job)
echo {announce}
echo "Starting Jupyter server (it might take about a couple minutes) ..."
myn=0
while ! grep -iq 'use control-c' ~/.jupyter/job/{kernel}-$jid.out > /dev/null 2>&1; do
sleep 10
if squeue -j $jid | grep -q AccountNotAllowed; then echo "{args.account} account not allowed to use {args.partition}. Use another account or change the partition"; exit; fi
echo "Starting Jupyter server ..."
myn=`expr $myn + 1`
if [ $myn -eq 15 ]; then
echo "
It is taking more than usual to start the server.
The following shows the status of your job in the queue:
"
squeue -j $jid
echo "
You can wait more if your job is waiting for resources (Priority or Resources) or cancel the job and try again.
To Cancel your job press 'Control+C' and run 'scancel $jid'.
"
fi
done
unset jid myn i
cd - > /dev/null 2>&1
    """)

    jid = os.popen("ls -t ~/.jupyter/job/%s-*.out 2> /dev/null | head -n 1 | grep -Po '(?<=job/%s-).*(?=.out)'" % (kernel,kernel)).read().strip()
    port = os.popen("cat ~/.jupyter/job/%s-%s.out 2> /dev/null | grep '\[.*\].http://' | grep -Po '(?<=http://).*' | grep -Po '(?<=:)\d{4}(?=/?)'" % (kernel,jid)).read().strip()
    host = os.popen(f"cat ~/.jupyter/job/{kernel}-{jid}.out 2> /dev/null | grep '\[.*\].http://' | grep -Po '(?<=http://).*' | grep -Po '.*(?=:)'").read().strip()
    url = os.popen(f"cat ~/.jupyter/job/{kernel}-{jid}.out 2> /dev/null | grep '\[.*\].*or.*http://' | grep -Po '(?<=or ).*'").read().strip()
    
    if len(jid) > 0:
        print(f"""
Jupyter Notebook is running.

Open a new terminal in your local computer and run:
ssh -NL {port}:{host}:{port} {user}@lewis.rnet.missouri.edu

After that open a browser and go:
{url}

To stop the server run the following on the cluster:
scancel {jid}
        """)
