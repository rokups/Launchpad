High level overview
===================

Launchpad consists of two main components: dashboard and client. When client connects to the dashboard it receives 
executable generated on the fly. Dashboard reads pre-generated zip file with python interpreter and dependencies,
appends client code to that zip, inserts zip into bootloader executable and sends resulting executable to client to
execute. Upon execution client connects to dashboard on the new connection and can be interacted with. 

Connections are asynchronous. On one end we have `LaunchpadClient` instance and on the other end there is 
`LaunchpadServer` instance. These objects can call each-other's methods through json-rpc. Please see
`dashboard.server_session.ServerSession.import_module` method. It is declared as usual and can be called by client
transparently as in `client.importer.load_module` method. Communication happens behind the scenes asynchronously.

# Project structure

* `bin`: Directory containing binary files required by Launchpad. For example bootloader executables, zips with 
interpreter, etc.
* `dep`: Directory contains external dependencies.
* `doc`: A place to store all documentation.
* `src/boot`: Native bootloader code. Bootloader is executable that bootstraps zipped python application.
* `src/client`: A client application. Code in this module will be appended to zip file with python standard library and 
sent to target machine for execution.
* `src/common`: Modules that are shared between client and dashboard. This module is also appended to application zip 
file which is sent to client.
* `src/dashboard`: A Django dashboard application.
* `src/launchpad`: A Django project.
* `src/tool`: A directory with utility scripts.
