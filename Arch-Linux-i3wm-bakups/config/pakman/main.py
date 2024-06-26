#!/usr/bin/python3

import os, sys, subprocess as sp, json
from pkg_list_maker import main as pkg_list_maker


message_type = {
    "success": 32,
    "worning": 33,
    "error": 31
}
execute = True


def print_message(msg_type: str, message, error_code: int = False, kill: bool = True):
    print(f"\033[1;{message_type[msg_type]}m[pan {msg_type}]\033[0m: {message}\033[0m", end='')

    if error_code:
        print(f"[error code {error_code}]")

    if (msg_type != "success") and (kill):
        print("Exetting...")
        exit()

    if (not kill) and (msg_type != "success"):
        print()


mainDir = os.path.dirname(os.path.abspath(__file__))
important_files = {
    "main": "main.py",
    "norms": "norms.json",
    "pkg_list_maker": "pkg_list_maker.py",
    "settings": "settings.json",
    "manual": "manual.txt"
}

for i in list(important_files.values()):
    if (not os.path.exists(os.path.join(mainDir, i))):
        print_message("error", f"Missing reqirements: \033[1m{i}", 1)


norms_file_path = os.path.join(mainDir, important_files["norms"])
settings_file_path = os.path.join(mainDir, important_files["settings"])
manual_file_path = os.path.join(mainDir, important_files["manual"])


def add_cmd_to_shell():
    shell = sp.check_output("echo $SHELL", shell=True).decode().replace('\n', '').split('/')[-1]
    user = sp.check_output("echo $USER", shell=True).decode().replace('\n', '')
    py3 = sp.check_output("which python3", shell=True).decode().replace('\n', '')

    shellrc_file = os.path.join('/', 'home', user, f".{shell}rc")
    shell_aliases_file = os.path.join('/', 'home', user, f".{shell}_aliases")

    cmd = f"{py3} {os.path.join(mainDir, 'main.py')}"
    aliase_cmd = f"alias {get_app_settings()['name']}=\'{cmd}\'"

    add_to = shellrc_file

    if os.path.exists(shell_aliases_file):
        add_to = shell_aliases_file

    with open(add_to, 'r') as f:
        aliases = f.readlines()

    if (aliase_cmd not in aliases) and (aliase_cmd+'\n' not in aliases):
        aliases.append(aliase_cmd)

    with open(add_to, 'w') as f:
        f.writelines(aliases)


def get_norms():
    with open(norms_file_path) as f:
        norms = dict(json.load(f))

    return norms


def get_app_settings():
    with open(settings_file_path) as f:
        return dict(json.load(f))["App-Settings"]


def get_pkgs():
    try:
        pkgs = sys.argv[1::]

    except IndexError:
        pkgs = [""]

    return pkgs


def update_norms(exclude: list):
    if exclude != []:
        with open(norms_file_path, 'r') as f:
            dat = json.load(f)

        if dat["exclude"] == []:
            dat["exclude"] = exclude

        else:
            for e in exclude:
                if e not in dat["exclude"]:
                    dat["exclude"].append(e)

        with open(norms_file_path, 'w') as f:
            json.dump(dat, f, indent=4)


def show_man():
    p = ''
    with open(manual_file_path) as f:
        x = f.readlines()
        for i in x:
            p += i

    print(p)
    exit()


def check_if_installed(pkg_name: str) -> bool:
    installed_pkgs = [i.split(' ')[0] for i in sp.check_output("/usr/bin/pacman -Q", shell=True).decode().split('\n') if i != '']
    return pkg_name in installed_pkgs


def main():
    args = get_pkgs()
    norms = get_norms()
    app_settinngs = get_app_settings()
    exclude_pkgs = []
    pkgs = []

    app_name = app_settinngs["name"]
    sudoer: bool = norms["sudoer"]
    pkgman = os.path.join('/', 'usr', 'bin', norms["package-maneger"])
    installarg = norms["install-argument"]
    removearg = norms["remove-argument"]
    updatearg = norms["update-argument"]
    unreqpkgsarg = norms["unrequird-package-argument"]

    adder        = ""
    run_command  = ""
    run_command1 = ""
    run_command2 = ""

    if sudoer:
        pkgman = 'sudo ' + pkgman

    if ("-h" in args) or ("--help" in args) or (args == []):
        show_man()

    elif ("-v" in args) or ("--version" in args):
        print(f"{app_name}: Version: \033[1m{app_settinngs['version']}\033[0m")
        exit()

    elif ("-u" in args) or ("--update" in args):
        try:
            sp.check_output(f"{pkgman} {unreqpkgsarg}", shell=True)
            run_command1 = f"{pkgman} {removearg} $({pkgman} {unreqpkgsarg})"
    
        except sp.CalledProcessError:
            run_command1 = ''

        run_command2 = f"{pkgman} {updatearg}"

        if (run_command1 != "") and (run_command2 != ""):
            adder = " && "

        run_command = f"{run_command1}{adder}{run_command2}"

    elif ("-rm" in args) or ("--remove" in args):
        run_command = f"{pkgman} {removearg}"
        runx = run_command

        if '--remove' in args:
            args[args.index('--remove')] = '-rm'

        try:
            args[args.index('-rm')+1]

        except IndexError:
            print_message("worning", "Nothing to remove")

        del args[args.index('-rm')]

        if '-r' in args:
            i = args.index('-r')
            if os.path.exists(args[i+1]):
                with open(args[i+1]) as f:
                    pkgs = [i.replace('\n', '') for i in f.readlines()]

            else:
                print_message("error", f"\'\033[1m{args[i+1]}\033[0m\': No such file or directory", 2)

        else:
            pkgs = args

        for pkg in pkgs:
            if check_if_installed(pkg):
                run_command += f' {pkg}'

            else:
                print_message("error", f"\'{pkg}\' is not installed.", 3, kill=False)
                print_message("worning", "Ignoring...", kill=False)

        if run_command == runx:
            print("There is nothing to do.")
            exit()

    else:
        if "-py" in args:
            pkgs = ["python-"+i for i in args if i != "-py"]

        elif '-e' in args:
            i = args.index('-e')
            try:
                if os.path.exists(args[i+1]):
                    with open(args[i+1]) as f:
                        pkgs = [i.replace('\n', '') for i in f.readlines()]
                        exclude_pkgs = pkgs

                else:
                    print_message("error", f"\'\033[1m{args[i+1]}\033[0m\': No such file or directory", 2)

            except IndexError:
                print_message("worning", "Enter a file name")

        elif '-r' in args:
            i = args.index('-r')
            try:
                if os.path.exists(args[i+1]):
                    with open(args[i+1]) as f:
                        pkgs = [i.replace('\n', '') for i in f.readlines()]

                else:
                    print_message("error", f"\'\033[1m{args[i+1]}\033[0m\': No such file or directory", 2)

            except IndexError:
                print_message("worning", "Enter a file name")

        else:
            pkgs = args

        instcmd = f"{pkgman} {installarg}"

        for pkg in pkgs:
            instcmd += f" {pkg}"

        run_command = instcmd

    add_cmd_to_shell()

    if execute:
        print(f"Running command: \'\033[1m{run_command.replace('/usr/bin/', '')}\033[0m\'")
        os.system(run_command)

    update_norms(exclude_pkgs)
    pkg_list_maker()


if __name__ == "__main__":
    main()
