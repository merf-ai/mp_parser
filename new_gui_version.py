from package import programm
import PySimpleGUI as sg
import clipboard as cd

WINDOW=None

def login_layout_prepare(visible_error_login=False):
    '''Создание окна входа и его прослушивание'''
    global WINDOW
    layout_login = [[sg.Text('Логин'),sg.Input(key='login'),sg.Button('Вставить текст',key='login_paste')],
                [sg.Text('Пароль'),sg.Input(key='password'),sg.Button('Вставить текст',key='password_paste')],
                [sg.Text('Данные введены неправильно,попробуйте,ещё раз!',key='error_login',visible=visible_error_login)],
                [sg.Button('Войти',key='login_but'), sg.Button('Выход')] ]
    WINDOW = sg.Window('Вход',layout_login)
    while True:
        event, values = WINDOW.read()
        if event == sg.WIN_CLOSED or event == 'Выход': 
            break
        elif event=='login_paste':
            WINDOW['login'].update(values['login']+cd.paste())
        elif event=='password_paste':
            WINDOW['password'].update(values['password']+cd.paste())
        elif event=='login_but':
            s,responce,logintoken=programm.find_logintoken()
            try:
                responce2,MAIN_SESSION,all_courses=programm.login_on_MP(responce,*values.values(),logintoken)
            except ValueError:
                WINDOW.close()
                login_layout_prepare(visible_error_login=True)
                return
            WINDOW.close()
            cours_layout_prepare(responce2,MAIN_SESSION,all_courses)

def cours_layout_prepare(responce2,MAIN_SESSION,all_courses,visible_course_error=False):
    '''Создание окна выбора курса и его прослушивание'''
    global WINDOW
    layout_cours=[
    [sg.Text('Вы успешно вошли!')],
    [sg.Text('Доступные курсы')],
    [sg.Listbox(values=list(all_courses.keys()),key='cours_list',size=(20,15),horizontal_scroll=True,select_mode='single')],
    [sg.Text('Выберите какой-нибудь курс!',text_color='red',visible=visible_course_error,key='cours_error')],
    [sg.Button('Выбрать',key='take_cours')],[sg.Button('Назад',key='back')]
    ]
    WINDOW=sg.Window('Курсы',layout_cours)
    while True:
        event, values = WINDOW.read()
        if event == sg.WIN_CLOSED :
            break
        if event =='back':
            WINDOW.close()
            login_layout_prepare()
        if event=='take_cours':
            try:
                cours_name=values['cours_list'][0]
                tests_name_and_links=programm.cours_page_open(responce2,MAIN_SESSION,all_courses,cours_name)
            except IndexError:
                WINDOW.close()
                cours_layout_prepare(responce2,MAIN_SESSION,all_courses,visible_course_error=True)
            WINDOW.close()
            tests_layout_prepare(tests_name_and_links,responce2,MAIN_SESSION,all_courses)

def tests_layout_prepare(tests_name_and_links,responce2,MAIN_SESSION,all_courses,visible_test_error=False):
    '''Создание окна выбора теста и его прослушивание'''
    global WINDOW
    layout_tests=[
    [sg.Text('Доступные тесты')],
    [sg.Listbox(values=list(tests_name_and_links.keys()),key='tests_list',size=(20,20),horizontal_scroll=True,select_mode='single')],
    [sg.Text('Выберите какой-нибудь тест!',text_color='red',visible=visible_test_error,key='test_error')],
    [sg.Button('Выбрать',key='take_test')],[sg.Button('Назад',key='back')]
    ]   
    WINDOW=sg.Window('Доступные тесты',layout_tests)
    while True:
        event, values = WINDOW.read()
        if event == sg.WIN_CLOSED :
            break
        if event =='back':
            WINDOW.close()
            cours_layout_prepare(responce2,MAIN_SESSION,all_courses)
        if event =='take_test':
            if  not bool(values['tests_list']):
                WINDOW.close()
                tests_layout_prepare(tests_name_and_links,responce2,MAIN_SESSION,all_courses,visible_test_error=True)
                return
            responce4=programm.test_page_open(*values['tests_list'],tests_name_and_links,MAIN_SESSION)
            WINDOW.close()
            file_test_layout_prepare(responce4,MAIN_SESSION,tests_name_and_links,responce2,all_courses)



def file_test_layout_prepare(responce4,MAIN_SESSION,tests_name_and_links,responce2,all_courses,visible_file_error=False,process_complete=False):
    '''Создание окна выбора файла и его прослушивание'''
    global WINDOW
    layout=[
    [sg.Text('Выберите путь к файл')],
    [sg.FileBrowse('Выберите файл,для поиска ответа',key='file_url')],
    [sg.Text('Файл не выбран!',text_color='red',visible=visible_file_error,key='file_error')],
    [sg.Text('Процесс завершён успешно!',text_color='green',visible=process_complete,key='process_complete')],
    [sg.Button('Продолжить',key='take_file')],[sg.Button('Назад',key='back')]
    ]
    WINDOW=sg.Window('Файл',layout)
    while True:
        event, values = WINDOW.read()
        if event == sg.WIN_CLOSED :
            break
        if event =='back':
            WINDOW.close()
            tests_layout_prepare(tests_name_and_links,responce2,MAIN_SESSION,all_courses)
            return
        if event=='take_file':
            responce5,sesskey=programm.attempt_page_open(responce4,MAIN_SESSION)
            if len(values['file_url'])==0:
                WINDOW.close()
                file_test_layout_prepare(responce4,MAIN_SESSION,tests_name_and_links,responce2,all_courses,visible_file_error=True)
            programm.answer_on_questions(responce5,sesskey,values['file_url'],MAIN_SESSION)
            


login_layout_prepare()
