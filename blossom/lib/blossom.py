import os
import sys
import imp
import json
import argparse
import yaml

from tags import *






def readEnvironmentVariable(varName):
      var = os.environ.get(varName)
      if not var:
         raise Exception('Missing environment variable %s specified in init file.' % varName)
      return var


class UnregisteredServiceException(Exception):
   def __init__(self, serviceName):
      Exception.__init__(self, 'No service registered under the alias "%s".' % serviceName)


class UnregisteredHandlerException(Exception):
   def __init__(self, handlerID, apiCallName):
      Exception.__init__(self, 'No handler function registered under the name "%s" for API call "%s".' % (handlerID, apiCallName))

class UnregisteredAPICallException(Exception):
   def __init__(self, apiCallName):
      Exception.__init__(self, 'No call registered under the name "%s".' % (apiCallName))
      

class Service():
   def __init__(self, baseURL, description):
      self.url = baseURL
      self.description = description
      
   
class APIParameter():
   def __init__(self, name, value):
      self.name = name
      value = str(value)
      if value.startswith('$'):
         self.value = readEnvironmentVariable(value[1:])
      else:
         self.value = value

   


class APICall():
   def __init__(self, urlPathString, parameterArray, handlerAlias):
      self.urlPath = urlPathString
      self.parameters = {}
      for p in parameterArray:
         self.parameters[p.name] = p
      self.handlerID = handlerAlias


   def addParameter(self, name, value):
      param = APIParameter(name, value)
      self.parameters[name] = param
      

   def generateQueryString(self):
      paramNames = self.parameters.keys()
      params = ['%s=%s' % (p, self.parameters[p].value) for p in paramNames]
      return '&'.join(params)


   def __repr__(self):
      return '%s?%s' % (self.urlPath, self.generateQueryString()) 


class APIManager():
   def __init__(self, yamlConfig):
      self.config = yamlConfig
      globalModulePath = self.config['global']['handler_module_path']      
      if globalModulePath.startswith('$'):
         globalModulePath = readEnvironmentVariable(globalModulePath[1:])
      sys.path.append(globalModulePath)
      self.callTable = self.loadAPICalls()
      self.callHandlers = self.loadHandlers()
      self.services = self.loadServices()


   def getServiceObject(self, serviceName):
      result = self.services.get(serviceName)
      if not result:
         raise UnregisteredServiceException(serviceName)
      return result
   

   def _createAPICallFromYAMLConfig(self, sectionName):

      configSection = self.config[CALL_SECTION_TAG][sectionName]
      path = configSection[CALL_URL_PATH_TAG]
      handlerAlias = configSection[CALL_HANDLER_TAG]
      
      params = []
      
      for param in configSection.get(CALL_PARAMETERS_TAG, []):
            params.append(APIParameter(param.get('name'), param.get('value')))
      
      if not handlerAlias:
         raise Exception('Invalid API call specified in init file under "%s".' % sectionName)

      if not path:
         path = ''
         
      return APICall(path, params, handlerAlias)
   


   def _loadHandlerFunction(self, moduleName, functionName):
      targetModule = __import__(moduleName)
      return getattr(targetModule, functionName)



   def loadAPICalls(self):
      apiCallTable = {}
      for callName in self.config[CALL_SECTION_TAG]:
         apiCall = self._createAPICallFromYAMLConfig(callName)
         apiCallTable[callName] = apiCall
      return apiCallTable



   def loadHandlers(self):
      handlerTable = {}      
      for handlerName in self.config[HANDLER_SECTION_TAG]:
         moduleName = self.config[HANDLER_SECTION_TAG][handlerName][HANDLER_MODULE_TAG]
         functionName = self.config[HANDLER_SECTION_TAG][handlerName][HANDLER_FUNCTION_TAG]
         
         handlerFunction = self._loadHandlerFunction(moduleName, functionName)
         handlerTable[handlerName] = handlerFunction   
      return handlerTable


   def loadServices(self):
      serviceTable = {}
      for serviceName in self.config[SERVICE_SECTION_TAG]:
         baseURL = self.config[SERVICE_SECTION_TAG][serviceName].get(SERVICE_BASE_URL_TAG, None)
         handlerModulePath = self.config[SERVICE_SECTION_TAG][serviceName].get(HANDLER_MODULE_PATH_TAG, None)
         description = self.config[SERVICE_SECTION_TAG][serviceName].get(DESCRIPTION_TAG, '')

         if not baseURL:
            raise Exception('base URL not specified for the service %s.' % serviceName)

         if handlerModulePath:
            sys.path.append(handlerModulePath)
            
         serviceTable[serviceName] = Service(baseURL, description)
      return serviceTable


   def getAPICallObject(self, name):
      callObject = self.callTable.get(name)
      if not callObject:
         raise UnregisteredAPICallException(name)
      return callObject


   def generateURL(self, serviceName, apiCallObject, **kwargs):
      for name in kwargs.keys():
         value = kwargs[name]
         apiCallObject.addParameter(name, value)
      targetService = self.services.get(serviceName)
      
      if not targetService:
         raise UnregisteredServiceException(serviceName)
      
      return '/'.join([targetService.url, str(apiCallObject)])



   def callAPIFunctionByName(self, serviceName, apiCallName, **kwargs):
      apiCall = self.getAPICallObject(apiCallName)
      fullUrl = self.generateURL(serviceName, apiCall, **kwargs)
      service = self.getServiceObject(serviceName)
      
      handlerFunction = self.callHandlers.get(apiCall.handlerID)
      if not handlerFunction:
         raise UnregisteredHandlerException(apiCall.handlerID, apiCallName)

      handlerFunction(**kwargs)
      return fullUrl
      


   def callAPIFunction(self, serviceName, apiCallObject):
      pass
   
   
   @property
   def apiCalls(self):
      return self.callTable.keys()


   @property
   def handlers(self):
      return self.callHandlers.keys()

 

