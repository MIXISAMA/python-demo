'''
This .py file is the program entry.
What the program can do?
    1. CURD all restaurants information.
    2. It supports regular expressions queries.
    3. Custom database URI.
    4. Custom location by latitude and longitude coordinates.
    5. The list is automatically sorted by distance.
    6. Import restaurants information from .json file.

What are the advantages?
    1. Fast.
        Optimized database query.
        Components update locally.
    2. User-friendly.
        Easier search.
        Automatically save after editing.
        Progress bar for long time operation.

How to run it in terminal?
    $ mongod    # Start service
    $ python3 gui.py

Dependency packages:
    MongoDB 4.x
    python 3.x
    pip install tkinter
    pip install pymongo

gui.py is only responsible for rendering the data onto the view.
controller.py is only responsible for interacting with the database.
gui.py is similar to the frontend.
controller.py is similar to the backend.
All most data save in controller.py.
If you want to see data interface, you can read controller.py doc at first.

This .py file has 3 class, they are Application, LoginGui, ProgressBarGui.
They all inherit tk.Frame, This way they can be used as the root of a window.

In the following example, the program will create a new window,
and LoginGui will be the root frame of the window.

    LoginGui(tk.Tk(), my_controller)

Each class is roughly divided into two parts,
they are created methods and updated methods.

Created methods are only called when the class is instantiated.
So they will only be called once.

Updated methods are event driven, such as called after a button is clicked.
So they will be called multiple times.


'''
import time
import threading

import tkinter as tk
from tkinter import messagebox as msgbox
from tkinter import ttk
from tkinter import filedialog

from controller import Controller

class Application(tk.Frame):
    '''
    Class Application is the main window.
    '''

    def __init__(self, master, controller):
        master.geometry("+300+200")
        master.title(
            "Humanity\'s most fundamental relationship is with what we eat."
        )
        master.resizable(False, False)
        self.controller = controller
        self.master = master
        super().__init__(master)
        self.pack(padx=5, pady=5)
        self.create_gui()
        self.controller.update_rstrts({})
        self.update_rstrts_list_gui()

    def create_gui(self):
        '''
        The root frame is divided into three parts: left, middle and right.
        +------+------+------+
        |      |      |      |
        | fm_1 | fm_2 | fm_3 |
        |      |      |      |
        +------+------+------+

        The left part is divided into two parts: search gui, operation gui.
        +---------------+
        | search gui    |
        +---------------+
        | operation gui |
        +---------------+

        The middle part is restaurants list gui

        The right part is divided into three parts.
        +----------------+
        | basic info gui |
        +----------------+
        | address gui    |
        +----------------+
        | grades gui     |
        +----------------+

        Merge above.
        +-----------+------------------+------------+
        | search    |                  | basic info |
        +-----------+                  +------------+
        | operation | restaurants list | address    |
        +-----------+                  +------------+
        |           |                  | grades     |
        +-----------+------------------+------------+
        '''

        fm_1 = tk.Frame(self)
        fm_1.grid(row=0, column=0, stick=tk.NS)

        self.search_fm = tk.LabelFrame(fm_1, text="search")
        self.search_fm.pack(fill=tk.BOTH, padx=2)
        self.create_search_gui()

        self.operation_fm = tk.LabelFrame(fm_1, text="operation")
        self.operation_fm.pack(fill=tk.BOTH, padx=2)
        self.create_operation_gui()

        self.rstrts_list_fm = tk.LabelFrame(self, text="restaurants list")
        self.rstrts_list_fm.grid(row=0, column=1, sticky=tk.NSEW, padx=2)
        self.create_rstrts_list_gui()

        fm_3 = tk.Frame(self)
        fm_3.grid(row=0, column=2, stick=tk.NSEW)

        self.rstrt_info_fm = tk.LabelFrame(
            fm_3, width=500, height=138, text="basic info")
        self.rstrt_info_fm.grid(row=0, column=0, sticky=tk.NSEW, padx=2)
        self.rstrt_info_fm.grid_propagate(False)
        self.create_rstrt_info_gui()

        self.rstrt_address_fm = tk.LabelFrame(
            fm_3, width=500, height=139, text="address")
        self.rstrt_address_fm.grid(row=1, column=0, sticky=tk.NSEW, padx=2)
        self.rstrt_address_fm.grid_propagate(False)
        self.create_rstrt_address_gui()

        self.rstrt_grades_fm = tk.LabelFrame(fm_3, width=500, text="grades")
        self.rstrt_grades_fm.grid(row=2, column=0, sticky=tk.NSEW, padx=2)
        self.create_rstrt_grades_gui()

    def create_search_gui(self):
        '''
        There are four search terms: Name, Borough, Street, Zipcode.
        Search results are their intersection.
        '''
        master = self.search_fm

        label_names = ["Name", "Borough", "Street", "Zipcode"]
        for row, name in enumerate(label_names):
            tk.Label(master, text=name).grid(row=row, column=0)

        self.search_views_list = list()
        for i in range(4):
            ety = tk.Entry(master, width=13)
            ety.grid(row=i, column=1, sticky=tk.EW)
            ety.bind("<Return>", self.search)
            self.search_views_list.append(ety)

        btns_fm = tk.Frame(master)
        btns_fm.grid(row=4, column=0, columnspan=2)

        clear_btn = tk.Button(
            btns_fm, text="clear", command=self.clear_search
        )
        clear_btn.grid(row=0, column=0)

        search_btn = tk.Button(btns_fm, text="search", command=self.search)
        search_btn.grid(row=0, column=1)

    def create_operation_gui(self):
        '''
        There are four buttons.
        new restaurant: Create a piece of new restaurant info.
        import .json: Import restaurant info from .json file.
        delete selected: Delete a piece of restaurant info.
        delete all: Delete all restaurant info where in list gui.
        '''
        master = self.operation_fm

        tk.Button(
            master, text="new restaurant", command=self.new_rstrt
        ).pack(fill=tk.X)

        tk.Button(
            master, text="import .json", command=self.import_rstrt
        ).pack(fill=tk.X)

        tk.Frame(master, height=10).pack() # blank block

        tk.Button(
            master, text="delete selected", command=self.del_rstrt
        ).pack(fill=tk.X)

        tk.Button(
            master, text="delete all", command=self.del_all_rstrts
        ).pack(fill=tk.X)

    def create_rstrts_list_gui(self):
        '''
        Create restaurants list gui.
        There is only a Treeview in this frame.
        +----------+------------+
        | distance | restaurant |
        +----------+------------+
        | ...      | ...        |
        | ...      | ...        |
        |          |            |
        '''
        master = self.rstrts_list_fm

        tree = ttk.Treeview(
            master, height=30, columns=list(range(2)), show="headings"
        )
        self.rstrts_list_tree = tree

        tree.column(0, width=100, anchor='center')
        tree.column(1, width=300, anchor='center')

        tree.heading(0, text='distance')
        tree.heading(1, text='restaurant')

        tree.bind("<ButtonRelease-1>", self.update_cur_rstrt)

        vbar = ttk.Scrollbar(master, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=vbar.set)
        tree.grid(row=0, column=0, sticky=tk.NSEW, pady=2)
        vbar.grid(row=0, column=1, sticky=tk.NS)

    def create_rstrt_info_gui(self):
        '''
        Create restaurant basic info gui.
        Auto save when press enter or control loses focus.
        '''
        master = self.rstrt_info_fm
        self.rstrt_info_views = list()

        texts = ["id:", "name:", "cuisine:", "borough:"]
        for text in texts:
            self.rstrt_info_views.append(tk.Label(master, text=text))
            ety = tk.Entry(master, width=48)
            ety.bind("<FocusOut>", self.edit_rstrt_info)
            ety.bind("<Return>", self.edit_rstrt_info)
            self.rstrt_info_views.append(ety)

    def create_rstrt_address_gui(self):
        '''
        Create restaurant address gui.
        Auto save when press enter or control loses focus.
        '''

        master = self.rstrt_address_fm
        self.rstrt_address_views = list()
        texts = ["building:", "street:", "zipcode:", "coord:"]
        for text in texts:
            self.rstrt_address_views.append(tk.Label(master, text=text))
            ety = tk.Entry(master, width=48)
            ety.bind("<FocusOut>", self.edit_rstrt_address)
            ety.bind("<Return>", self.edit_rstrt_address)
            self.rstrt_address_views.append(ety)

        coord_fm = tk.Frame(master)
        self.rstrt_address_views[-1] = coord_fm
        for _ in range(2):
            ety = tk.Entry(coord_fm, width=23)
            ety.bind("<FocusOut>", self.edit_rstrt_coord)
            ety.bind("<Return>", self.edit_rstrt_coord)
            self.rstrt_address_views.append(ety)

        self._locked = False

    def create_rstrt_grades_gui(self):
        '''
        Create restaurants grades gui.
        There are a Treeview and two Buttons in this frame.
        +-------+-------+------+
        | grade | score | date |
        +-------+-------+------+
        | ...   | ...   | ...  |
        | ...   | ...   | ...  |
        +-------+-------+------+
               [ + ] [ - ]
        '''
        master = self.rstrt_grades_fm
        tree = ttk.Treeview(
            master, height=13, columns=list(range(3)), show="headings"
        )
        self.rstrt_grades_tree = tree

        tree.column(0, width=100, anchor='center')
        tree.column(1, width=100, anchor='center')
        tree.column(2, width=300, anchor='center')

        tree.heading(0, text='grade')
        tree.heading(1, text='score')
        tree.heading(2, text='date')

        vbar = ttk.Scrollbar(master, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=vbar.set)
        tree.grid(row=0, column=0, sticky=tk.NSEW, pady=2)
        vbar.grid(row=0, column=1, sticky=tk.NS)

        btn_fm = tk.Frame(master)
        btn_fm.grid(row=1, column=0, columnspan=2)

        tk.Button(
            btn_fm, text=" + ", command=self.add_grade
        ).grid(row=0, column=0)

        tk.Button(
            btn_fm, text=" - ", command=self.del_grade
        ).grid(row=0, column=1)

    ### Methods above are only called once.

    def update_cur_rstrt(self, event=None):
        '''
        The selected item in the restaurants list gui is the current
        restaurant. This function is to render current restaurant data
        to the right part of the main window.
        step 1: Get the selected item.
        step 2: Get data from DB.
        step 3: render data to gui.
        '''
        index = None
        if self.rstrts_list_tree.selection():
            index = self.rstrts_list_tree.index(
                self.rstrts_list_tree.selection()[0]
            )

        self.controller.update_cur_rstrt(index)

        self.update_rstrt_info_gui()
        self.update_rstrt_address_gui()
        self.update_rstrt_grades_gui()

    def update_rstrt_info_gui(self):
        '''
        Render restaurant basic info to gui.
        '''
        rstrt = self.controller.cur_rstrt
        if rstrt is None:
            self.forget_rstrt_info_gui()
        else:
            self.show_rstrt_info_gui()


    def show_rstrt_info_gui(self):
        '''
        Show all components in basic info gui.
        Insert data into entries.
        '''
        rstrt = self.controller.cur_rstrt
        views = self.rstrt_info_views
        for i in range(4):
            views[i*2].grid(row=i, column=0, sticky=tk.E)

        keys = ["restaurant_id", "name", "cuisine", "borough"]
        views[1].config(state=tk.NORMAL)
        for i, key in enumerate(keys):
            views[i*2+1].delete(0, tk.END)
            views[i*2+1].insert(0, rstrt[key])
            views[i*2+1].grid(row=i, column=1, sticky=tk.W)
        views[1].config(state=tk.DISABLED)

    def forget_rstrt_info_gui(self):
        '''
        Forget all components in basic info gui.
        Forget means hide, you can not see them, but they are still in memory.
        It is fast to show them again.
        '''
        for slave in self.rstrt_info_fm.grid_slaves():
            self.rstrt_info_views.append(slave)
            slave.grid_forget()


    def update_rstrt_address_gui(self):
        '''
        Render restaurant address data to gui.
        '''
        rstrt = self.controller.cur_rstrt
        if rstrt is None:
            self.forget_rstrt_address_gui()
        else:
            self.show_rstrt_address_gui()

    def show_rstrt_address_gui(self):
        '''
        Show all components in address gui.
        Insert data into entries.
        '''
        rstrt = self.controller.cur_rstrt
        views = self.rstrt_address_views

        for i in range(4):
            views[i*2].grid(row=i, column=0, sticky=tk.E)

        keys = ['building', 'street', 'zipcode']
        for i, key in enumerate(keys):
            views[i*2+1].delete(0, tk.END)
            views[i*2+1].insert(0, rstrt['address'][key])
            views[i*2+1].grid(row=i, column=1, sticky=tk.W)
        views[7].grid(row=3, column=1, sticky=tk.W)

        coord = rstrt['address']['coord']
        for i in range(2):
            views[i+8].delete(0, tk.END)
            if coord and coord[i]:
                views[i+8].insert(
                    0,
                    "%.9f%c"%(
                        abs(coord[i]),
                        (('E', 'N')[i], ('W', 'S')[i])[coord[i] < 0]
                    )
                )
            views[i+8].grid(row=0, column=i, sticky=tk.W)

    def forget_rstrt_address_gui(self):
        '''
        Forget all components in address gui.
        Forget means hide, you can not see them, but they are still in memory.
        It is fast to show them again.
        '''
        for slave in self.rstrt_address_fm.grid_slaves():
            self.rstrt_address_views.append(slave)
            slave.grid_forget()

    def update_rstrt_grades_gui(self):
        '''
        Render restaurant grades data to gui.
        '''
        tree = self.rstrt_grades_tree
        rstrt = self.controller.cur_rstrt

        for item in tree.get_children():
            tree.delete(item)

        if rstrt is None:
            return

        for grade in rstrt['grades']:
            time_array = time.localtime(int(grade['date'])/1000)
            format_time = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
            tree.insert(
                '', tk.END,
                values=(grade['grade'], grade['score'], format_time)
            )

    def update_rstrts_list_gui(self):
        '''
        1. Render restaurants list data to gui.
        2. Update current restaurant data.
            Generally, this data is empty,
            and then the related components are hidden.
        '''
        self.refresh_rstrts_list_gui()
        self.update_cur_rstrt()

    def refresh_rstrts_list_gui(self):
        '''
        Render restaurants list data to gui.
        '''
        tree = self.rstrts_list_tree
        rstrts = self.controller.filtered_rstrts

        for item in tree.get_children():
            tree.delete(item)

        for rstrt in rstrts:
            tree.insert(
                '', tk.END,
                values=("%.2fkm"%(rstrt['dist']), rstrt['name'])
            )

    def clear_search(self, event=None):
        '''
        This function will be called after clicking the "clear" button.
        This is a user-friendly design.
        After clicking the "clear" button, all search content will be cleared.
        No need to delete manually.
        '''
        views = self.search_views_list
        for view in views:
            view.delete(0, tk.END)

    def search(self, event=None):
        '''
        This function will be called after clicking the "search" button.
        Give the search content to controller.py to search and update the
        restaurants list data. Then render restaurants list data to gui.
        '''
        views = self.search_views_list
        keys = ['name', 'borough', 'street', 'zipcode']
        condition = dict()
        for i in range(4):
            condition[keys[i]] = views[i].get().strip()
        self.controller.update_rstrts(condition)
        self.update_rstrts_list_gui()

    def import_rstrt(self):
        '''
        This function will be called after clicking the "import .json" button.
        Start a thread to import the .json file into the database.
        The main thread is used to load the progress bar.
        Display all restaurant information in the database after import.
        '''
        files_names = filedialog.askopenfilenames(
            filetypes=[("json file", "*.json")]
        )
        if not files_names:
            return

        def run():
            self.controller.add_rstrts_from_json(files_names[0])
        self.controller.init_progress()
        threading.Thread(target=run).start()
        pbg = ProgressBarGui(tk.Toplevel())
        while True:
            time.sleep(0.1)
            state, rate = self.controller.progress
            if state:
                break
            pbg.update_gui(rate*0.9)
        pbg.update_gui(1)
        pbg.master.destroy()
        self.controller.update_rstrts({})
        self.update_rstrts_list_gui()

    def del_rstrt(self):
        '''
        It will be called after clicking the "delete selected" button.
        Delete the currently selected restaurant.
        Partial re-rendering by useing the Treeview.delete(item) method.
        '''
        if not self.rstrts_list_tree.selection():
            return
        self.controller.del_rstrt()
        self.rstrts_list_tree.delete(self.rstrts_list_tree.selection()[0])
        self.update_cur_rstrt()

    def new_rstrt(self):
        '''
        It will be called after clicking the "new restaurant" button.
        create a new empty restaurant.
        Partial re-rendering by useing the Treeview.insert(...) method.
        '''
        self.controller.new_rstrt()
        tree = self.rstrts_list_tree
        tree.insert('', 0, values=('99999.99km', 'untitled'))
        tree.selection_set(tree.get_children()[0])
        self.update_cur_rstrt()

    def del_all_rstrts(self):
        '''
        It will be called after clicking the "delete all" button.
        And it will give a message box to confirm.
        '''
        if not msgbox.askyesno(
                'Sure?', 'Do you want to delete all information'):
            return
        self.controller.del_all()
        self.update_rstrts_list_gui()

    def edit_rstrt_info(self, event=None):
        '''
        It will be called after press enter or control loses focus.
        '''
        views = self.rstrt_info_views

        keys = ["name", "cuisine", "borough"]
        docs = dict()
        for i in range(3):
            docs[keys[i]] = views[i*2+3].get()
        self.controller.edit_info(docs)
        tree = self.rstrts_list_tree
        item = tree.get_children()[self.controller.cur_index]
        tree.set(item, column=1, value=views[3].get())

    def edit_rstrt_address(self, event=None):
        '''
        It will be called after press enter or control loses focus.
        '''
        views = self.rstrt_address_views
        keys = ['building', 'street', 'zipcode']
        docs = dict()
        for i in range(3):
            docs[keys[i]] = views[i*2+1].get()
        self.controller.edit_address(docs)

    def edit_rstrt_coord(self, event=None):
        '''
        It will be called after press enter or control loses focus.
        And it will check the legality of data.
        '''
        if self._locked:
            return
        try:
            views = self.rstrt_address_views
            lng = views[8].get()
            lng_var = None
            if not lng == "":
                if lng[-1] == 'E' or lng[-1] == 'e':
                    lng_var = 1
                elif lng[-1] == 'W' or lng[-1] == 'w':
                    lng_var = -1
                else:
                    raise Exception(
                        "Last symbol should be E or W or e or w not "
                        + lng[-1]
                    )

                var = float(lng[:-1])
                if not 0 <= var <= 180:
                    raise Exception(
                        "Longitude can only be between 0 and 180 E/W"
                    )
                lng_var *= var

            lat = views[9].get()
            lat_var = None
            if not lat == "":
                if lat[-1] == 'N' or lat[-1] == 'n':
                    lat_var = 1
                elif lat[-1] == 'S' or lat[-1] == 's':
                    lat_var = -1
                else:
                    raise Exception(
                        "Last symbol should be S or N or s or n not "
                        + lng[-1]
                    )

                var = float(lat[:-1])
                if not 0 <= var <= 90:
                    raise Exception(
                        "Latitude can only be between 0 and 90 N/S"
                    )
                lat_var *= var
            self.controller.edit_coord(lng_var, lat_var)

            tree = self.rstrts_list_tree
            item = tree.get_children()[self.controller.cur_index]
            rstrt = self.controller.filtered_rstrts[self.controller.cur_index]
            tree.set(item, column=0, value="%.2fkm"%(rstrt['dist']))
        except Exception as e:
            self._locked = True
            msgbox.showerror('error', e)
            self._locked = False

    def add_grade(self):
        '''
        It will be called after clicking the " + " button.
        '''
        if self.controller.cur_rstrt is None:
            return
        AddGradeGui(self)
        self.update_rstrt_grades_gui()

    def del_grade(self):
        '''
        It will be called after clicking the " - " button.
        '''
        tree = self.rstrt_grades_tree
        if not tree.selection() or self.controller.cur_rstrt is None:
            return
        item = tree.selection()[0]
        index = tree.index(item)
        tree.delete(item)
        self.controller.del_grade(index)
        self.update_rstrt_grades_gui()










class AddGradeGui(tk.Frame):
    '''
    It is the add grade window.
    '''
    def __init__(self, father):
        self.master = tk.Toplevel(father.master)
        self.master.geometry("+600+400")
        self.master.title("Grade")
        super().__init__(self.master, width=100, height=50)
        self.controller = father.controller
        self.father = father
        self.pack()
        self.create_gui()

    def create_gui(self):
        '''
        Create gui.
        +------+-----------+
        |Grade:|           |
        +------+-----------+
        |Score:|           |
        +------+-----------+
                [ + ]
        '''
        master = self
        tk.Label(master, text="Grade:").grid(row=0, column=0)
        self.grade_ety = tk.Entry(master)
        self.grade_ety.grid(row=0, column=1)

        tk.Label(master, text="Score:").grid(row=1, column=0)
        self.score_ety = tk.Entry(master)
        self.score_ety.grid(row=1, column=1)

        tk.Button(
            master, text=" + ", command=self.add
        ).grid(row=2, column=0, columnspan=2)

    def add(self):
        '''
        It will be called after clicking the " + " button.
        '''
        grade = self.grade_ety.get()
        score = self.score_ety.get()
        self.controller.add_grade(grade, score)
        self.father.update_rstrt_grades_gui()
        self.master.destroy()








class LoginGui(tk.Frame):
    '''
    It is the first window of the program.
    It is used to set the database uri and your current location.
    '''

    def __init__(self, master, controller):
        master.geometry("+350+230")
        master.title("Connect to DB")
        master.attributes("-topmost", True)
        master.resizable(False, False)
        self.controller = controller
        self.master = master
        super().__init__(master, width=100, height=50)
        self.pack()
        self.create_gui()

    def create_gui(self):
        '''
        create gui.
        +-------------------+
        | Database          |
        |                   |
        +-------------------+
        | coord             |
        |                   |
        +-------------------+
         [Connect or Create]
        '''
        self.db_fm = tk.LabelFrame(self, text="Database")
        self.db_fm.pack(padx=10, pady=5)
        self.create_db_gui()

        self.coord_fm = tk.LabelFrame(self, text="coord")
        self.coord_fm.pack()
        self.create_coord_gui()

        tk.Button(
            self, text="Connect or Create", command=self.login
        ).pack(pady=8)

    def create_db_gui(self):
        '''
        Create database uri gui.
        +---------+----------------------------+
        | Client: | mongodb://localhost:27017/ |
        +---------+----------------------------+
        | DB name:| restaurants                |
        +---------+----------------------------+
        '''

        master = self.db_fm
        tk.Label(master, text="Client").grid(row=0, column=0, sticky=tk.E)
        self.ip_ety = tk.Entry(master, width=22)
        self.ip_ety.insert(0, "mongodb://localhost:27017/")
        self.ip_ety.grid(row=0, column=1)
        tk.Label(master, text="DB name").grid(row=1, column=0, sticky=tk.E)
        self.db_name_ety = tk.Entry(master, width=22)
        self.db_name_ety.insert(0, "restaurants")
        self.db_name_ety.grid(row=1, column=1)

    def create_coord_gui(self):
        '''
        Create current location coordinates gui.
        +---------+-------+
        | 73.9    | ○E ◎W |
        +---------+-------+
        | 40.9    | ◎N ○S |
        +---------+-------+
        New York by default.
        '''

        master = self.coord_fm
        self.lng_ety = tk.Entry(master)
        self.lng_ety.insert(0, "73.9")
        self.lng_ety.grid(row=0, column=0)

        self.lng_var = tk.IntVar()

        tk.Radiobutton(
            master, text="E", value=1, variable=self.lng_var
        ).grid(row=0, column=1)

        tk.Radiobutton(
            master, text="W", value=-1, variable=self.lng_var
        ).grid(row=0, column=2)

        self.lng_var.set(-1)

        self.lat_ety = tk.Entry(master)
        self.lat_ety.insert(0, "40.9")
        self.lat_ety.grid(row=1, column=0)

        self.lat_var = tk.IntVar()
        tk.Radiobutton(
            master, text="N", value=1, variable=self.lat_var
        ).grid(row=1, column=1)
        tk.Radiobutton(
            master, text="S", value=-1, variable=self.lat_var
        ).grid(row=1, column=2)
        self.lat_var.set(1)

    def login(self):
        '''
        It will be called after clicking the "Connect or Create" button.
        '''
        try:
            ip = self.ip_ety.get()
            db_name = self.db_name_ety.get()
            lng = float(self.lng_ety.get())*self.lng_var.get()
            lat = float(self.lat_ety.get())*self.lat_var.get()
            self.controller.cur_coord = (lng, lat)
            self.controller.connect(ip, db_name)
            self.master.destroy()
            Application(tk.Tk(), self.controller)
        except Exception as e:
            msgbox.showerror('error', e)






class ProgressBarGui(tk.Frame):
    '''
    Write this myself, because I did not see ttk.Progressbar then.
    Building wheels is bad. :(
    '''
    def __init__(self, master, title=''):
        super().__init__(master)
        master.geometry("+600+400")
        master.title(title)
        master.protocol("WM_DELETE_WINDOW", self.do_nothing)
        master.resizable(False, False)
        self.master = master
        self.pack()
        self.create_gui()
        self.last_width = 0

    def create_gui(self):
        '''
        create gui.
        +-------+
        |■■■■   |
        +-------+
        '''
        self.cv = tk.Canvas(self, width=110, height=30)
        self.cv.grid()

        self.outer_rec = self.cv.create_rectangle(5, 5, 105, 25, width=1)
        self.inner_rec = self.cv.create_rectangle(5, 5, 5, 25, fill="#4F4F4F")

    def update_gui(self, rate):
        now_width = int(rate*100)
        if now_width == self.last_width:
            return
        self.cv.coords(self.inner_rec, (5, 5, 5+now_width, 25))
        self.master.update()
        self.last_width = now_width

    def do_nothing(self):
        pass




def main():
    LoginGui(tk.Tk(), Controller())
    tk.mainloop()

if __name__ == '__main__':
    main()
