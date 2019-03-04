import tkFileDialog
import ttk
from Tkinter import *
import csv
import json

import preferences


class TemplateForm(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master, padding="3 3 12 12")
        self.grid(column=0, row=0, sticky=(N, W, E, S))
        self._seutp_widgets()

    def _seutp_widgets(self):
        self.pack(fill='both', expand=True)
        editor = TemplateEditor(self)
        TemplateLoadForm(self, editor)


class TemplateEditor(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master, padding="3 3 12 12")
        self.grid(column=0, row=0, sticky=(N, W, E, S))
        self.template_teacher = StringVar(self.master)
        self.template_class = StringVar(self.master)
        self.selected_template = None
        self._seutp_widgets()
        self._build_template_tree()

    def _seutp_widgets(self):
        template_frame = ttk.Frame(self)
        template_frame.grid(row=0, column=0)

        class_frame = ttk.Frame(self)
        class_frame.grid(row=0, column=1)

        self.template_tree = ttk.Treeview(columns='Label', show="headings", selectmode="browse")
        template_vsb = ttk.Scrollbar(orient="vertical", command=self.template_tree.yview)
        self.template_tree.configure(yscrollcommand=template_vsb.set)
        self.template_tree.grid(column=0, row=0, sticky='nsew', in_=template_frame)
        template_vsb.grid(column=1, row=0, sticky='ns', in_=template_frame)
        self.template_tree.bind("<<TreeviewSelect>>", self._select, "+")
        self.template_tree.heading('Label', text='Label')

        ttk.Label(class_frame, text="Teacher").grid(row=0, column=2, sticky=W)
        ttk.Entry(class_frame, name='template_teacher', textvariable=self.template_teacher, width=45).grid(row=0, column=3)

        ttk.Label(class_frame, text="Class").grid(row=1, column=2, sticky=W)
        ttk.Entry(class_frame, name='template_class', textvariable=self.template_class, width=45).grid(row=1, column=3)

        self.scholar_tree = ttk.Treeview(columns=('ID', 'Scholar'), show="headings")
        scholar_vsb = ttk.Scrollbar(orient="vertical", command=self.scholar_tree.yview)
        self.scholar_tree.configure(yscrollcommand=scholar_vsb.set)
        self.scholar_tree.grid(column=3, row=2, sticky='nsew', in_=class_frame)
        scholar_vsb.grid(column=4, row=2, sticky='ns', in_=class_frame)
        self.scholar_tree.heading('ID', text='ID')
        self.scholar_tree.heading('Scholar', text='Scholar')

    def _build_template_tree(self):
        for item in Templates().templates.keys():
            self.template_tree.insert('', 'end', text=item, value=[item])
        items = self.template_tree.get_children()
        if len(items) > 0:
            self.template_tree.selection_set(items[0])

    def _build_scholar_tree(self):
        for children in self.scholar_tree.get_children():
            self.scholar_tree.delete(children)

        if self.selected:
            template = Templates().templates[self.selected]

            self.template_teacher.set(template['Teacher Name:'])
            self.template_class.set(template['Class:'])

            for scholar in template['Scholars']:
                self.scholar_tree.insert('', 'end', value=scholar)

    def _select(self, event=None):
        items = self.template_tree.selection()
        if len(items) == 1:
            self.selected = self.template_tree.item(items[0], 'text')
            self._build_scholar_tree()

    def add_template(self, label):
        item = self.template_tree.insert('', 'end', text=label, values=label)
        self.template_tree.selection_set(item)


class TemplateLoadForm(ttk.Frame):
    def __init__(self, master, editor):
        ttk.Frame.__init__(self, master, padding="3 3 12 12", relief="sunken", borderwidth=2)
        self.editor = editor
        self.grid(column=0, row=1, sticky=(N, W, E, S))
        self.template_label = StringVar(self.master)
        self.template_file = StringVar(self.master)
        self._setup_widgets()

    def _setup_widgets(self):
        vcmd = (self.register(self.validate), '%P', '%W')
        ttk.Label(self, text="Label").grid(row=0, column=0, sticky=W)
        ttk.Entry(self, name='template_label', textvariable=self.template_label, validate='key',
              validatecommand=vcmd).grid(row=0, column=1, sticky=W)

        ttk.Label(self, text="File").grid(row=1, column=0, sticky=W)
        ttk.Entry(self, name='template_file', textvariable=self.template_file, validate='key',
              validatecommand=vcmd, width=45).grid(row=1, column=1, sticky=W)

        ttk.Button(self, text="Find File...", command=self.select_template_file).grid(row=1, column=3)

        self.load_button = ttk.Button(self, text="Load", state=DISABLED, command=self.load_template)
        self.load_button.grid(row=2, column=3, sticky=W)

    def select_template_file(self):
        self.template_file.set(tkFileDialog.askopenfilename(initialdir="~/Downloads", title="Select template file",
                                                            filetypes=(("CSV files", "*.csv"), ("all files", "*.*"))))
        filename = self.template_file.get()
        label = self.template_label.get()
        self.load_button.config(state=(NORMAL if filename and label else DISABLED))

    def validate(self, p, w):
        filename = self.template_file.get()
        label = self.template_label.get()
        if 'file' in w:
            filename = p
        else:
            label = p

        if self.load_button:
            self.load_button.config(state=(NORMAL if filename and label else DISABLED))
        return True

    def load_template(self):
        Templates().load_template(self.template_label.get(), self.template_file.get())
        self.editor.add_template(self.template_label.get())
        self.template_file.set('')
        self.template_label.set('')
        self.update()


class Templates:
    class __impl:
        def __init__(self):
            self.templates = {}
            self.template_file = preferences.home().joinpath('templates')

            self.load_templates()

        @property
        def templates(self):
            return self.__templates

        @templates.setter
        def templates(self, templates):
            self.__templates = templates

        def load_templates(self):
            if not self.template_file.is_file():
                self.save_templates()

            with self.template_file.open("r", encoding="utf-8") as tfile:
                self.templates = json.load(tfile)

        def save_templates(self):
            with self.template_file.open('w', encoding="utf-8") as tfile:
                tfile.write(unicode(json.dumps(self.templates, ensure_ascii=False)))

        def load_template(self, label, filename):
            template = {}
            with open(filename, 'rb') as csvfile:
                csv_reader = csv.reader(csvfile)

                for i in range(2):
                    row = csv_reader.next()
                    template[row[0]] = row[1]

                for i in range(6):
                    csv_reader.next()

                template['Scholars'] = []
                for row in csv_reader:
                    template['Scholars'].append([row[0], row[1]])

            self.templates[label] = template
            self.save_templates()

        def delete_template(self, label):
            self.templates.remove(label)

        def rename_template(self, label, new_label):
            self.templates[new_label] = self.templates[label]
            self.templates.remove(self.templates[label])

        def get_ids_for_label(self, label):
            return self.get_ids(self.templates[label])

        def get_ids(self, template):
            return [x[0] for x in template['Scholars']]

    # storage for the instance reference
    __instance = None

    def __init__(self):
        """ Create singleton instance """
        # Check whether we already have an instance
        if Templates.__instance is None:
            # Create and remember instance
            Templates.__instance = Templates.__impl()

        # Store instance reference as the only member in the handle
        self.__dict__['_Singleton__instance'] = Templates.__instance

    def __getattr__(self, attr):
        """ Delegate access to implementation """
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        """ Delegate access to implementation """
        return setattr(self.__instance, attr, value)
