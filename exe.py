# TODO : fix arrays display

from gettext import translation
import os
import csv
import ENT_API
from time import sleep
from platform import system

translations = open('lang.csv', newline='')
lang = csv.reader(translations, delimiter=' 'n quotechar='|')
language: str = None

retries = 3  # max retries
client: ENT_API.Connection = None
clrCmd = 'cls' if system() == 'Windows' else 'clear'

def ask(string, condFn = lambda s: bool(s)) -> str:
    """
    Asks the user multiple times.
    """
    
    inp = input(string)

    while not condFn(inp):
        print('Sorry, incorrect input. Try again:')
        inp = input(string)
    
    return str(inp)

def dis(string) -> None:
    """
    Display message with a separator
    """

    os.system(clrCmd)

    cols = int(os.popen('stty size').read().split()[1])
    half = int(cols / 2) - int(len(string) / 2) - 2

    print('\033[92m' + '.' * cols)
    print('.' * half + ' ' + string + ' ' + '.' * half + ('.', '')[len(string)%2==0])
    print('.' * cols + '\033[0m')

def present(li, sep = '->') -> None:
    """
    Output a formated array.
    """

    TermWidth = int(os.popen('stty size').read().split()[0])
    curWidth = 0

    for i, el in enumerate(li):
        printing = f'{i} {sep} {el}'
        
        curWidth += len(printing) + 8

        if curWidth > TermWidth:
            curWidth = 0
            print('\n')
        
        print(printing, end = '\t')
    
    print('\n')


# ========== log into ENT ========== #
dis('Welcome')

isLoginDone = False
while not isLoginDone:
    try:
        usr = ask('Enter your username > ', lambda s: bool(s) and '.' in s)
        pwd = ask('Enter your password > ', lambda s: 1)

        client = ENT_API.Connection(payload = {'email': usr, 'password': pwd})
        client.login()
        isLoginDone = True

    except KeyboardInterrupt: exit('\n')
    except: print('Unable to connect to ENT.\nThis may be because of a wrong payload, or because the ENT is out of reach.\nPlease try again.')


# ========== Fetch the students ========== #
dis('Logged into ENT')

isFetchingDone = False
while not isFetchingDone:

    # get the school
    isSchoolDone = False
    while not isSchoolDone:
        try:
            AvSchools = client.fetchSchools()
            
            print('Please pick a school:')
            present(map(lambda e: e['name'], AvSchools))

            school = AvSchools[int(ask('Number > ', lambda s: s.isdigit() and int(s) <= len(AvSchools)))]

            isSchoolDone = True

        except KeyboardInterrupt: break
        except: print('Something went wrong in fetching school. Please try again.')

    # get the group
    isGroupsDone = False
    while not isGroupsDone:
        try:
            AvGroups = client.fetchSchoolGroups(school['id'])
            
            print('Please pick a group:')
            present(map(lambda e: e['name'], AvGroups))

            group = AvGroups[int(ask('Number > ', lambda s: s.isdigit() and int(s) <= len(AvGroups)))]

            isGroupsDone = True
        
        except KeyboardInterrupt: exit('\n')
        except: print('Something went wrong . Please try again.')

    # get the students
    try:
        students = client.fetchStudents(group['id'])

        if len(students) == 0: print('Sorry, you are not authorized to fetch those students. Please try again.')
        else: isFetchingDone = True
    
    except KeyboardInterrupt: exit('\n')
    except: print('Something went wrong. Please try again.')


# ====================================== #
# ========== Prepare the copy ========== #
# ====================================== #
dis('Got students')

# === Get book name === #
isNameReady = False
while not isNameReady:
    try:
        bookName = ask('Enter the exact name of the ScrapBook you want to copy > ', lambda s: bool(s))
        bookId = client.getBookIdbyTitle(bookName)
        bookId
        isNameReady = True

    except KeyboardInterrupt: exit('\n')
    except: print('Something went wrong. Please try again.')

# === Get the folder === #
print('The books are ready to be copied. They will be copied in a folder. If you want this folder to have a custom name, please enter it here, else just press enter.')
folderName = ask('Name (optional) > ', lambda s: bool(s))

if not folderName: folderName = f'{bookName}'

folderId = client.createFolder(folderName, 'root')
folderCl = client.getFolderInfos(folderId)


# ========================== #
# ========== Copy ========== #
# ========================== #
dis('Copying')

passed = False

for student in students:
    print(f'Copying book for {student}: ', end = '')

    for i in range(retries):

        try:
            curBookId = client.duplicateBook(bookId)
            client.renameBook2(curBookId, f'{student} book')
            client.setInFolder(curBookId, folderCl)
            passed = True
            break

        except KeyboardInterrupt:
            if ask('\nYou pressed Ctrl+c. Do you really want to quit? (yes, no) > ').lower() == 'yes': exit('\n')

        print('\033[93m/!\\' * i, end = '')
        sleep(1)
    
    # print(('\033[91m Failed', '\033[92mSuceeded')[passed] + f' to copy book for {student}' + '\033[0m\n')
    print(('\033[91m Failed', '\033[92mSuceeded')[passed], '\033[0m')


# =============================== #
# ========== That's it ========== #
# =============================== #
exit(f'Successfully copied {len(students)} books into folder "{folderName}".\nYou may need to reload the ENT before seeing it.')
