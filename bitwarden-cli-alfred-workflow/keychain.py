from subprocess import Popen, PIPE

def getpassword(service):
    cmd = '/usr/bin/security find-generic-password -w -s {service}'.format(service=service)
    proc = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    output, err = proc.communicate()
    if err:
      return None
    return output

def setpassword(service, password):
    cmd = '/usr/bin/security add-generic-password -C note -U -a {service_account} -s {service} -w {session_key}'.format(service_account=service, service=service, session_key=password)
    proc = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    output, err = proc.communicate()
    if err:
      return err
    return None

def deletepassword(service):
    cmd = '/usr/bin/security delete-generic-password -s {service}'.format(service=service)
    proc = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
    proc.communicate()
