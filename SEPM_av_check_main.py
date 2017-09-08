import datetime
import logging
import sys
import json
import pyrestcwapi
import SEPM_av_check
import re
import os

FORMAT = '%(asctime)-15s - %(message)s'

if __name__ == "__main__":

    if os.path.isfile('config.json'):
        with open('config.json', 'r') as f:
            config = json.load(f)
            logging.basicConfig(filename=config['execution_log_file'], level=logging.INFO, format=FORMAT)

    else:
        with open('config.json', 'w') as f:
                config = {
                  "database_server": "SEPM_DB_SERVER",
                  "database_port": 1433,
                  "database_user": "DB_READONLY_User",
                  "database_pass": "DBUsers_password",
                  "database_name": "SEPM",
                  "execution_log_file": "SEPM_av_check.log",
                  "report_file": "report.csv",
                  "report_threshold_older_than_days": 14,
                  "exclusions": {
                      "regex": {
                          "computer_name_contains": [
                          ],
                          "company_id_contains": [
                          ]
                      }
                  },
                  "connectwise": {
                    "auto_create_tickets": False,
                    "testmode": {
                        "active": True,
                        "reason": "Code Refactor"
                    },
                    "auth": "BASE 64 API AUTH TOKEN",
                    "server": "API SERVER",
                    "sepm_path_pairing": {
                        "SEPM PATH ID": "CONNECTWISE COMPANY IDENTIFIER",
                      }
                  }
                }
                json.dump(config, f, indent=2, sort_keys=True)
                logging.basicConfig(filename=config['execution_log_file'], level=logging.INFO, format=FORMAT)
                logging.info("Config not found. Writing default config file")

    report_file = config["report_file"]
    report_threshold = config['report_threshold_older_than_days']

    # Config connection

    if config['connectwise']['auto_create_tickets'] is True:
        auth = config['connectwise']['auth']
        server = config['connectwise']['server']
        connectwise = pyrestcwapi.CWAPIClient(server, auth)
        if config['connectwise']['testmode']['active'] is True:
            summary_base = "TEST TICKET - Reason: {}".format(config['connectwise']['testmode']['reason'])
        else:
            summary_base = "AV definitions out of date"

        ticket_type = 'Planned Maintenance'
        ticket_subtype = 'Proactive Maintenance'
        ticket_service_item = 'System Checks'

    server = config["database_server"]
    user = config["database_user"]
    password = config["database_pass"]
    db_name = config["database_name"]

    SEPM_TO_CW_ID = config['connectwise']['sepm_path_pairing']

    return_outdated = False

    SEPM_av_check.write_csv(report_file, "Ticket ID", "Computer Name", "Def File Date", "Last Seen Date", "Days diff", "SEPM path", "Last logged in user")

    result = SEPM_av_check.sepm_query(server, user, password, db_name)

    for x in result:
        skip_flag = False
        computer_name = x[0]
        revision = x[1].split(' ')[0]
        #print(x, x[1])
        #if x[1] == "":
        #    revision=("1970-01-01")
        if revision == "":
            revision = ("1970-01-01")
        rev_date = datetime.datetime.strptime(revision, "%Y-%m-%d").date()
        timestamp = x[2].date()
        path = x[3]
        user = x[4]
        delta = timestamp - rev_date
        days = delta.days
        for excluded_computer_name in config['exclusions']['regex']['computer_name_contains']:
            if re.search(excluded_computer_name, computer_name):
                skip_flag = True
                #print("Skipping Computer Name: {} because it matches regex {}".format(computer_name, excluded_computer_name))
        for excluded_company_id in config['exclusions']['regex']['company_id_contains']:
            if re.search(excluded_company_id, path):
                skip_flag = True
                #print("Skipping Computer Name: {} because its path ({}) belongs to excluded company {}".format(computer_name, path, excluded_company_id))

        if (days > report_threshold):
            if skip_flag is True:
                SEPM_av_check.write_csv(report_file, "Excluded", computer_name, rev_date, timestamp, days, path, user)
                continue
            if config['connectwise']['auto_create_tickets'] is True:
                summary = ("{} - {}").format(summary_base, computer_name)
                #company_id = path.split('\\')[1]
                try:
                    company_id = SEPM_TO_CW_ID[path.split('\\')[1]].strip()
                except:
                    company_id = "LTL"
                description = """
                Please review the below and update virus definitions
                Host Name	{}
                Last seen	{}
                Definition Date	{}
                Approx days between AV Definition and last seen dates	{}
                SEPM Path   {}

                KB: http://kb.luminatech.co.uk/kb/index.php?View=file&EntryID=18
                """.format(computer_name, timestamp, rev_date, days, path)
                print(summary)
                print(company_id)
                print(description)

                resp = connectwise.create_new_ticket(summary=summary, company_identifier=company_id, ticket_type=ticket_type, sub_type=ticket_subtype, service_item=ticket_service_item, initial_description=description)

                try:
                    print(resp.json())
                    ticket_id = resp.json()['id']
                    SEPM_av_check.write_csv(report_file, ticket_id, computer_name, rev_date, timestamp, days, path, user)
                except:
                    print(resp.json())
                    SEPM_av_check.write_csv(report_file, "No ID found", computer_name, rev_date, timestamp, days, path, user)
                    pass

            else:
                SEPM_av_check.write_csv(report_file, '', computer_name, rev_date, timestamp, days, path, user)


            return_outdated = True
            if config['connectwise']['testmode']['active'] is True:
                break

    if return_outdated is True:
        sys.exit(1)

    else:
        sys.exit(0)