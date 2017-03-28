#!/usr/bin/env python

import json, urlparse, sys, os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from subprocess import call

class GitAutoDeploy(BaseHTTPRequestHandler):

    CONFIG_FILEPATH = './gitLabHook.conf'
    config = None
    quiet = False
    daemon = False

    @classmethod
    def getConfig(myClass):
        if(myClass.config == None):
            try:
                configString = open(myClass.CONFIG_FILEPATH).read()
            except:
                sys.exit('Could not load ' + myClass.CONFIG_FILEPATH + ' file')

            try:
                myClass.config = json.loads(configString)
            except:
                sys.exit(myClass.CONFIG_FILEPATH + ' file is not valid json')

        return myClass.config

    def do_POST(self):
        event = self.headers.getheader('X-Gitlab-Event')
        content_len = int(self.headers.getheader('content-length', 0))
        post_body = self.rfile.read(content_len)
        print('{}\n{}\n\n{}'.format(
            '-----------START-----------',
            '\n'.join('{}: {}'.format(k, v) for k, v in self.headers.items()),
            post_body,
        ))        
        if event == 'ping':
            if not self.quiet:
                print 'Ping event received'
            self.respond(204)
            return
        if event != 'Build Hook':
            if not self.quiet:
                print 'We only handle ping and build events, but [' + event + '] here'
            self.respond(304)
            return

        self.respond(204)
        if "\"status\":\"success\"" in post_body:
            print('Start deploy...')
            self.deploy()

    def respond(self, code):
        self.send_response(code)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()

    def deploy(self):
        os.system('./start.sh')

def main():
    try:
        server = None
        for arg in sys.argv: 
            if(arg == '-d' or arg == '--daemon-mode'):
                GitAutoDeploy.daemon = True
                GitAutoDeploy.quiet = True
            if(arg == '-q' or arg == '--quiet'):
                GitAutoDeploy.quiet = True
                
        if(GitAutoDeploy.daemon):
            pid = os.fork()
            if(pid != 0):
                sys.exit()
            os.setsid()

        if(not GitAutoDeploy.quiet):
            print 'Github Autodeploy Service v0.2 started'
        else:
            print 'Github Autodeploy Service v 0.2 started in daemon mode'
             
        server = HTTPServer(('', GitAutoDeploy.getConfig()['port']), GitAutoDeploy)
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit) as e:
        if(e):
            print >> sys.stderr, e

        if(not server is None):
            server.socket.close()

        if(not GitAutoDeploy.quiet):
            print 'Goodbye'

if __name__ == '__main__':
     main()
