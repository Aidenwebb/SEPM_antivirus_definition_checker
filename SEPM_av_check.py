import sys
import json
import csv
import pymssql
import _mssql  # required to make pyinstaller .exe work
import decimal  # required to make pyinstaller .exe work
import uuid  # required to make pyinstaller .exe work
from datetime import datetime
import logging

FORMAT = '%(asctime)-15s - %(message)s'

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
        logging.basicConfig(filename=config['execution_log_file'], level=logging.INFO, format=FORMAT)

except:

    with open('config.json', 'w') as f:
        config = {

            "database_server": "",
            "database_port": "",
            "database_user": "",
            "database_pass": "",
            "database_name": "",
            "execution_log_file": "SEPM_av_check.log"
        }
        json.dump(config, f, indent=2, sort_keys=True)
        logging.basicConfig(filename=config['execution_log_file'], level=logging.INFO, format=FORMAT)
        logging.info("Config not found. Writing default config file")

report_file = config["report_file"]
report_threshold = config['report_threshold_older_than_days']

# Config connection

server = config["database_server"]
user = config["database_user"]
password = config["database_pass"]
db_name = config["database_name"]

conn = pymssql.connect(server, user, password, db_name)
cursor = conn.cursor()

statement = """
select i.COMPUTER_NAME
, pat.version as DEFINITION_DATE
, dateadd(s,convert(bigint,LAST_UPDATE_TIME)/1000,'01-01-1970 00:00:00') LASTUPDATETIME
, g.name as GROUP_NAME
, i.CURRENT_LOGIN_USER
from sem_agent as sa with (nolock) left outer join pattern pat on sa.pattern_idx=pat.pattern_idx
inner join v_sem_computer i on i.computer_id=sa.computer_id
inner join identity_map g on g.id=sa.group_id
where
(sa.agent_type='105' or sa.agent_type='151') and sa.deleted='0' and I.DELETED = 0
order by group_name, i.COMPUTER_name;"""

cursor.execute(statement)

result = cursor.fetchall()


def write_csv(pc_name, av_date, last_seen, diff_av_last_seen, sepm_path, user_login):
    with open(report_file, 'a', newline='') as csvfile:
        data = [pc_name, av_date, last_seen, diff_av_last_seen, sepm_path, user_login]
        print_row(*data)

        file = csv.writer(csvfile, delimiter=',')
        try:
            file.writerow(data)
        except Exception as e:
            logging.error(e)
            logging.error("{0} - {1} ".format(data, e))

def print_row(pc_name, rev_date, seen_date, date_diff, SEPM_path, last_user):
    print(
        "{:15} | {:14} | {:14} | {:9} | {:<30} | {:<20}".format(pc_name, str(rev_date), str(seen_date), date_diff,
                                                                              str(SEPM_path), last_user,
                                                                              end=' '))


write_csv("Computer Name", "Def File Date", "Last Seen Date", "Days diff", "SEPM path", "Last logged in user")

#print_row("Computer Name", "Def File Date", "Last Seen Date", "Days diff", "SEPM path", "Last logged in user")

if __name__ == "__main__":

    return_outdated = False

    for x in result:
        computer_name = x[0]
        revision = x[1].split(' ')[0]
        rev_date = datetime.strptime(revision, "%Y-%m-%d").date()
        timestamp = x[2].date()
        path = x[3]
        user = x[4]
        delta = timestamp - rev_date
        days = delta.days

        if days > report_threshold:
            return_outdated = True
            write_csv(computer_name, rev_date, timestamp, days, path, user)

    if return_outdated is True:
        sys.exit(1)

    else:
        sys.exit(0)