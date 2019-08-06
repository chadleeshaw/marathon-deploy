#!/usr/bin/python

from utilities.marathonUtils import *
import argparse
import sys
import os
import logging

logging.basicConfig()


def parse_args(args):
    env = ['dev','stage','prod'
    group = ['admin', 'monitoring']

    parser = argparse.ArgumentParser(description='Marathon Deployment Utility')
    parser.add_argument('-e', '--env', nargs='+', choices=env, required=True,
                        help="Space seperated list of environment(s)")
    parser.add_argument('--committer', nargs=1, default=None, help="Add commiter name for update image")
    group1 = parser.add_mutually_exclusive_group(required=True)
    group1.add_argument('-d', '--deploy', nargs='?', const='noargs',
                        help='Deploy app/group(s), optional argument image version')
    group1.add_argument('-t', '--tasks', nargs='?', const='noargs', help='Get application/group(s) tasks state')
    group1.add_argument('-C', '--CLEAR', action='store_true', help="Destroy app/group(s)")
    group1.add_argument('-S', '--SCALE', nargs=1, help="Scale app/group(s)")
    group1.add_argument('-R', '--RESTART', action='store_true', help="Restart app/group(s)")
    group1.add_argument('-P', '--PINCH', action='store_true', help="Pinch app/group(s)")
    group2 = parser.add_mutually_exclusive_group(required=True)
    group2.add_argument('-g', '--group', nargs='+', choices=group, help="Space seperated list of groups",
                        metavar='{groups}')
    group2.add_argument('-a', '--apps', nargs='+', help="Space seperated list of apps", metavar='{apps}')
    try:
        args = parser.parse_args()
        return args
    except:
        # parser.print_help()
        sys.exit(0)


def main(args):
    args = parse_args(args)
    ############ Deploy/Update ############
    if args.deploy:
        for env in args.env:
            envList, templateList = get_deploy_lists(env, args)
            if envList and templateList:
                if not 'noargs' in args.deploy:
                    update_image(env, envList, args.deploy, args.committer)
                render_json(env, envList, templateList)
                deploy_apps(env)
            else:
                print "Application not found"
    ############ Destroy Apps ############
    elif args.CLEAR == True:
        for env in args.env:
            if args.apps:
                clear_marathon(env, 'app', args.apps)
            if args.group:
                clear_marathon(env, 'group', args.group)
    ############ Scale Apps ############
    elif args.SCALE:
        for env in args.env:
            appIds = get_appids(env, args)
            scale_apps(env, appIds, args.SCALE)
    ############ Restart Apps ############
    elif args.RESTART:
        for env in args.env:
            appIds = get_appids(env, args)
            restart_apps(env, appIds)
    ############ Pinch Apps ############
    elif args.PINCH:
        for env in args.env:
            appIds = get_appids(env, args)
            scale_apps(env, appIds, ['0'], True)
            envList, templateList = get_deploy_lists(env, args) 
            if envList and templateList:
                render_json(env, envList, templateList)
                deploy_apps(env)
            else:
                print "Application not found"
    ############ Status of tasks ############
    elif args.tasks:
        for env in args.env:
            print_tasks(env, args)


if __name__ == '__main__':
    main(sys.argv[1:])
