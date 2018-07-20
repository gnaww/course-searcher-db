import psycopg2
import json

import time
import timeit

import grequests
import requests

TOTAL_UNIQUE_COURSES = 0


def main():
    semester_campus_level_combos = [
        {'Semester': '92018', 'Campus': 'NB', 'Level': 'U'},
        {'Semester': '92018', 'Campus': 'NB', 'Level': 'G'},
        {'Semester': '92018', 'Campus': 'NK', 'Level': 'U'},
        {'Semester': '92018', 'Campus': 'NK', 'Level': 'G'},
        {'Semester': '92018', 'Campus': 'CM', 'Level': 'U'},
        {'Semester': '92018', 'Campus': 'CM', 'Level': 'G'}
    ]
    subjects = get_all_subjects()
    start = timeit.default_timer()
    # dbpass = input("Please enter db password")
    try:
        conn = psycopg2.connect("dbname='course-planner' user='postgres' host='127.0.0.1' password=''")
        # conn = psycopg2.connect("dbname='courseplanner' user='postgres' host='localhost' password='" + dbpass + "\'")
    except:
        print("db connection error")
    subjects_to_db(subjects, conn)
    conn.close()
    stop = timeit.default_timer()

    print('DURATION: {}'.format(stop - start))
    # print('\n\n{}'.format(TOTAL_UNIQUE_COURSES))

    # TO DO HERE: FINISH THE REST API AND DETERMINE HOW YOU WANT THE QUERIES TO COME IN.
    # MORE TO DO: OPTIMIZE THE DATA FURTHUR, INCLUDE DURATION OF EACH CLASS TIME, AND OTHER INFORMATION
    # GATHER MORE INFORMATIN FOR EACH SECTION AS WELL, ALONG WITH THE CURRENT ONES

    return


def get_all_subjects():
    l = 'https://sis.rutgers.edu/soc/subjects.json?semester=92018&campus=NB&level=U'
    r = requests.get(l).json()
    subjects = []

    for c in r:
        subjects.append(c['code'])
    return subjects


def subjects_to_db(subjects, conn):
    global TOTAL_UNIQUE_COURSES
    db_conn = conn.cursor()
    db_conn.execute(
        '''
        DROP TABLE IF EXISTS courses;
        CREATE TABLE IF NOT EXISTS public."courses"(
            course_unit integer,
            course_subject integer,
            course_number integer,
            course_full_number text COLLATE pg_catalog."default",
            name text COLLATE pg_catalog."default",
            section_number character(2) COLLATE pg_catalog."default",
            section_index integer,
            section_open_status text COLLATE pg_catalog."default",
            instructors text COLLATE pg_catalog."default",
            times jsonb,
            notes text COLLATE pg_catalog."default",
            exam_code character(1) COLLATE pg_catalog."default",
            campus character(2) COLLATE pg_catalog."default",
            credits real,
            url text COLLATE pg_catalog."default",
            pre_reqs text COLLATE pg_catalog."default",
            core_codes jsonb,
            last_updated text COLLATE pg_catalog."default"
            )
        '''
    )
    db_conn.execute('''
                        PREPARE coursesplan (integer, integer, integer, text, text, character, integer, text, text, jsonb, text, character, character, real, text, text, jsonb, text) AS
                            INSERT INTO courses VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18);'''
    )
    # subjects_course_ct = {}
    # print(len(subjects))
    request_urls = ['https://sis.rutgers.edu/soc/courses.json?subject={}&semester=92018&campus=NB&level=U'.format(s) for
                    s in subjects]
    all_requests = (grequests.get(u) for u in request_urls)
    request_results = zip(grequests.map(all_requests), request_urls)

    ct = 0
    for result in request_results:  # requests all subjects
        while True:
            try:
                r = result[0].json()
                print('URL: {} - - - - - - - - - - - - - - - - - - - - -'.format(result[0].url))
            except (AttributeError, ConnectionError):
                r = requests.get(result[1]).json()
                print('URL: {} - - - - - - - - - - - - - - - - - - - - -'.format(result[1].url))
                time.sleep(1)
            break
        # subjects_course_ct[s] = 0
        placeholder = {}
        print(r)
        for c in r:  # iterates through all courses within the subject
            # ct +=1
            course_unit_code = c['offeringUnitCode']
            course_subject = c['subject']
            course_number = c['courseNumber']
            course_full_num = '{}:{}:{}'.format(course_unit_code, course_subject, course_number)
            course_short_title = c['title'].strip().replace("'", "")
            course_sections = c['sections']
            course_campus = c['campusCode']
            course_credits = 0
            if c['credits'] is not None:
                course_credits = c['credits']
            course_url = c['synopsisUrl']
            course_pre_reqs = c['preReqNotes']
            course_core_codes = json.dumps(placeholder)
            if c['coreCodes']:
                course_core_codes = json.dumps((c['coreCodes'])[0])

            for section in course_sections:
                ct += 1
                section_num = section['number']
                section_index = section['index']
                if section['openStatus']:
                    section_open_status = 'OPEN'
                else:
                    section_open_status = 'CLOSED'

                section_instructors = None
                for d in section['instructors']:
                    if section_instructors is not None:
                        section_instructors += " and {}".format(d["name"])
                    else:
                        section_instructors = d["name"]
                if section_instructors is not None:
                    section_instructors = section_instructors.replace("'", "")

                section_times = json.dumps((section['meetingTimes'][0]))
                section_notes = section['sectionNotes']
                if section['sectionNotes'] is not None:
                    section_notes = section_notes.replace("'", "")

                section_exam_code = section['examCode']
                last_updated_time = time.strftime('%m-%d-%Y %H:%M')
                db_conn.execute('''
                    EXECUTE coursesplan({}, {}, {}, \'{}\', \'{}\', \'{}\', {}, \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\', \'{}\');
                    '''.format(
                                 course_unit_code,
                                 course_subject,
                                 course_number,
                                 course_full_num,
                                 course_short_title,
                                 section_num,
                                 section_index,
                                 section_open_status,
                                 section_instructors,
                                 section_times,
                                 section_notes,
                                 section_exam_code,
                                 course_campus,
                                 course_credits,
                                 course_url,
                                 course_pre_reqs,
                                 course_core_codes,
                                 last_updated_time
                        )
                )
                print('{} | '.format(ct), end='')
                print('{}\t{}\tSECTION {}\tINDEX {}\t{}'.format(course_full_num, course_short_title, section_num,
                                                                section_index, section_open_status))

                # print('{}\t{}'.format(course_full_num, course_short_title))
            TOTAL_UNIQUE_COURSES += 1
            # subjects_course_ct[s] += 1

        conn.commit()
        # except:
        #     secs_to_wait = 5
        #     print('\n\033[91mFailed on subject {}. Trying again in {} seconds.\033[0m\n'.format(s, secs_to_wait))
        #     time.sleep(secs_to_wait)
        #     continue
        # break


if __name__ == '__main__':
    main()
