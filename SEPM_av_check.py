import csv
import pymssql
import _mssql  # required to make pyinstaller .exe work
import decimal  # required to make pyinstaller .exe work
import uuid  # required to make pyinstaller .exe work
import logging

FORMAT = '%(asctime)-15s - %(message)s'

def sepm_query(server, user, password, db_name):
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
    return result

def write_csv(file_path, pc_name, av_date, last_seen, diff_av_last_seen, sepm_path, user_login):
    with open(file_path, 'a', newline='') as csvfile:
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