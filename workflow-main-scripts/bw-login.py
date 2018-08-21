from __future__ import print_function
from workflow import Workflow
from workflow.util import set_config
from subprocess import Popen, PIPE
import os
import keychain

log = None
wf = Workflow()
result = {}  # type: dict
result["items"] = []
my_env = os.environ.copy()
my_env["PATH"] = "/usr/local/bin:/opt/local/bin:" + my_env["PATH"]

def build_osascript(login_mail, title, mfa_enabled=None, mfa_method=None):
    log.debug('login: START for {user} and title: {title}'.format(user=login_mail, title=title))
    if not mfa_enabled:
        args = [login_mail, title, 'hidden']
    else:
        args = [login_mail, title, '']
    password = None
    script = """on run argv
    set AppleScript's text item delimiters to " "
    if item 3 of argv as string contains "hidden" then
      set my_password to display dialog item 2 of argv as string & ":" with title "Bitwarden " & item 1 of argv as string with icon caution default answer "" buttons {"Cancel", "OK"} default button 2 giving up after 295 with hidden answer
else
    set my_password to display dialog item 2 of argv as string & ":" with title "Bitwarden " & item 1 of argv as string with icon caution default answer "" buttons {"Cancel", "OK"} default button 2 giving up after 295 with answer
end if
    if the button returned of the result is "Cancel" then
        error number -128
    else
    return (text returned of my_password)
    end if
    end run
    """
    log.debug('login: START osascript to ask for the password.')
    proc = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    password, err = proc.communicate(script)
    log.debug('login: Evaluate returned result status from the password entry.')
    if "-128" in err:
        log.debug('login: osascript - User cancelled login')
        return None, True, 'User cancelled login', None
    elif err:
        log.debug('login: osascript - An error occured: {err}'.format(err=err))
        return None, True, 'An error occured, entering password', err
    elif len(password.strip()) < 1:
        log.debug('login: osascript - No password was entered - leading and trailing spaces are stripped')
        return None, True, 'No password was entered', 'Leading and trailing spaces are stripped'
    return password, err, None, None


def login(login_mail, mfa_enabled=None, mfa_method=None):
    log.debug('login: - bw Start running bw login')
    password, err, status, message = build_osascript(login_mail, 'Enter Bitwarden password')
    if err:
        return out, err, status, message

    if not mfa_enabled:
        cmd = "/usr/local/bin/bw --raw login {login_mail} {password}".format(login_mail=login_mail, password=password)
    elif mfa_enabled and not mfa_method:
        mfa_code, err, status, message = build_osascript(login_mail, 'Enter Bitwarden second factor code', True)
        cmd = "/usr/local/bin/bw --raw login {login_mail} {password} --code {mfa_code}".format(login_mail=login_mail, password=password, mfa_code=mfa_code)
    else:
        mfa_code, err, status, message = build_osascript(login_mail, 'Enter Bitwarden second factor code', True)
        cmd = "/usr/local/bin/bw --raw login {login_mail} {password} --method {mfa_method} --code {mfa_code}".format(login_mail=login_mail, password=password, mfa_method=mfa_method, mfa_code=mfa_code)

    proc = Popen(cmd.split(), env=my_env, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()
    print('error output: {err}'.format(err=err))
    password, cmd = None, None
    log.debug('login: bw Evaluating bw login result')
    if err:
        if 'Two-step login' in err:
            log.debug('login: bw Two Step login in the account enabled but not in the workflow config: {err}'.format(err=err))
            return out, err, '2FA config not correct/missing.', err
        log.debug('login: bw An error occured: {err}'.format(err=err))
        return out, err, 'An error occured while logging in', err
    if 'incorrect' in out:
        log.debug('login: bw incorrect credentials {out}'.format(out=out))
        return out, None, 'Incorrect credentials', out
    if 'Invalid' in out:
        log.debug('login: bw Invalid master password {out}'.format(out=out))
        return out, None, 'Invalid master password', out
    if 'You are already logged' in out:
        log.debug('login: bw You are already logged in {out}'.format(out=out))
        return out, None, 'You are already logged in', out
    log.debug('login: bw Return login result')
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

    out = keychain.getpassword('alfred-bitwarden-2fa-method')
    if not out:
        login_mfa_method = False
        log.debug('MAIN: 2fa method not set')
    else:
        login_mfa_method = out.strip()

    out = keychain.getpassword('alfred-bitwarden-2fa-enabled')
    if not out:
        login_mfa_enabled = False
        log.debug('MAIN: 2fa not used')
    elif 'off' in out:
        login_mfa_enabled = False
        log.debug('MAIN: 2fa not used')
    else:
        login_mfa_enabled = True

    bw_exec = get_bw_exec()

    if not login_mfa_enabled:
        log.debug('MAIN: Start login without 2fa')
        output, err, status, message  = login(login_mail)
        log.debug('MAIN: login result: {output} (trimmed)'.format(output=output[:15]))
    elif login_mfa_enabled and not login_mfa_method:
        log.debug('MAIN: Start login with 2fa but without a method set')
        output, err, status, message  = login(login_mail, True)
        log.debug('MAIN: 2fa login result: {output} (trimmed)'.format(output=output[:15]))
    else:
        log.debug('MAIN: Start login with 2fa and method set to: {method}'.format(method=login_mfa_method))
        output, err, status, message  = login(login_mail, True, login_mfa_method)
        log.debug('MAIN: 2fa with method set login result: {output} (trimmed)'.format(output=output[:15]))

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
            set_notification('Login Successful.', 'User: {user}'.format(user=login_mail))

if __name__ == '__main__':
    wf = Workflow()
    log = wf.logger
    wf.run(main)
