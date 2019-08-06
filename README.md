 # Marathon Deploy Utility
 A file based utility to deploy to various Marathon environments.  It uses Python/Jinja templating to create JSON payloads to send to Marathon.

Compatibility with Marathon 1.4 and below.  Json structure change required for 1.5 and above

### File Structure
> marathon-deploy.py - Deploy script  
> Dockfile - Docker build file  
> cert.crt - Cert for https requests
> Dockerfile - Docker build file
> _env - environment variables per env per app  
> _templates - application templates  
> utilities - custom packages

### Marathon controls
**General Usage:**
```sh
./marathon-deploy.py {action: -d -w -t -S -C} {env: -e} {selector: -g -a}
```
**Deploy and change Docker image version.  Not specificy the image version will use the image version in the env json.**
```sh
./marathon-deploy.py -d 3.2.0 -e dev -g monitoring
```
**Deploy list of apps:**
```sh
./marathon-deploy.py -d -e dev -a loadbalancer zk-web
```
**Deploy group of apps (monitoring, admin):**
```sh
./marathon-deploy.py -d -e dev -g admin
```
**Scale Marathon:**
```sh
./marathon-deploy.py -S 0 -e dev -g admin
```
**List tasks that are running/healthy/unhealthy/staged:**
```sh
./marathon-deploy.py -t -e dev -g admin
```