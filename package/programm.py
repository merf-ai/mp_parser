'''Вход на сайт Мосполитех СДО'''

from bs4 import BeautifulSoup 
import requests
import os 


def check_login_and_password_on_MP(soup):
    '''Проверка правильности ввода логина и пароля пользователем'''
    title=soup.find('title')
    if 'Вход' in title.text:
        return True
    else:
        return False


def test_check_img(soup):
    '''Нахождение всех тестов на странице курса по картинке'''
    return list(filter(lambda x:'quiz' in x.find('img')['src'],soup.find_all('a',class_='aalink')))


def test_check_span(soup):
    ''''Нахождение всех тестов на странице курса по тексту в теге span'''   
    return list(filter(lambda x:'тест' in x.find('span',class_='instancename').text.lower(),soup.find_all('a',class_='aalink')))
 

def question_find_radio(form):
    '''Нахождение вариантов ответов на странице,если на ней только radio кнопки'''
    form_answer=form.find('div',class_='formulation clearfix').find('div',class_='answer')
    divs_radio=form_answer.find_all('div')
    answer_dict={}
    for tag in divs_radio:
        tag_value=tag.find_next().get('value')
        if tag_value is None:
            continue
        tag_answer =tag.find_next().find_next().text
        if tag.find_next().find_next().name=='div':
            tag_answer=' '.join(tag_answer.split()[1:])     
        answer_dict[tag_answer]=tag_value
    return answer_dict


def question_find_checkbox(form):
    '''Нахождение вариантов ответов на странице,если на ней только checkbox кнопки'''
    form_answer=form.find('div',class_='formulation clearfix').find('div',class_='answer')
    divs_checkbox=form_answer.find_all('div')
    answer_dict={}
    for tag in divs_checkbox:
        tag_value=tag.find_next().find_next().get('value')
        tag_name=tag.find_next().find_next().get('name')
        if tag_value is None :
            continue
        tag_answer =tag.find_next().find_next().find_next().text
        if tag.find_next().find_next().find_next().name=='div':
            tag_answer=' '.join(tag_answer.split()[1:])     
        answer_dict[tag_answer]=tag_name
    return answer_dict


def question_find_text():
    '''Нет необходимости находить вариант ответа на вопрос,если форма text,
    так как его не существует,функция создана,для сохранения структуры кода'''
    pass


def test_find(form_tag,ses):
    ''''Находит все тесты на странице и возвращает словарь в следующем виде 
    название теста:ссылка'''
    tests_on_page=test_check_img(form_tag)
    titles_h3=form_tag.find_all('h3',class_='section-title')
    urls=list(map(lambda x:x.find('a'),titles_h3))
    for url in urls:
        if bool(url):
            url=url['href']
            arr_url=url.split('?')[1]
            param_url=arr_url.split('&')
            datas={
                'id':param_url[0].split('=')[1],
                'section':param_url[1].split('=')[1]
            }
            res=ses.post(url,headers=header,data=datas)
            tests_on_page.extend(test_check_img(BeautifulSoup(res.text,'html.parser')))
    return dict(zip(list(map(lambda x:x.find('span',class_='instancename').text,tests_on_page)),list(map(lambda x:x['href'],tests_on_page))))


def file_record(file_name,text_record):
    '''Запись текста ответа сервера в файл'''
    with open(os.path.join("package\\responce_files", file_name) ,'w',encoding='UTF-8') as F:
        F.writelines(text_record.split('/n'))
        return F


def find_logintoken():
    '''Нахождение logintiken пользователя'''
    s=requests.Session()
    responce=s.post('https://online.mospolytech.ru/login/index.php')

    F=file_record('MPlog.txt',responce.text)
    soup = BeautifulSoup(responce.text, 'html.parser')
    logintoken=soup.find('div',class_='submit-wrapper').find_all('input')[1]['value']
    s.close
    return s,responce,logintoken


def login_on_MP(responce,username,password,logintoken):
    '''Вход пользователя на сайт,и создание сессии,которая будет использоваться 
    в дальнейшем'''
    s2=requests.Session()
    cookie_dict=[
    {'domain':key.domain,'name':key.name,'path':key.path,'value':key.value}
    for key in responce.cookies
    ]
    for k in cookie_dict:
        s2.cookies.set(**k)
    datas={
    'username':username,
    'password':password,
    'logintoken':logintoken 
    } 
    responce2=s2.post('https://online.mospolytech.ru/login/index.php',headers=header,data=datas)
    if check_login_and_password_on_MP(BeautifulSoup(responce2.text,'html.parser')):
        raise ValueError('Введены неверный пароль или логин!')
    F=file_record('MPlog_1.txt',responce2.text)
    all_courses=list(map(lambda x:x.find('div').find('a'),BeautifulSoup(responce2.text,'html.parser').find('ul',class_='unlist').find_all('li')))
    return responce2,s2,dict(zip(tuple(map(lambda x:x.text,all_courses)),tuple(map(lambda x:x['href'],all_courses))))


def cours_page_open(responce_form,session,all_courses,cours_name):
    ''''Переход на страницу выбранного курса'''
    soup_page_courses=BeautifulSoup(responce_form.text,'html.parser')
    try:
        cours=all_courses[cours_name]
    except KeyError:
        raise KeyError('Выбранного курса не существует')
    except IndexError:
        raise IndexError('Курс не выбран!')
    datas={
        'id':cours.split('=')[1]
    }
    responce3=session.post(cours,data=datas,headers=header)
    soup_for_courses=BeautifulSoup(responce3.text,'html.parser')
    #test_links=test_check_img(soup_for_courses) test_names_and_links=dict(zip(list(map(lambda x:x.find('span',class_='instancename').text,test_links)),list(map(lambda x:x['href'],test_links))))-раньше так находил тесты,но способ не работает,там где пристутствуют разделы,например английский язык 
    test_names_and_links=test_find(soup_for_courses,session)
    F=file_record('MP_cours.txt',responce3.text)
    return test_names_and_links

def attempt_page_open(responce,ses):
    '''Переход на страницу попытки'''
    access="Y"
    soup_attempt=BeautifulSoup(responce.text,'html.parser')
    attempt_form=soup_attempt.find('div',class_='box py-3 quizattempt').find('div',class_='singlebutton quizstartbuttondiv').find('form')
    sesskey=attempt_form.find('input').find_next()['value']
    data_for_attempt={
        "cmid":attempt_form.find_next('input')['value'],
        'sesskey':sesskey
    }    
    warning_form=soup_attempt.select_one('input[name="_qf__mod_quiz_preflight_check_form"]')
    if (warning_form is not None) and (warning_form.get('value')=="1"):
        access=input('Данный тест имеет ограничение по времени,вы уверены,что хотите начать?,введите Y,если да')
        data_for_attempt.update({
            '_qf__mod_quiz_preflight_check_form':'1',
            'submitbutton':'Начать попытку'
        })  
    if access=='Y':     
        responce5=ses.post(attempt_form['action'],headers=header,data=data_for_attempt)
        F=file_record('MP_attempt.txt',responce5.text)
    return responce5,sesskey

def test_page_open(test_name,all_test_dict,session):
    '''Переход на страницу с тестом'''
    try:
        test=all_test_dict[test_name]
    except KeyError:
        raise KeyError('Выбранного теста не существует!')
    data_test={
        'id':test.split('=')[1]
    }
    responce4=session.post(test,data=data_test,headers=header)
    F=file_record('MP_test.txt',responce4.text)
    return responce4

def answer_on_questions(responce5,sesskey,file_name,s2):
    '''Проходит по всем страницам теста и отвечает на вопросы'''
    soup_attempt_answer=BeautifulSoup(responce5.text,'html.parser')
    form_answer=soup_attempt_answer.find('form',id='responseform')
    form_clearfix=form_answer.find('div',class_='formulation clearfix')
    sequencecheck_input=form_clearfix.find('input')
    pages_num=len(soup_attempt_answer.find('div',class_='qn_buttons clearfix multipages').find_all('a'))
    attempt=form_answer.select_one('input[name="attempt"]')
    cmid=soup_attempt_answer.select_one('input[name="cmid"]')['value']
    '''Получаем данные из файла'''
    all_type_answer_dict=file_answer_scanner(file_name)


    for a in range(1,pages_num+1):
        form_clearfix=form_answer.find('div',class_='formulation clearfix')
        scrollpos=form_answer.select_one('input[name="scrollpos"]')['value']
        slots=form_answer.select_one('input[name="slots"]')
        this_page=form_answer.select_one('input[name="thispage"]')['value']
        next_page=str(int(this_page)+1)
        sequencecheck=form_answer.find('div',class_='formulation clearfix').find('input')
        q=sequencecheck['name'].split('_')[0]
        form_type=type_check_beta(form_clearfix,sequencecheck['name'])
        qvalue='-1'
        if form_type=='input_answer_radio':
            question_dict=question_find_radio(form_answer)
            qtext=' '.join(form_clearfix.find('div',class_='qtext').text.split())
            for a in all_type_answer_dict['input_answer_radio']:
                if a==qtext:
                    for b in all_type_answer_dict['input_answer_radio'][a]:
                        for c in question_dict:
                            if c==b:
                                qvalue=question_dict[c]
            datas={
            f'{q}_:flagged':'0',
            f'{q}_:flagged':'0',
            sequencecheck['name']:sequencecheck['value'],
            f'{q}_answer':qvalue,
            'next':'Следующая страница',
            'attempt': attempt['value'],
            'thispage': this_page,
            'nextpage': next_page,
            'timeup': '0',
            'sesskey':sesskey,
            'scrollpos':scrollpos ,
            'slots': slots['value']
            }
        if form_type=='input_choice_checkbox':
            question_dict=question_find_checkbox(form_answer)
            qvalue={question_dict[a]:'0' for a in question_dict}
            qtext=' '.join(form_clearfix.find('div',class_='qtext').text.split())
            for a in all_type_answer_dict['input_choice_checkbox']:
                if a==qtext:
                    for b in all_type_answer_dict['input_choice_checkbox'][a]:
                        for c in question_dict:
                            if c==b:
                                qvalue[question_dict[c]]='1'
            datas={
            f'{q}_:flagged':'0',
            f'{q}_:flagged':'0',
            sequencecheck['name']:sequencecheck['value'],
            'next':'Следующая страница',
            'attempt': attempt['value'],
            'thispage': this_page,
            'nextpage': next_page,
            'timeup': '0',
            'sesskey':sesskey,
            'scrollpos':scrollpos ,
            'slots': slots['value']
            }
            datas.update(qvalue)
        if (form_type=='input_answer_text'):
            qtext=' '.join(form_clearfix.find('div',class_='qtext').text.split())
            qvalue=''
            for a in all_type_answer_dict['input_answer_text']:
                if qtext==a:
                    qvalue=all_type_answer_dict['input_answer_text'][a][0]
            datas={
            f'{q}_:flagged':'0',
            f'{q}_:flagged':'0',
            sequencecheck['name']:sequencecheck['value'],
            f'{q}_answer':qvalue,
            'next':'Следующая страница',
            'attempt': attempt['value'],
            'thispage': this_page,
            'nextpage': next_page,
            'timeup': '0',
            'sesskey':sesskey,
            'scrollpos':scrollpos ,
            'slots': slots['value']
            }
        responce_answer=s2.post(form_answer['action'],headers=header,data=datas)
        F=file_record('MP_q1.txt',responce_answer.text)
        soup_attempt_answer=BeautifulSoup(responce_answer.text,'html.parser')
        form_answer=soup_attempt_answer.find('form',id='responseform')
    responce_beg_page=redirect_on_begin_page_attempt(s2,attempt['value'],cmid)

def type_check_beta(form,sequencecheck_name):
    ''''Проверка типа заполняемой формы'''
    q=sequencecheck_name.split(':')[0]
    types={'p':'select','answer':'input(text,radio)','sub':'ul,select','response':'сложить слово,переложить слова в нужном порядка',
    'choice':'checkbox'}           
    form_answer=list(filter(lambda x:x.get('name') is not None,form.find_all()))
    type_form=''
    for a in form_answer:       
        for b in types:
            if (set(q+b)<set(a['name'])):
                if a.name=='input': 
                    type_form=f'{a.name}_{b}_{a["type"]}'
                else:
                    type_form=f'{a.name}_{b}'
                break
    return type_form


def find_answer_text_checkbox(form_content,sequencecheck_name):
    '''Находит ответы в форме,если она состоит из checkbox'''
    answer_list=[]
    form_answer=form_content.find('div',class_='answer')
    answer_form=list(filter(lambda x:'correct' in x['class'],form_answer.find_all('div')))
    if len(answer_form)>0:
        for tag in answer_form:
            answer=tag.find_next().find_next().text
            if tag.name=='div':
                answer=' '.join(answer.split()[1:])
            answer_list.append(answer)
    return answer_list


def find_answer_text_radio(form_content,sequencecheck_name):
    '''Находит ответы в форме,если она состоит из radio'''
    answer=''
    form_answer=form_content.find('div',class_='answer')
    answer_form=list(filter(lambda x:'correct' in x['class'],form_answer.find_all('div')))
    if bool(answer_form):
        answer=answer_form[0].find_next().find_next().text
        if answer_form[0].name=='div':
            answer=' '.join(answer.split()[1:])
    #Данная часть алгоритма отвечает,за поиск ответов в окошке с правильным ответом,не всегда работает корректно,так как сплит производится по части,которая может быть в самом ответе
    else:
        form_answer=form_content.find('div',class_='outcome clearfix').find('div',class_='rightanswer')
        if bool(form_answer):
            answer=form_answer.text.split('ответ: ')[1]
    return answer


def find_answer_text(form_content):
    '''Находит ответы в форме,если она состоит из text'''
    form_answer=form_content.find('span',class_='answer').find_next()
    if 'correct' in form_answer['class']:
        return form_answer['value']
    else:
        form_answer=form_content.find('div',class_='outcome clearfix').find('div',class_='rightanswer')
        if bool(form_answer):
            return form_answer.text.split('ответ: ')[1]
    return None


def file_answer_scanner(file_path):
    ''''Берёт ответы на вопросы из файла'''
    all_type_dict={'select_p':{},'input_answer_text':{},'input_answer_radio':{},
    'sub_ul':{},'sub_select':{},'responce__ul':{},'input_choice_checkbox':{}}
    with open(file_path,'r',encoding='UTF-8') as F:
        soup_answer=BeautifulSoup(F.read(),'html.parser')
        #form_content=soup_answer_html_radio('div',class_='content')
        answer_forms=list(map(lambda x:x.find_previous(),soup_answer.find_all('div',class_='formulation clearfix')))
        sequencecheck=answer_forms[0].find('input')['name']
        for tag in answer_forms:
            tag_question_text=tag.find('div',class_='qtext').text
            type_tag=type_check_beta(tag,sequencecheck)
            if (type_tag=='input_answer_radio'):
                answer=find_answer_text_radio(tag,sequencecheck)
                if (bool(answer)):
                    all_type_dict[type_tag].setdefault(' '.join(tag_question_text.split()),[]).append(answer)
            if  (type_tag=='input_choice_checkbox'):
                answer=find_answer_text_checkbox(tag,sequencecheck)
                if (bool(answer)):
                    all_type_dict[type_tag].setdefault(' '.join(tag_question_text.split()),[]).extend(answer)
            if (type_tag=='input_answer_text'):
                answer=find_answer_text(tag)
                if (bool(answer)):
                    all_type_dict[type_tag].setdefault(' '.join(tag_question_text.split()),[]).append(answer)                     
    return all_type_dict


def redirect_on_begin_page_attempt(session,attempt,cmid):
    '''Перенаправление на первую страницу теста'''
    datas={
        'attempt':attempt,
        'cmid':cmid
    }
    url=f'https://online.mospolytech.ru//mod/quiz//attempt.php?attempt={attempt}&cmid={cmid}'
    responce=session.post(url,headers=header,data=datas)
    return responce
    
header={
        'User-Agent':'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36', 
    }
if '__main__'==__name__:
    '''Переход в директорию package,для успешного запуска файла в __main__'''
    os.chdir('..')

    ''''responce отвечает за получение logintoken'''

    s,responce,logintoken=find_logintoken()

    ''''responce2 отвечает за вход на сайт'''

    responce2,s2,all_courses=login_on_MP(responce,'','',logintoken)

    ''''Переход в необходимый курс'''

    test_names_and_links=cours_page_open(responce2,s2,all_courses,'Управление проектами')


    ''''Выбор необходимого теста и переход на страницу с ним'''

    responce4=test_page_open('Тест по теме 3 Бизнес - планирование в управление проектами',test_names_and_links,s2)

    ''''Переход на страницу попытки'''

    responce5,sesskey=attempt_page_open(responce4,s2)


    '''Проход по страничкам теста и ответы на вопросы'''

    answer_on_questions(responce5,sesskey,r'package\тесты\Тест по теме 3 Бизнес - планирование.html',s2)




