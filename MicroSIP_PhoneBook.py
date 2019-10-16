#!/usr/bin/env python3
# Basic phonebook MicroSIP in an Avaya IP Office environment.


import cgi 
import cgitb
cgitb.enable()

# SETTING: IP address or DNS name of the Avaya IP Office server
#AVAYA_IP='AvayaPBX.sip.ACME.co'
AVAYA_IP='10.0.0.1'

#===================================================
# CLASSES
#===================================================


class Avaya(object):
  def __init__ (self, httpserver):
    self.serveraddress = httpserver
  def getaddressbook (self):
    import urllib.request
    import xml.etree.ElementTree as ET
    tree = ET.parse (urllib.request.urlopen ('http://' + self.serveraddress + '/system/user/scn_user_list'))
    root = tree.getroot()

    userlist = None
    for element in root:
      #print(element.tag)
      if element.tag == '{http://www.avaya.com/ipoffice/userlist}list':
        userlist = element
    #print (len(userlist))

    phonebook = []
    for user in userlist:
      phonebookitem = {'name':None, 'extension':None}
      for tags in user:
        #print (tags.tag, tags.text)
        if tags.tag == '{http://www.avaya.com/ipoffice/userlist}fname': 
          phonebookitem['name'] = tags.text
        if tags.tag == '{http://www.avaya.com/ipoffice/userlist}extn':
          phonebookitem['extension'] = tags.text
      #print (phonebookitem)
      if not ((phonebookitem['name'] is None) or (phonebookitem['extension'] is None)):
        phonebook.append(phonebookitem)

    ### Removed sort by name as it seemss to break 
    #sort_on = "name"
    #decorated = [(dict_[sort_on], dict_) for dict_ in phonebook]
    #decorated.sort()
    #result = [dict_ for (key, dict_) in decorated]
    #return result

    return phonebook

class MicroSIPphonebook:
  MAX_PER_PAGE=20
  __search_criterea = ''
  __count=0

  def setSearchCriterea(self, xml_data_input):
    from lxml import etree, objectify
    if (not (xml_data_input == None)):
      if (len(xml_data_input) > 10):
        try:
          parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
          xml = etree.fromstring(xml_data_input, parser=parser)
        except Exception as e:
          print("Error in XML")
          print(xml_data_input)
          print()
          print(e)
          return
      else:
        print('Expected XML data too short (<10)')
        return
    else:
      print('XML data expected. None received')
      return
    root = xml.getroottree()
    try:
      self.__search_criterea = root.find('body').find('params').find('condition').text.strip()
      #print(self.__search_criterea)
    except Exception as e:
      print(e)
    #print (head.condition)

  def __makebean(self,phonebookitem):
    from lxml import etree
    bean = etree.Element('entry')
    name = etree.Element('name')
    name.text = phonebookitem['name'] + ' : ' +  phonebookitem['extension']
    extension = etree.Element('extension')
    extension.text = phonebookitem['extension']
    presence = etree.Element('presense')
    presence.text = '1'
    bean.append(name)
    bean.append(extension)
    bean.append(presence)
    return bean


  def outputXML(self,phonebook):
    from lxml import etree
    root = etree.Element('directory')

    for phonebookitem in phonebook:
      self.__count = self.__count + 1
      root.append(self.__makebean(phonebookitem))

    return (etree.tostring(root).decode('utf-8'))

#===================================================
# MAIN
#===================================================

##Do the lookup and prepare data
avayasystem = Avaya(AVAYA_IP)
MicroSIP = MicroSIPphonebook()
phonebook = avayasystem.getaddressbook()

output = MicroSIP.outputXML(phonebook)

## Final stage. Start writing out HTTP response
print ("Content-Type: text/xml;charset=utf-8")
print ()
print ('<?xml version="1.0" encoding="UTF-8" standalone="no" ?>')
print(output)
