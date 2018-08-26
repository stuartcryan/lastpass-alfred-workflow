from __future__ import print_function
from workflow import Workflow
from workflow.util import set_config
from subprocess import Popen, PIPE
import os
import keychain
import shlex

log = None
wf = Workflow()
result = {}  # type: dict
result["items"] = []
my_env = os.environ.copy()
my_env["PATH"] = "/usr/local/bin:/opt/local/bin:" + my_env["PATH"]

def build_osascript(login_mail, title):
    log.debug('unlock: START for {user} and title: {title}'.format(user=login_mail, title=title))
    args = [login_mail, title, 'hidden']
    password = None
    script = """on run argv
    set AppleScript's text item delimiters to " "
    set my_password to display dialog item 2 of argv as string & ":" with title "Bitwarden " & item 1 of argv as string with icon caution default answer "" buttons {"Cancel", "OK"} default button 2 giving up after 295 with hidden answer
    if the button returned of the result is "Cancel" then
        error number -128
    else
    return (text returned of my_password)
    end if
    end run
    """
    log.debug('unlock: START osascript to ask for the password.')
    proc = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    password, err = proc.communicate(script)
    log.debug('unlock: Evaluate returned result status from the password entry.')
    if "-128" in err:
        log.debug('unlock: osascript - User cancelled unlocking')
        return None, True, 'User cancelled unlocking', None
    elif err:
        log.debug('unlock: osascript - An error occured: {err}'.format(err=err))
        return None, True, 'An error occured, entering password', err
    elif len(password.strip()) < 1:
        log.debug('unlock: osascript - No password was entered - leading and trailing spaces are stripped')
        return None, True, 'No password was entered', 'Leading and trailing spaces are stripped'
    return password, err, None, None


def login(login_mail):
    log.debug('unlock: - bw Start running bw unlock')
    password, err, status, message = build_osascript(login_mail, 'Enter Bitwarden password to unlock')
    if err:
        return out, err, status, message

    cmd = "/usr/local/bin/bw --raw unlock \"{password}\"".format(password=password.strip())
    split_cmd = shlex.split(cmd)
    proc = Popen(split_cmd, env=my_env, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    print('error output: {err}'.format(err=err))
    password, cmd = None, None
    log.debug('unlock: bw Evaluating bw login result')
    if err:
        log.debug('unlock: bw An error occured: {err}'.format(err=err))
        return out, err, 'An error occured while logging in', err
    if 'incorrect' in out:
        log.debug('unlock: bw incorrect credentials {out}'.format(out=out))
        return out, None, 'Incorrect credentials', out
    if 'Invalid' in out:
        log.debug('unlock: bw Invalid master password {out}'.format(out=out))
        return out, None, 'Invalid master password', out
    if 'You are already logged' in out:
        log.debug('unlock: bw you are already logged in {out}'.format(out=out))
        return out, None, 'You are already logged in', out
    if 'You are not logged in' in out:
        log.debug('unlock: bw you are not logged in {out}'.format(out=out))
        return out, None, 'You are not logged in', out
    log.debug('unlock: bw Return unlock result')
    return out, None, None, None

def set_notification(status, message):
        set_config('STATUS_MESSAGE', status)
        set_config('STATUS_MESSAGE_DESC', message)

def get_bw_exec():
    log.debug('START get_bw_exec')
    bw_exec = ""
    for f in ['/usr/local/bin/bw', '/opt/local/bin/bw', '/usr/bin/bw']:
        if os.path.exists(f):
            bw_exec = f
    if not bw_exec:
        log.debug('ERROR get_bw_exec: no bw binary found.')
        set_notification('Bitwarden CLI not found.', 'Please install the Bitwarden CLI first.')
        exit(2)
    log.debug('END found get_bw_exec')
    return bw_exec

def set_login():
    proc = Popen("launchctl setenv BW_ASKPASS true".split(), stdout=PIPE)
    output = proc.stdout.read().decode()
    if output:
        set_notification("Failed to set login env key", output)
        exit(1)
    return

def main(wf):
    log.debug('MAIN: Started')
    out = keychain.getpassword('alfred-bitwarden-email-address')
    if not out:
        log.debug('MAIN: No login mail configuration found.')
        set_notification('Error Login Config', 'No login email is configured.')
        exit(1)
    else:
        login_mail = out.strip()

    bw_exec = get_bw_exec()

    log.debug('MAIN: Start unlock')
    output, err, status, message  = login(login_mail)
    log.debug('MAIN: unlock result: {output} (trimmed)'.format(output=output[:15]))

    if err:
        log.debug('MAIN: Error occured: {err}'.format(err=err))
        set_notification(status, message)
        exit(1)
    if status or message:
        set_notification(status, message)
    else:
        output = keychain.setpassword('alfred-bitwarden-session-key', output.strip())
        if output:
            log.debug('MAIN: Error setting session key occured: {output}'.format(output=output))
            set_notification('Error setting session-key.', output)
            exit(1)
        else:
            set_login()
            set_notification('Unlock successful.', 'User: {user}'.format(user=login_mail))

if __name__ == '__main__':
    wf = Workflow()
    log = wf.logger
    wf.run(main)
