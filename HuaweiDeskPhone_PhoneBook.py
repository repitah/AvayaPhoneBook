#!/usr/bin/env python3
# Basic phonebook and number lookup for Huawei eSpace 79x0 phones and probbaly more.
# Basic emulator for UC (2.0) phonebook requests -- because integration in heterogenious environments is a challenge :)
# Normal UC path: http://<server>/appServer/appserver/searchEmployeeForIpPhone.action -- this can be changed on the phone.

import cgi 
#import cgitb
#cgitb.enable()

import sys

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

class HuaweiPhoneUC:
  MAX_PER_PAGE=20
  __search_criterea = ''
  __search_exact='0'
  __count=0

  def setArgSearchCritera(self, exact, searchval):
    self.__search_criterea = searchval
    self.__search_exact = exact


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
    try:
      self.__search_exact = root.find('body').find('params').find('exactsearch').text.strip()
      #print(self.__search_criterea)
    except Exception as e:
      print(e)
    #print (head.condition)

  def __makebean(self,phonebookitem):
    from lxml import etree
    bean = etree.Element('bean')
    name = etree.Element('name')
    name.text = phonebookitem['name']
    extension = etree.Element('officephone')
    extension.text = phonebookitem['extension']
    bean.append(name)
    bean.append(extension)
    return bean


  def outputXML(self,phonebook):
    from lxml import etree
    root = etree.Element('message')

    head = etree.Element('head')
    retcode = etree.Element('retcode')
    retcode.text = '0'
    retcontext = etree.Element('retcontext')
    retcontext.text = 'Phonebook@mustek.ltd'
    head.append(retcode)
    head.append(retcontext)
    root.append(head)

    body = etree.Element('body')

    params = etree.Element('params')
    paramlist = etree.Element('paramlist')

    self.__count=0

    tmpphonebook = list()
    if ((self.__search_criterea == '') or (self.__search_criterea == None)): ##if no criterea
      tmpphonebook = phonebook
    else:
      if (self.__search_exact == '1'):
        for phonebookitem in phonebook:
          if ( phonebookitem['extension'].lower() == self.__search_criterea.lower() ):
            tmpphonebook.append(phonebookitem)
      else:
        for phonebookitem in phonebook:
          if (phonebookitem['name'].lower().find(self.__search_criterea.lower()) >= 0) or (phonebookitem['extension'].lower().find(self.__search_criterea.lower()) >= 0 ):
            if ( phonebookitem['extension'].lower() == self.__search_criterea.lower() ):
              tmpphonebook.insert(0,phonebookitem)
            else:
              tmpphonebook.append(phonebookitem)

    for phonebookitem in tmpphonebook:
      self.__count = self.__count + 1
      paramlist.append(self.__makebean(phonebookitem))
      if self.__count > (self.MAX_PER_PAGE - 1):
        break

    total = etree.Element('total')
    sum = etree.Element('sum')
    total.text = str(self.__count)
    sum.text = '1'
    params.append(total)
    params.append(sum)
    body.append(params)

    body.append(paramlist)
    root.append(body)

    return (etree.tostring(root).decode('utf-8'))

#===================================================
# MAIN
#===================================================

form = cgi.FieldStorage()
incomingformdata = None
for key in form.keys():
  incomingformdata = (key + form.getvalue(key)).encode('utf-8')

##Do the lookup and prepare data
avayasystem = Avaya(AVAYA_IP)
huaweiphone = HuaweiPhoneUC()
phonebook = avayasystem.getaddressbook()

if len(form.keys()) > 0:
  huaweiphone.setSearchCriterea(incomingformdata)
if len(sys.argv) == 2:
  huaweiphone.setArgSearchCritera('0',sys.argv[1])
if len(sys.argv) == 3:
  huaweiphone.setArgSearchCritera(sys.argv[2],sys.argv[1])

output = huaweiphone.outputXML(phonebook)

## Final stage. Start writing out HTTP response
print ("Content-Type: text/xml;charset=utf-8")
print ()
print ('<?xml version="1.0" encoding="UTF-8" standalone="no" ?>')
print(output)
