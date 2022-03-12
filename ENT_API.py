import json, requests, Errors
from copy import copy

class Connection:
    def __init__(self, usr: str = None, pwd: str = None, payload: dict = None, session: requests.Session = None) -> None:
        """
        Represents an instance of a connection with the ENT.
        """

        # Error protection
        #if not((usr is None or pwd is None) or (payload['email'] + payload['password'])): raise Errors.PayloadError('Invalid credentials.')

        # Save payload
        self.payload = {'email': usr, 'password': pwd} if payload is None else payload
        self.payload['callBack'] = 'https%3A%2F%2Fent.iledefrance.fr%2Ftimeline%2Ftimeline'
        
        # Save session
        self.session = requests.Session() if session is None else session

        # Utilities
        self.logged = False
        self.initAuth: requests.Response = None
        self.initCookies: requests.Response.cookies = None

        # XSRF token
        self.xsrf: str = None
        self.xsrf_headers = {"accept": "application/json, text/plain, */*","accept-language": "fr","content-type": "application/json;charset=UTF-8","sec-fetch-dest": "empty","sec-fetch-mode": "cors","sec-fetch-site": "same-origin","sec-gpc": "1"}
    
    def post(self, type: str = None, url: str = None, req: dict = None) -> requests.Response:
        #TODO
        """
        Performs a raw post to ENT.
        """

        type = str(type).upper()

        url = 'https://ent.iledefrance.fr/' + url

        if req is None: req = {}
        req = json.dumps(req)

        # send
        res = self.session.request(
            method = type,
            url = url,
            data = req,
            headers = self.xsrf_headers,
        )

        # error protection
        if not res.ok: raise Errors.ConnectionError('Could not connect to ENT.')

        return res
    
    def login(self) -> None:
        """
        Attempts to connect using the given credentials.
        """

        # headers = {
        #     'connection': 'keep-alive',
        #     'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:73.0) Gecko/20100101 Firefox/73.0'
        # }

        # send the payload
        auth = self.session.post('https://ent.iledefrance.fr/auth/login', data = self.payload, ) # headers=headers
        #auth = self.post('post', 'auth/login', self.payload)

        if not auth.ok: raise Errors.ConnectionError('Failed to login.')

        self.initAuth = auth
        self.initCookies = auth.cookies
        self.logged = True

        self.xsrf = self.initCookies["XSRF-TOKEN"]
        self.xsrf_headers = {"accept": "application/json, text/plain, */*","accept-language": "fr","content-type": "application/json;charset=UTF-8","sec-fetch-dest": "empty","sec-fetch-mode": "cors","sec-fetch-site": "same-origin","sec-gpc": "1"}
        self.xsrf_headers["x-xsrf-token"] = self.xsrf
    
    def fetchStudents(self, classId: str = None) -> list:
        """
        Attempts to get the students on ENT.
        """

        # Error protection
        if classId is None: raise Errors.PayloadError('Invalid class Id.')

        # Post
        req = {
            "search": "",
            "types": ["User"],
            "structures": [],
            "classes": [classId],
            "profiles": [],
            "nbUsersInGroups": True,
            "functions": [],
            "mood": True
        }

        res = self.session.post("https://ent.iledefrance.fr/communication/visible", data = json.dumps(req), headers = self.xsrf_headers)
        #res = self.post('post', 'communication/visible', req)

        users = [user['displayName'] for user in res.json()['users'] if user['profile'] == 'Student']

        return users
    
    def getFolderList(self) -> list:
        """
        Returns a list of all the created folders.
        """

        res = self.session.get('https://ent.iledefrance.fr/scrapbook/folder/list/all', headers = self.xsrf_headers)
        #res = self.post('get', 'scrapbook/folder/list/all')


        return res.json()
    
    def getBooks(self) -> list:
        """
        Returns a list of all the created books on the root.
        """

        res = self.session.get('https://ent.iledefrance.fr/scrapbook/list/all', headers = self.xsrf_headers)
        #res = self.post('get', 'scrapbook/list/all')

        return res.json()
    
    def setInFolder(self, id: str, folder: str) -> None:
        """
        Attemps to move a book to a folder.
        """

        req = {"parentId": folder['parentId'], "ressourceIds": folder['ressourceIds'],  "title": folder['title']}
        req['ressourceIds'].append(id)

        # print('req is:', req)

        res = self.session.put(f'https://ent.iledefrance.fr/scrapbook/folder/{folder["_id"]}', data = json.dumps(req), headers = self.xsrf_headers)
        # res1 = self.session.put(f'https://ent.iledefrance.fr/scrapbook/folder/{folder["_id"]}', data = json.dumps(req), headers = self.xsrf_headers)

        return res.text #, res1.text
    
    def createBook(self, title, subtitle, color) -> str:
        """
        Creates a book and return its Id.
        """

        req = {
            'coverColor': color,
            'subTitle': subtitle,
            'title': title
        }

        res = self.session.post('https://ent.iledefrance.fr/scrapbook', data = json.dumps(req), headers = self.xsrf_headers)
        #res = self.post('post', 'scrapbook', req)

        return res.json()['_id']
    
    def createFolder(self, name: str, parent: str) -> str:
        """
        Creates a folder and returns its id.
        """

        req = {
            'parentId': parent,
            'ressourceIds': [],
            'title': name
        }

        res = self.session.post('https://ent.iledefrance.fr/scrapbook/folder', data = json.dumps(req), headers = self.xsrf_headers)
        #res = self.post('post', 'scrapbook/folder', req)

        return res.json()['_id']
    
    def duplicateBook(self, id: str) -> str:
        """
        Duplicates a book and returns the id of the duplicated one.
        """

        req = {"application": "scrapbook", "resourceId": id}

        res = self.session.post('https://ent.iledefrance.fr/archive/duplicate', data = json.dumps(req), headers = self.xsrf_headers)

        return res.json()['duplicateId']
    
    def renameBook(self, id: str, title: str = None, subtitle: str = None, color: str = None, _trash: int = 0) -> int:
        """
        Rename a book.
        """

        fixes_rm_keys = ['created', 'name', 'modified', '_id', 'nameSearch', 'owner']

        # fetch data
        bookData = self.getInfosOnBook(id)

        for i in range(3):
            keysPassed = []
            for key in fixes_rm_keys:
                re = bookData.pop(key, False)
                keysPassed.append(re)
            
            if all(keysPassed): break
            print('\033[94m' + f'Failed to get {id}, retrying... ({i+1})' + '\033[0m')
        
        if 0: print('\033[94mGot infos on book.\033[0m')

        req = bookData
        if title is not None: bookData['title'] = title
        if subtitle is not None: bookData['subTitle'] = subtitle
        if color is not None: bookData['coverColor'] = color

        res = self.session.put(f'https://ent.iledefrance.fr/scrapbook/{id}', data = json.dumps(req), headers = self.xsrf_headers)

        return res.json()['number']
    
    def renameBook2(self, id: str, title: str) -> None:
        """
        Attempts to rename a book.
        """

        book = self.getInfosOnBook(id)
        
        if not 'coverColor' in book.keys(): book['coverColor'] = 'purple'
        if not 'icon' in book.keys(): book['icon'] = ''
        if not 'pages' in book.keys(): book['pages'] = []
        if not 'subTitle' in book.keys(): book['subTitle'] = 'Automation by https://github.com/Egsagon'

        data = {
            'coverColor': book['coverColor'],
            'icon': book['icon'],
            'pages': book['pages'],
            'subTitle': book['subTitle'],
            'title': title,
            'trashed': book['trashed']
        }

        res = self.session.put(f'https://ent.iledefrance.fr/scrapbook/{id}', data = json.dumps(data), headers=self.xsrf_headers)

        if res.json()['number'] != 1: print('/!\\ ENT PUT REQUEST DIDNT RETURNED VALUE 1')
    
    def getInfosOnBook(self, id: str) -> dict:
        """
        Get the primary informations on a book.
        """

        for _ in range(3):
            res = self.session.get(f'https://ent.iledefrance.fr/scrapbook/get/{id}', headers=self.xsrf_headers)
            #res = self.post('get', f'scrapbook/get/{id}')

            try:
                if res.json() != {}: return res.json()
            
            except: print(f'/!\\ Failed to retreive data from book {id}, retrying...')
    
    def trashBook(self, id: str) -> None:
        """
        Place a book in the trash.
        """

        return self.renameBook(id, _trash = 1)
    
    def deleteBook(self, id: str) -> None:
        """
        Permanently delete a book.
        """

        self.session.delete(f'https://ent.iledefrance.fr/scrapbook/{id}', headers = self.xsrf_headers)

        return

    def getBookIdbyTitle(self, title: str) -> str:
        """
        Finds a book's id with his name.
        /!\ Multiple books with the same name pay create conflicts.
        """

        books = self.getBooks()
        
        for book in books:
            if book['title'] == title: return book['_id']
        return
    
    def getFolderInfos(self, id: str) -> dict:
        """
        Get informations on folder (needed to call setInFolder() function).
        """

        folders = self.getFolderList()

        for folder in folders:
            if folder['_id'] == id: return folder
        return

    def fetchGroupId(self, name: str, school: str = None) -> list:
        """
        Attempts to get a group Id from its name (and eventually its school).
        """

        # Post
        req = {
            "search": name,
            "types": ["Group"],
            "structures": [] if school is None else [school],
            "classes": [],
            "profiles": ["Student"],
            "functions": [],
            "nbUsersInGroups": True,
            "groupType": True
        }

        res = self.session.post("https://ent.iledefrance.fr/communication/visible", data = json.dumps(req), headers = self.xsrf_headers)

        groups = res.json()['groups']

        return [{'id': group['id'], 'name': group['name']} for group in groups]
    
    def fetchStudentsFromGroupId(self, id: str) -> list:
        """
        Get the list of students from the result of a ENT group request.
        """

        res = self.session.get(f'https://ent.iledefrance.fr/communication/visible/group/{id}', headers = self.xsrf_headers)

        return [stud['displayName'] for stud in res.json()['users']]

    def fetchSchools(self) -> list:
        """
        Attempts to get all the available user's schools.
        """

        res = self.session.get('https://ent.iledefrance.fr/userbook/structures', headers=self.xsrf_headers)

        return [{'name': school['name'], 'id': school['id']} for school in res.json()]
    
    def fetchSchoolGroups(self, schoolId: str) -> list:
        """
        Attempts to get all the available groups in a school.
        """

        res = self.session.get(f"https://ent.iledefrance.fr/userbook/search/criteria/{schoolId}/classes", headers = self.xsrf_headers)

        return [{'id': group['id'], 'name': group['label']} for group in res.json()['classes']]

if __name__ == '__main__':
    c = Connection('raphael.kern', '')
    c.login()
    s = c.fetchSchools()[1]['id']
    print(s)
    g = c.fetchSchoolGroups(s)
    print(g)