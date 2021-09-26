import binascii
import hashlib
import rsa
import struct, os
import xml.etree.ElementTree as ET

from modules.Exceptions import AuthServiceException, MissingParameterException
from modules.ResponseCode import ResponseCodes
class LoginProfileHandler():
    def __init__(self, APIClient, CryptoWriter):
        self.APIClient = APIClient
        self.CryptoWriter = CryptoWriter
    def Handle(self, root_tree):
        resp_xml = ET.Element('{http://schemas.xmlsoap.org/soap/envelope/}Envelope')
        body = ET.SubElement(resp_xml, '{http://schemas.xmlsoap.org/soap/envelope/}Body')
        login_result = ET.SubElement(body, '{http://gamespy.net/AuthService/}LoginProfileResult')
        
        response_code = ResponseCodes.LOGIN_RESPONSE_SUCCESS
        
        response_code_node = ET.SubElement(login_result, '{http://gamespy.net/AuthService/}responseCode') #order is important... must be after peer key and before sig
        
        try:
            request_root = root_tree.find('.//{http://gamespy.net/AuthService/}LoginProfile')
            if request_root == None:
                raise MissingParameterException()

            #get request info
            nick_node = request_root.find('{http://gamespy.net/AuthService/}profilenick')
            nick = nick_node.text

            email_node = request_root.find('{http://gamespy.net/AuthService/}email')
            email = email_node.text

            partnercode_node = request_root.find('{http://gamespy.net/AuthService/}partnercode')
            partnercode = partnercode_node.text

            namespaceid_node = request_root.find('{http://gamespy.net/AuthService/}namespaceid')
            namespaceid = namespaceid_node.text

            #decrypt pw
            encrypted_pass = request_root.find('{http://gamespy.net/AuthService/}password').find('{http://gamespy.net/AuthService/}Value')

            password = self.CryptoWriter.DecryptPassword(encrypted_pass.text)

            results = self.APIClient.NickLogin(nick, email, namespaceid, partnercode, password)

            self.CryptoWriter.WritePeerkeyPrivate(login_result)
            self.CryptoWriter.WriteSignature(login_result, results)

        except AuthServiceException as e:
            response_code = e.response_code
        except:
            response_code = ResponseCodes.LOGIN_RESPONSE_SERVER_ERROR
        finally:
            response_code_node.text = str(response_code)
        
        return ET.tostring(resp_xml, encoding='utf8', method='xml')