from utilities.gitUtils import *
from prettytable import PrettyTable
import os
import re
import json
import requests
import collections
import base64
import jinja2
import shutil
import time


def list_json(directory):
    '''list files with json extension'''
    filePaths = []
    for root, directories, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".json"):
                filepath = os.path.join(root, filename)
                filePaths.append(filepath)
    return filePaths

def load_json(files):
    """Load all json files as a list of dictionaries"""
    config = []
    for file in files:
        with open(file, 'r') as data_file:
            config.append(collections.OrderedDict(json.load(data_file)))
    return config


def render_json(deployEnv, envFiles, templateFiles):
    '''Match template id with env filename, render, write _json files '''
    clear_json()
    envJson = load_json(envFiles)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="."), trim_blocks=True, lstrip_blocks=True)
    for templateFile in templateFiles:
        outputPath = templateFile.replace("_templates", "_json/{}".format(deployEnv))
        if not os.path.exists(os.path.dirname(outputPath)):
            os.makedirs(os.path.dirname(outputPath))
        appName = os.path.splitext(os.path.basename(outputPath))[0]
        templateEnv = list(filter(lambda key_search: key_search['id'] == appName, envJson))[0]
        template = env.get_template(templateFile)
        with open(outputPath, 'w') as f:
            f.write(template.render(template=templateEnv))


def marathon_request(env, method, uri, data=None):
    '''Build request to Marathon'''
    config = load_json(['./_env/{}/marathon.conf'.format(env)])
    password = base64.b64decode(json.dumps(config[0].get('password'))).decode().rstrip('\n')
    auth = ('admin', password)
    headers = {'Content-type': 'application/json'}
    baseUrl = json.dumps(config[0].get('marathon')).strip('"')
    url = "{}{}".format(baseUrl, uri)
    req = requests.request(method, url, headers=headers, auth=auth, data=data, timeout=40, verify='./cert.crt')
    req.raise_for_status()
    return req

def get_appids(env, args):
    appIds = []
    if args.apps:
        apps = marathon_request(env, 'get', '/v2/apps').json()['apps']
        for app in args.apps:
            search = "/{}".format(app)
            appIds = [x['id'] for x in apps if search in x['id']]
    elif args.group:
        for group in args.group:
            apps = marathon_request(env, 'get', '/v2/groups/{}'.format(group)).json()['apps']
            appIds = [app['id'] for app in apps]
    return appIds

def get_deploy_lists(env, args):
    envList = []
    templateList = []
    if args.group:
        for group in args.group:
            envList.append(list_json('./_env/{}/{}'.format(env, group)))
            templateList.append(list_json('./_templates/{}'.format(group)))
        envList = sum(envList, [])
        templateList = sum(templateList, [])
    elif args.apps:
        envFiles = list_json('./_env/{}'.format(env))
        templateFiles = list_json('./_templates/')
        for app in args.apps:
            search = "/{}.json".format(app)
            [envList.append(envFile) for envFile in envFiles if search in envFile]
            [templateList.append(templateFile) for templateFile in templateFiles if search in templateFile]
    return envList, templateList

def deploy_apps(env, sync=False):
    '''Deploy to Marathon'''
    deployFiles = sorted(list_json('./_json/{}'.format(env)))
    deployConfig = load_json(deployFiles)
    for config in deployConfig:
        finalJson = json.dumps(config)
        r = marathon_request(env, 'put', '/v2/apps{}?force=true'.format(config['id']), finalJson)
        if r.ok:
            if 'macvlan' in finalJson:
                r = marathon_request(env, 'put', '/v2/apps{}?force=true'.format(config['id']),
                                     '{"ipAddress": [], "ports": []}')
            if not sync:
                print("Deploying {} to {}".format(config['id'], env))
            else:
                if config.get('instances') >= 1:
                    deployId = get_deploy_id(r)
                    sync_deploy(env, deployId, config['id'])
                else:
                    print("Syncronous deploy has zero instances: {}".format(config['id']))
        else:
            print("Error deploying app {}\n{}".format(config['id'], r.text))


def instance_check(env, appId):
    apps = marathon_request(env, 'get', '/v2/apps').json()['apps']
    running = False
    for app in apps:
        if appId in app.get('id'):
            if apps[(apps.index(app))].get('instances') >= 1:
                running = True
    return running


def update_image(env, apps, version, committer=None):
    '''Change the version of the docker image'''
    appIds = []
    if type(apps) == str:
        for app in apps.split(','):
            appIds.append(app)
    if type(apps) == list:
        appIds = apps
    for app in appIds:
        envFiles = list_json('./_env/{}'.format(env))
        templateFiles = list_json('./_templates/{}'.format(env))
        try:
            ''' Change image in env file '''
            for envFile in envFiles:
                if app in envFile:
                    with open(envFile, 'r+') as f:
                        data = json.load(f)
                        image = data.get('image').strip('"')
                        try:
                            oldImage = image.split(':')
                            newImage = "{}:{}".format(oldImage[0], ''.join(version))
                        except:
                            newImage = "{}:{}".format(image, ''.join(version))
                        data['image'] = newImage
                        f.seek(0)
                        json.dump(data, f, indent=2)
                        f.truncate()
        except:
            print("Error updating, image field not in env file")
            quit()
    try:
        envList = []
        for app in apps:
            appName = os.path.splitext(os.path.basename(app))[0]
            envList.append(appName)
        if gitConfig('./'):
            if gitStatus('./'):
                if gitAdd('./', './'):
                    if gitCommit('{} update to {} \n{} {}'.format(''.join(env), ''.join(version), ','.join(envList),
                                                                  ''.join(committer)), './'):
                        if gitPush('master', './'):
                            print("Git commit worked!")
    except:
        print("Git commit failed :(")


def scale_apps(env, appIds, instances, sync=False):
    for app in appIds:
        r = marathon_request(env, 'put', '/v2/apps/{}?force=true'.format(app), '{"instances":%s}' % ''.join(instances))
        print('Scaling {} in {} to {}'.format(app, env, ''.join(instances)))
        if sync:
            deployId = get_deploy_id(r)
            sync_deploy(env, deployId, app)

def restart_apps(env, appIds):
    for app in appIds:
        r = marathon_request(env, 'post', '/v2/apps/{}/restart'.format(app))
        print('Restarting {} in {}'.format(app, env))

def clear_marathon(env, args, delList):
    '''Destroy app/group'''
    print(delList)
    danger = raw_input("Are you sure you want to do this in {}? (yes/no): ".format(env))
    if danger == 'yes' or 'y':
        if args == 'app':
            for delete in delList:
                search = "/{}".format(delete)
                apps = marathon_request(env, 'get', '/v2/apps').json()['apps']
                appId = [x['id'] for x in apps if search in x['id']]
                if appId:
                    req = marathon_request(env, 'delete', '/v2/apps/{}?force=true'.format(appId[0]))
                    if req.ok:
                        print("deleting app: {}".format(delete))
                    else:
                        print("error deleteing app {}\n{}".format(delete, req.text))
                else:
                    print("Can't destroy {} in {}: not found".format(delete, env))
        if args == 'group':
            for delete in delList:
                search = "/{}".format(delete)
                groups = marathon_request(env, 'get', '/v2/groups').json()['groups']
                groupId = [group['id'] for group in groups if search in group['id']]
                if groupId:
                    req = marathon_request(env, 'delete', '/v2/groups/{}?force=true'.format(str(groupId[0])))
                    if req.ok:
                        print("deleting group: {}".format(delete))
                    else:
                        print("error deleteing group: {}\n{}".format(delete, req.text))
                else:
                    print("Can't destroy {} in {}: not found".format(delete, env))


def clear_json():
    '''remove rendered json files in _json'''
    try:
        for filename in os.listdir('./_json/'):
            filepath = os.path.join('./_json/', filename)
            try:
                shutil.rmtree(filepath)
            except OSError:
                os.remove(filepath)
    except:
        pass


def sync_deploy(env, deployId, app):
    '''Check for deployment, if exists wait until it's done'''
    retries = 0
    maxRetries = 90
    deploys = marathon_request(env, 'get', '/v2/deployments').json()
    deployIds = [x['id'] for x in deploys]
    if deployId in deployIds:
        print('Waiting for {} in {}'.format(app, env))
        while deployId in deployIds and retries < maxRetries:
            deploys = marathon_request(env, 'get', '/v2/deployments').json()
            deployIds = [x['id'] for x in deploys]
            retries += 1
            time.sleep(1)
        if retries < maxRetries:
            print('Done with {} in {}'.format(app, env))
        else:
            print('Max retries met for {} : {}'.format(app, deployId))
    else:
        print('Deployment not found: {} : {}'.format(app, deployId))


def get_deploy_id(response):
    '''return deployment id'''
    try:
        rJson = response.json()
        deployId = rJson.get('deploymentId')
        return deployId
    except requests.exceptions.RequestException as e:
        print(e)

def print_tasks(env, args):
    apps = []
    if args.apps:
        req = marathon_request(env, 'get', '/v2/apps').json()['apps']
        for app in args.apps:
            search = "/{}".format(app)
            appIds = [x['id'] for x in req if search in x['id']]
            for appId in appIds:
                apps.append([x for x in req if appId in x['id']][0])
    elif args.group:
        for group in args.group:
            req = marathon_request(env, 'get', '/v2/groups/{}'.format(group)).json()['apps']
            appIds = [app['id'] for app in req]
            for appId in appIds:
                apps.append(marathon_request(env, 'get', '/v2/apps{}'.format(appId)).json()['app'])
    if 'noargs' in args.tasks:
        t = PrettyTable(['Env', 'App', 'Image', 'Status', 'I', 'R', 'H', 'U', 'S'])
        t.align = "r"
        for app in apps:
            if app['instances'] == 0:
                status = 'NotRunning'
            elif not app['deployments']:
                status = 'Running'
            else:
                status = 'Deploying'
            t.add_row([env, app['id'], app['container']['docker']['image'], status, app['instances'], app['tasksRunning'], app['tasksHealthy'], app['tasksUnhealthy'],
                    app['tasksStaged']])
        print(t)
    else:
        for app in apps:
            if not app['deployments']:
                status = 'Running'
            elif app['deployments']:
                status = 'Deploying'
            elif app['instances'] == 0:
                status = 'NotRunning'
            print({'env': env, 'app': app['id'], 'image': app['container']['docker']['image'], 'status': status, 'instances': app['instances'], 'tasksRunning': app['tasksRunning'],
                'tasksHealthy': app['tasksHealthy'], 'tasksUnhealthy': app['tasksUnhealthy'], 'tasksStaged': app['tasksStaged']})


if __name__ == '__main__':
    pass
