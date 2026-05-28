import math

class Book:
    def __init__(self,title,author,text,id):
        self.title=title
        self.author=author
        self.id=id
        self.text=text

class Pagination:
    def __init__(self,book,char_per_page=100):
        self.book=book
        self.char_per_page=char_per_page
        self.pages=[]
    def pagination(self):
        for i in range(0, math.ceil(len(self.book.text) / self.char_per_page)):
            self.pages.append(self.book.text[i*self.char_per_page:i*self.char_per_page+self.char_per_page])
        return self.pages
    def page(self,number):
        return self.pages[number]
    @property
    def number_of_pages(self):
        return len(self.pages)

class Reading:
    def __init__(self,pagination,current_page=0):
        self.pagination=pagination
        self.current_page=current_page
    def next_page(self):
        self.current_page=(self.current_page+1)%self.pagination.number_of_pages
    def prev_page(self):
        self.current_page =(self.current_page-1)%self.pagination.number_of_pages
    def display_page(self):
        return self.pagination.pages[self.current_page]









