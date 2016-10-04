import requests
import time
import sqlite3
import timeit

TOTAL_UNIQUE_COURSES = 0


def main():
    subjects = get_all_subjects()
    # subjects = [198, 180]


    start = timeit.default_timer()

    conn = sqlite3.connect('RU SOC.db')
    subjects_to_db(subjects, conn)

    conn.close()

    stop = timeit.default_timer()

    print('duration: {}'.format(stop - start))

    print('\n\n{}'.format(TOTAL_UNIQUE_COURSES))
    return


def get_all_subjects():
    l = 'https://sis.rutgers.edu/soc/subjects.json?semester=92016&campus=NB&level=U'
    r = requests.get(l).json()
    subjects = []

    for c in r:
        subjects.append(c['code'])

    return subjects


def subjects_to_db(subjects, conn):
    global TOTAL_UNIQUE_COURSES
    db_conn = conn.cursor()
    db_conn.execute('''CREATE TABLE IF NOT EXISTS Fall_2016_SOC(course_unit TEXT,course_subject TEXT,course_number TEXT,course_full_number TEXT,name TEXT,section_number TEXT,section_index TEXT,section_open_status TEXT,instructors TEXT,times TEXT,notes TEXT,exam_code TEXT,campus TEXT,credits INT,url TEXT,pre_reqs TEXT,core_codes TEXT,last_updated TEXT)''')
    # subjects_course_ct = {}
    # print(len(subjects))

    ct = 0
    for s in subjects:  # requests all subjects
        while True:
            try:
                # time.sleep(1)
                l = 'https://sis.rutgers.edu/soc/courses.json?subject={}&semester=92016&campus=NB&level=U'.format(s)
                r = requests.get(l).json()
                # subjects_course_ct[s] = 0
                print('SUBJECT: {} - - - - - - - - - - - - - - - - - - - - -'.format(s))

                for c in r:  # iterates through all courses within the subject
                    # ct +=1
                    course_unit_code = c['offeringUnitCode']
                    course_subject = c['subject']
                    course_number = c['courseNumber']
                    course_full_num = '{}:{}:{}'.format(course_unit_code, course_subject, course_number)
                    course_short_title = c['title'].strip()
                    course_sections = c['sections']
                    course_campus = c['campusCode']
                    course_credits = c['credits']
                    course_url = c['synopsisUrl']
                    course_pre_reqs = c['preReqNotes']
                    course_core_codes = str(c['coreCodes'])


                    for section in course_sections:
                        ct += 1
                        section_num = section['number']
                        section_index = section['index']
                        if section['openStatus']:
                            section_open_status = 'OPEN'
                        else:
                            section_open_status = 'CLOSED'
                        section_instructors = str(section['instructors'])
                        section_times = str(section['meetingTimes'])
                        section_notes = section['sectionNotes']
                        section_exam_code = section['examCode']
                        last_updated_time = time.strftime('%m-%d-%Y %H:%M')
                        db_conn.execute('insert into Fall_2016_SOC values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                                        (course_unit_code,
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
                                         last_updated_time))
                        print('{} | '.format(ct), end='')
                        print('{}\t{}\tSECTION {}\tINDEX {}\t{}'.format(course_full_num, course_short_title, section_num,
                                                                        section_index, section_open_status))

                        # print('{}\t{}'.format(course_full_num, course_short_title))
                    TOTAL_UNIQUE_COURSES += 1
                    # subjects_course_ct[s] += 1

                conn.commit()
            except:
                secs_to_wait = 5
                print('\n\033[91mFailed on subject {}. Trying again in {} seconds.\033[0m\n'.format(s, secs_to_wait))
                time.sleep(secs_to_wait)
                continue
            break

if __name__ == '__main__':
    main()
