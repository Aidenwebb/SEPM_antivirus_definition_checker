import json
import requests
import base64

def generate_auth(company_id, public_key, private_key):
    token = "{}+{}:{}".format(company_id, public_key, private_key)
    token = base64.b64encode(bytes(token, 'utf-8'))
    print(token)
    token = token.decode('utf-8')
    return token


class APIError(Exception):
    """An API Error Exception"""

    def __init__(self, status):
        self.status = status

    def __str__(self):
        return "APIError: status={}".format(self.status)

class CWAPIClient(object):

    def __init__(self, site, auth):
        self._default_headers = {"Authorization": "Basic %s" % auth,
                                 "Content-Type": "application/json"}
        self.site = site
        self.auth_token = auth
        self.api_url = "https://{site}/v4_6_release/apis/3.0".format(site=self.site)
        self.connection = requests.Session()
        self.connection.headers = self._default_headers

    def _url(self, path):
        return self.api_url + path

    def _add_condition(self, string, add_string, add_value):
        if string == '':
            if type(add_value) is not str:
                result = '{}={}'.format(add_string, add_value)
            else:
                result = '{}="{}"'.format(add_string, add_value)
            print('1st shot')
        else:
            if type(add_value) is not str:
                result = '{} and {}={}'.format(string, add_string, add_value)
            else:
                result = '{} and {}="{}"'.format(string, add_string, add_value)
            print('2nd shot?')
        print(result)
        return result

    def _get_contact_id(self, contact_name, company_identifier):
        first_name = contact_name.split(' ')[0]
        last_name = contact_name.split(' ')[1]
        contact = self.get_contacts(first_name=first_name, last_name=last_name, company_identifier=company_identifier).json()
        return contact[0]['id']


    def get_contacts(self, first_name=None, last_name=None, company_identifier=None, db_rid=None):
        conditionstring = ""
        if db_rid:
            conditionstring = self._add_condition(conditionstring, 'id', db_rid)
        if first_name:
            conditionstring = self._add_condition(conditionstring, 'firstName', first_name)
        if last_name:
            conditionstring = self._add_condition(conditionstring, 'lastName', last_name)
        if company_identifier:
            conditionstring = self._add_condition(conditionstring, 'company/identifier', company_identifier)
        parameters = {
            "conditions": conditionstring
            }

        return self.connection.get(self._url("/company/contacts/"), params=parameters)

    def get_companies(self, company_name=None, status=None, company_identifier=None, db_rid=None):
        conditionstring = ""
        if db_rid:
            conditionstring = self._add_condition(conditionstring, 'id', db_rid)
        if company_name:
            conditionstring = self._add_condition(conditionstring, 'name', company_name)
        if status:
            conditionstring = self._add_condition(conditionstring, 'status', status)
        if company_identifier:
            conditionstring = self._add_condition(conditionstring, 'identifier', company_identifier)
        print(conditionstring)
        parameters = {
            "conditions": conditionstring
            }

        return self.connection.get(self._url("/company/companies/"), params=parameters)

    def get_configurations(self, type=None, last_name=None, company_identifier=None, db_rid=None, status="active"):
        conditionstring = ""
        if status:
            conditionstring = self._add_condition(conditionstring, 'status/name', status)
        if db_rid:
            conditionstring = self._add_condition(conditionstring, 'id', db_rid)
        if type:
            conditionstring = self._add_condition(conditionstring, 'type/name', type)
        if last_name:
            conditionstring = self._add_condition(conditionstring, 'naame', last_name)
        if company_identifier:
            conditionstring = self._add_condition(conditionstring, 'company/identifier', company_identifier)

            print(conditionstring)
        parameters = {
            "conditions": conditionstring,
            "pageSize": 1000
            }

        return self.connection.get(self._url("/company/configurations/"), params=parameters)

    def create_new_ticket(self, summary, company_identifier, contact_name=None, ticket_type=None, sub_type=None, service_item=None, initial_description=None):
        data = {
            "summary": summary,
            "company":  {"identifier": company_identifier}
                }
        if contact_name:
            data['contact'] = {}
            data['contact']['id'] = self._get_contact_id(contact_name, company_identifier)
        if ticket_type:
            data['type'] = {}
            data['type']['name'] = ticket_type
        if sub_type:
            data['subType'] = {}
            data['subType']['name'] = sub_type
        if service_item:
            data['item'] = {}
            data['item']['name'] = service_item
        if initial_description:
            data['initialDescription'] = initial_description

        print(data)

        resp = self.connection.post(self._url('/service/tickets/'), json=data)
        print(resp)
        print(resp.json())
        return resp

    def patch_configuration(self, conf_id, op, path, value):

        data= [{
            "op": op,
            "path": path,
            "value": value,
        }]
        print(data)
        resp = self.connection.patch(self._url("/company/configurations/{}/".format(conf_id)), json=data)
        print(resp)
        print(resp.json)
        return resp

if __name__ == "__main__":

    company_id = 'LTL'
    pub_key = 'FFjbc6tutXn1Aduf'
    priv_key = 'iG0MSc9OkJd42YtE'
    #cookie_val = 'LuminaTechnologies'

    auth = generate_auth(company_id, pub_key, priv_key)
    #auth = 'TFRMK0ZGamJjNnR1dFhuMUFkdWY6aUcwTVNjOU9rSmQ0Mll0RQ=='



    #connection = requests.Session()

    #connection.auth(auth)
    #connection.headers={"Authorization": "Basic %s" % auth}


    connectwise = CWAPIClient('psa.luminatech.co.uk', auth)
    summary = 'Test Ticket - Please delete'
    target_company_id = 'LTL'
    company_contact = "Dave Grimmer"
    ticket_type = "Planned Maintenance"
    ticket_subtype = "Proactive Maintenance"
    description = """Creation reason: Attempting to raise ticket as non-default company contact via REST API:
     Tried contact as: {}""".format(company_contact)
    connectwise.create_ticket(summary=summary, company_identifier=company_id, contact_name=company_contact, ticket_type=ticket_type, sub_type=ticket_subtype, initial_description=description)
    #print(connectwise._get_contact_id(company_contact, company_id))
    #connectwise.patch_ticket()

    #connectwise.get_tickets()
    #connectwise.get_companies()
    #connectwise.get_boards()

