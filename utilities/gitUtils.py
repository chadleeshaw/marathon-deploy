import time
import subprocess

def gitConfig(repoDir):
    cmd = ('if [[ -z $(git config --get user.name) ]]; then '
        'git config --global user.name "Marathon Deploy" && '
        'git config --global user.email "marathon@deploy.com" && '
        'git config --global push.default simple;fi')
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir,stdout = subprocess.PIPE,stderr = subprocess.PIPE )
    (out, error) = pipe.communicate()
    pipe.wait()
    return True if not error else False

def gitStatus(repoDir):
    cmd = 'git status -z'
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir,stdout = subprocess.PIPE,stderr = subprocess.PIPE )
    (out, error) = pipe.communicate()
    pipe.wait()
    return True if out else False

def gitAdd(fileName, repoDir):
    cmd = 'git add ' + fileName
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir,stdout = subprocess.PIPE,stderr = subprocess.PIPE )
    (out, error) = pipe.communicate()
    pipe.wait()
    return True if not error else False

def gitCommit(commitMessage, repoDir):
    cmd = 'git commit -m "{}"'.format(commitMessage)
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir,stdout = subprocess.PIPE,stderr = subprocess.PIPE )
    (out, error) = pipe.communicate()
    pipe.wait()
    return True if not error else False

def gitPush(branch,repoDir):
    cmd = 'git push origin HEAD:{}'.format(branch)
    pipe = subprocess.Popen(cmd, shell=True, cwd=repoDir,stdout = subprocess.PIPE,stderr = subprocess.PIPE )
    (out, error) = pipe.communicate()
    pipe.wait()
    return True if not error else False

if __name__ == '__main__':
    pass
