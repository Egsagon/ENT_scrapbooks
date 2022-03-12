# ENT_API_SCRAPBOOKS
> This python API provides a bunch of functions centerd around the Scrapbook application f the [ENT iledefrance](https://ent.iledefrance.fr).

## Requirements
- json
- requests (2.27.1)

## Usage
THis API consists of a main class `Connection()` that you need to initialize to use.

### Connection
It is possible to connect by passing your username and password as parameters or by passing through the ENT payload.

```json
{"email": "name.lastname", "password": "1234"}
 ```
 
 ```python
 from ENT_API import Connection # import the module
 
 client = Connection(usr='last.lastname', pwd='1234') # initialize the connection
 ```
 or
 ```python
 client = Connection(payload=my_payload)
 ```
 You must also call the ```login()``` function before using any other function.
 ```python
 client.login()
 ```
The function will raise ```ConnectionError()``` from the *Errors*.py module if it ails to connect.
 ### ScrapBooks Managment
 The API includes multiple functions to manage scrapbooks.
 The ENT ScrapBooks are recognized using an id.
 ```python
 getInfosOnBook(id) # get the presentation of a book

 getBooks() # get all the books you have

 createBook(title, subtitle, color) # create a new book

 duplicateBook(id) # duplicate a book

 renameBook(id, title, subtitle, color) # rename a book

 trashBook(id) # move a book to trash

 deleteBook(id) # delete the book (must have been trashed before)
 ```
 ### Folder Managment
 The API also includes a folder managment functions:
 ```python
 getFolderList() # returns a list of folders

 getFolderInfos(id) # returns infos on a folder
 
 createFolder(title, parent) # creates a new folder (the main parent is 'root')

 setInFolder(id, folderId) # moves a book to a folder
 ```
 ### Utilities
 API also includes utilities function:
```python
fetchStudents(classId) # returns a list of students given a group

getBookIdByTitle(title) # returns the id a book given its title (may panic if there are multiple books with the same title)
 ```