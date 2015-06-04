#!/usr/bin/env python

import argparse
import yaml
import sys
from lib import blossom


def readInitfile(initfileName):
    '''Load a YAML initfile by name, returning the dictionary of its contents

    '''
    config = None
    with open(initfileName, 'r') as f:
        config = yaml.load(f)
 
    return config
 



def main(argv):
   parser = argparse.ArgumentParser(description='Trello API wrapper')
   
   parser.add_argument('--debug', action='store_true', required=False, help='show (but do not send) API request')
   parser.add_argument('initfile')
   args = parser.parse_args()

   if len(sys.argv) < 2:
      print 'Usage: %s <initfile>' % (sys.argv[0])
      exit(1)

   initfileName = args.initfile
   yamlConfig = readInitfile(initfileName)

   apimgr = blossom.APIManager(yamlConfig)


   print apimgr.apiCalls
   print apimgr.handlers

   print apimgr.callAPIFunctionByName('trello', 'blocpower_boards', user_id='foo')




if __name__== '__main__':
   main(sys.argv[1:])
