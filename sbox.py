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

part_cpu = config['cpu_partition']
part_gpu = config['gpu_partition']
user = os.getenv('USER')

parser = argparse.ArgumentParser(description = 'Small toolbox for Slurm users.', formatter_class = lambda prog: argparse.HelpFormatter(prog,max_help_position = 56))
parser.add_argument('-a', '--account', action = 'store_true', help = 'show slurm accounts')
parser.add_argument('-f', '--fairshare', action = 'store_true', help = 'show fairshare')
parser.add_argument('-g', '--group', action = 'store_true',  help = 'show posix groups')
parser.add_argument('-q', '--queue', action = 'store_true', help = 'show jobs in the queue')
parser.add_argument('-j', '--job', type = int, help = 'show a running/pending job info', metavar = 'JOBID')
parser.add_argument('-c', '--cpu', action = 'store_true', help = 'show computational resources')
parser.add_argument('-p', '--partition', action = 'store_true', help = 'show partitions')
parser.add_argument('-u', '--user', nargs = '?', default = user, help = 'user id', metavar = 'UID')
parser.add_argument('-v', '--version', action = 'version', version = '%(prog)s 1.2')
parser.add_argument('--eff', type = int, help = 'show efficiency of a job', metavar = 'JOBID')
parser.add_argument('--history', choices = ['day','week','month','year'], help = 'show jobs history for last day/week/month/year')
parser.add_argument('--pending', action = 'store_true', help = 'show pending jobs')
parser.add_argument('--running', action = 'store_true', help = 'show running jobs')
parser.add_argument('--qos', action = 'store_true', help = 'show quality of services')
parser.add_argument('--quota', action = 'store_true', help = 'show quotas')
parser.add_argument('--ncpu', action = 'store_true', help = 'show number of available cpus')
parser.add_argument('--ngpu', action = 'store_true', help = 'show number of available gpus')
parser.add_argument('--gpu', action = 'store_true', help = 'show gpu resources')
parser.add_argument('--license', action = 'store_true', help = 'show available licenses')
parser.add_argument('--reserve', action = 'store_true', help = 'show reservation')
parser.add_argument('--topusage', action = 'store_true', help = 'show top usage users')
parser.add_argument('--whodat', help = 'show users informations by uid', metavar = 'UID')
parser.add_argument('--whodat2', help = 'show users informations by name', metavar = 'NAME')
parser.add_argument('--agent', choices = ['start','stop','list'], help = 'start/stop/list ssh-agents on the current host')
args = parser.parse_args()

if len(sys.argv) == 1:
    parser.print_help(sys.stderr)
    sys.exit(1)

if args.account:
    print(' Accounts '.center(90,'-'))
    os.system(f"""
    sacctmgr show assoc -np user={args.user} format=account | tr "|\n" " " && echo
    echo
    """)

if args.fairshare:
    print(' Fairshare '.center(90,'-'))
    os.system(f"""
    sshare -Uu {args.user}
    echo
    """)

if args.group:
    print(' Groups '.center(90,'-'))
    os.system(f"""
    groups {args.user}
    echo
    """)

if args.queue:
    print(' Jobs in the Queue '.center(90,'-'))
    os.system(f"""
    squeue -u {args.user}
    echo
    """)

if args.job:
    print(' Job Info '.center(90,'-'))
    os.system(f"""
    scontrol -dd show job {args.job}
    """)

if args.cpu:
    print(' CPU/Mem per Node '.center(90,'-'))
    os.system("""
    sjstat -c
    echo
    """)

if args.partition:
    print(' Partitions '.center(90,'-'))
    os.system("""
    sinfo -o "%15P %6a %12l %F"
    echo
    """)

if args.eff:
    print(' Job Efficiency '.center(90,'-'))
    os.system(f"""
    install -d ~/.seff
    rm -f ~/.seff/seff.out
    if sacct -Xj {args.eff} | grep -iq "COMPLETED"; then
    seff {args.eff}
    else
    cat > ~/.seff/seff-job.sh <<EOF
#!/bin/bash
#SBATCH --jobid {args.eff}
top -u $USER -b -n 1 > ~/.seff/seff.out
EOF
    sleep 0.1
    if squeue -j {args.eff} | grep -q '0:00'; then
    echo 'Job is not running. Retry when the job is started!'
    exit
    fi
    srun --jobid {args.eff} /bin/bash ~/.seff/seff-job.sh
    while [ ! -f ~/.seff/seff.out ]; do
    sleep 0.5
    done
    cat ~/.seff/seff.out | grep -P "$USER|PID" | grep -v top | grep -v slurm_scri
    echo
    echo 'RES: shows resident memory which is accurate representation of how much actual physical memory a process is consuming'
    echo '%CPU: shows the percentage of the CPU that is being used by the process'
    fi
    echo
    """)

if args.history:
    print(f" Jobs History - Last {args.history.capitalize()} ".center(123,'-'))
    os.system(f"""
    sacct --user {args.user} --state bf,ca,cd,dl,f,nf,pr,s,to --allocations --format jobid%10,user%6,account%7,state%10,partition%9,qos%7,ncpus%5,nnodes%5,reqmem%5,submit,reserved,start,elapsed,end,nodelist%30,jobname%15 -S $(date --date='{args.history} ago' +"%Y-%m-%d")
    echo
    """)

if args.running:
    print(' Running Jobs '.center(90,'-'))
    os.system(f"""
    sacct --user {args.user} --state R --allocations --format jobid%10,user%6,account%7,state%10,partition%9,qos%7,ncpus%5,nnodes%5,reqmem%5,submit,reserved,start,elapsed,Timelimit,nodelist%30,jobname%15
    """)

if args.pending:
    print(' Pending Jobs '.center(90,'-'))
    os.system(f"""
    squeue --user {args.user} --states PENDING --sort S --format "%10i %6u %7a %10T %9P %7q %5C %5D %5m %20V %20S %30Y %10r %j"
    """)

if args.qos:
    print(' QOS '.center(90,'-'))
    os.system(f"""
    sacctmgr show assoc format=account%15,share%7,qos%56 user={args.user}
    echo "\n The following shows information about the available quality of services (QOS):\n"
    sacctmgr show qos format=Name%16,MaxWall,MaxSubmit,GrpTRES%8,GrpJobs,MaxTRES,MaxTRESPU,MaxJobsPU,MaxSubmit
    echo "\n Note that blank means there is no limit."
    echo
    """)

if args.ncpu:
    print(' Number of CPUs '.center(90,'-'))
    for p in part_cpu:
        idle = os.popen(f"""
        sinfo --partition {p} --Node --format %C | cut --delimiter '/' --fields 2,4 | tr '/' ' ' | awk '{{ sum1 += $1; sum2 += $2 }} END {{ print sum1, sum2 }}'
        """).read().strip().split()
        if int(idle[1]) > 0:
            print('Partition ',p,' has ',idle[0],' cpus available out of ',idle[1],' (',round((int(idle[0])/int(idle[1]))*100),'%)',sep='')
    print()

if args.ngpu:
    print(' Number of GPUs '.center(90,'-'))
    for g in part_gpu:
        unavail = os.popen(f"""
        squeue -O jobid,partition,gres,state,username | grep RUNNING | grep -i {g} | awk '{{ print $3 }}' | awk 'BEGIN{{ FS=":" }} {{ total+=$2 }} END{{ print total }}'
        """).read().strip()
        try:
            unavail = int(unavail)
        except ValueError:
            unavail = 0
        
        total = os.popen(f"""
        sinfo -p {g} -o %n,%G | grep -Po '(?<=:)\d' | awk '{{ sum1 += $1 }} END {{ print sum1 }}'
        """).read().strip()
        try:
            total = int(total)
        except ValueError:
            total = 0
        
        avail = total - unavail
        print('Partition ',g,' has ',avail,' gpus available out of ',total,' (',round((avail/total)*100),'%)',sep='')
    print()

if args.gpu:
    print(' GPU Resources '.center(90,'-'))
    os.system("""
    sinfo -p Gpu -o %n,%G
    echo
    """)

if args.license:
    print(' Licenses '.center(90,'-'))
    os.system("""
    scontrol show licenses
    echo
    """)

if args.reserve:
    print(' Reservations '.center(90,'-'))
    os.system("""
    scontrol show reserv
    """)

if args.topusage:
    print(' Top Usage '.center(90,'-'))
    os.system("""
    sreport user topusage
    """)

if args.whodat:
    print(' User Info '.center(90,'-'))
    os.system(f"""
    if [ -z `which ldapsearch 2> /dev/null` ]; then echo "ldapsearch is not availble."; exit; fi
    ldapsearch -x -LLL "(uid=*{args.whodat}*)"
    """)

if args.whodat2:
    print(' User Info '.center(90,'-'))
    os.system(f"""
    if [ -z `which ldapsearch 2> /dev/null` ]; then echo "ldapsearch is not availble."; exit; fi
    ldapsearch -x -LLL "(gecos=*{args.whodat2}*)"
    """)

if args.quota:
    disk_quota = config['disk_quota_paths']
    gpn = os.popen(f"""
    echo $(groups {args.user} | grep -Po "(?<=: ).*")
    """).read().strip().split()
    if args.user == user:
        if args.user not in gpn:
            for d in disk_quota:
                os.system(f"""
                rm -f ~/.quota
                lfs quota -hu {user} {d} > ~/.quota 2> /dev/null
                if [ -s ~/.quota ]; then
                if ! grep -q " 0. * 0. * 0. " ~/.quota; then
                python3 -c "print(' {user} {d} storage '.center(95,'-'))"
                cat ~/.quota | grep -Pv "setting|gid|uid";
                python3 -c "print(''.center(95,'-'))"; fi
                else if [ -d {d}/{user} ]; then
                python3 -c "print(' {user} {d} storage '.center(95,'-'))"
                df -h --output="file,used,pcent,avail,size,fstype" {d}/{user} | tr -s ' ' ',' | sed -e 's/^/,,,/' | column -t -s ',';
                python3 -c "print(''.center(95,'-'))"; fi
                fi
                """)
        
        for g in gpn:
            for d in disk_quota:
                os.system(f"""
                rm -f ~/.quota
                lfs quota -hg {g} {d} > ~/.quota 2> /dev/null
                if [ -s ~/.quota ]; then
                if ! grep -q " 0. * 0. * 0. " ~/.quota; then
                python3 -c "print(' {g} {d} storage '.center(95,'-'))"
                cat ~/.quota | grep -Pv "setting|gid|uid";
                python3 -c "print(''.center(95,'-'))"; fi
                else if [ -d {d}/{g} ]; then
                python3 -c "print(' {g} {d} storage '.center(95,'-'))"
                df -h --output="file,used,pcent,avail,size,fstype" {d}/{g} | tr -s ' ' ',' | sed -e 's/^/,,,/' | column -t -s ',';
                python3 -c "print(''.center(95,'-'))"; fi
                fi
                """)
    
    else:
        print(' Home Storage '.center(122,'-'))
        if args.user in gpn:
            lfsq = 'g'
        else:
            lfsq = 'u'
        os.system(f"""
        rm ~/.quota
        lfs quota -h{lfsq} {args.user} {disk_quota[0]} > ~/.quota 2> /dev/null
        if [ -s ~/.quota ]; then
        if ! grep -q " 0. * 0. * 0. " ~/.quota; then
        cat ~/.quota | grep -Pv "setting|gid|uid";
        python3 -c "print(''.center(122,'-'))"; fi
        else if [ -d {disk_quota[0]}/{args.user} ]; then
        df -h --output="file,used,pcent,avail,size,fstype" {disk_quota[0]}/{args.user} | tr -s ' ' ',' | sed -e 's/^/,,,/' | column -t -s ',';
        python3 -c "print(''.center(122,'-'))"; fi
        fi
        """)
        
        gpn = ' '.join(gpn)
        os.system(f"""
        if [ -z `which rcss-lfs-quota 2> /dev/null` ]; then echo "No rcss-lfs-quota found! You may try the command from the login node.\n"; exit; fi
        python -c "print(' HPC Storage '.center(122,'-'))"
        rcss-lfs-quota {gpn[:]}
        echo
        """)

if args.agent:
    if args.agent == 'start':
        os.system("""
        if [ -z `which ssh-agent 2> /dev/null` ]; then echo "No ssh-agent found!"; exit; fi
        if [ -f ~/.ssh/id_rsa ]; then
        if ! ps -elf | grep ssh-agent | grep -v grep | grep -q $USER; then
        echo "Starting an agent on $(hostname) ..."
        install -d ~/.ssh_auth
        eval `ssh-agent -s`
        ssh-add
        echo $SSH_AUTH_SOCK > ~/.ssh_auth/$(hostname)
        if ! grep -q SSH_AUTH_SOCK ~/.bashrc; then
        echo "
# >>> ssh-agent >>>
if [ -f ~/.ssh_auth/\$(hostname) ]; then
export SSH_AUTH_SOCK=\`cat ~/.ssh_auth/\$(hostname)\`
fi
# <<< ssh-agent <<<
" >> ~/.bashrc
        fi
        echo "The ssh-agent authentication is added to ~/.bashrc. $(tput bold)Run 'source ~/.bashrc' to apply the changes.$(tput sgr0)"
        else
        if [ -z $SSH_AUTH_SOCK ]; then
        echo "An agent is running but the authentication is not available. Stop the agent with -k and rerun the command."
        fi
        echo "The ssh-agent is running on $(hostname)."
        fi
        else
        echo "SSH keys not found. Add your id_rsa keys to '~/.ssh'."
        fi
        """)

    if args.agent == 'stop':
        os.system("""
        if ps -elf | grep ssh-agent | grep -v grep | grep -q $USER; then
        echo "Stopping the current agent on $(hostname) ..."
        kill `ps -elf | grep ssh-agent | grep -v grep | grep $USER | awk '{print $4}'`
        rm -f ~/.ssh_auth/$(hostname)
        else
        echo "No running agent found on $(hostname)."
        fi
        """)

    if args.agent == 'list':
        os.system("""
        if ps -elf | grep ssh-agent | grep -v grep | grep -q $USER; then
        ps -elf | grep ssh-agent | grep -v grep | grep $USER
        else
        echo "No running agent found on $(hostname)."
        fi
        """)
