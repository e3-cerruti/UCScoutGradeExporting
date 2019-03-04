import csv
import logging
import ttk
from Tkinter import *

import preferences
from canvasapi import Canvas

# Canvas API URL
from canvasapi.exceptions import ResourceDoesNotExist, InvalidAccessToken
from templates import Templates, TemplateLoadForm, TemplateForm

# API_URL = "https://classroom.ucscout.org/"
# Canvas API key
# API_KEY = "4612~9PUiqObJcODLN2w29iPuQkoXULyj29BunIAW1gXuSYVnmRvpP4WPmTJlBkS8uVsH"


class App(ttk.Frame):
    def __init__(self, master):
        ttk.Frame.__init__(self, master)
        self.grid(column=0, row=0, sticky=(N, W, E, S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.selected_course = StringVar(self.master)

        self._setup_widgets()

    def _setup_widgets(self):
        self.pack(fill='both', expand=True)

        ttk.Label(self, text="Course").grid(row=0, column=0, sticky=W)
        course_menu = ttk.OptionMenu(self, self.selected_course, courses[0].name, *[x.name for x in courses])
        course_menu.grid(row=1, column=0, sticky='w')
        self.selected_course.trace("w", self.course_changed)

        self.assignment_tree = ttk.Treeview(self, columns=['Assignment'], selectmode='browse', show='headings')
        self.assignment_tree.grid(row=2, column=0, sticky='wens')
        self.assignment_tree.pack(fill='x')
        self.load_assignment_tree()

        ttk.Button(self, text="Create Files", command=generate_grade_files).grid(row=3, column=0, sticky="w")
        for child in self.winfo_children(): child.grid_configure(padx=1, pady=1)

    def course_changed(self, *args):
        if self.selected_course.get():
            self.load_assignment_tree()

    def load_assignment_tree(self):
        for children in self.assignment_tree.get_children():
            self.assignment_tree.delete(children)

        current_course = self.get_course()
        assignments = current_course.get_assignments()
        for item in assignments:
            self.assignment_tree.insert('', 'end', text=item.name, values=[item.name])

        items = self.assignment_tree.get_children()
        if len(items) > 0:
            self.assignment_tree.selection_set(items[0])

    def load_template(self):
        templates = TemplateLoadForm(root)

    def get_course(self):
        selected_course_name = self.selected_course.get()
        return next((x for x in courses if x.name == selected_course_name), None)

    def get_assignment(self):
        items = self.assignment_tree.selection()
        if len(items) == 1:
            assignment_name = self.assignment_tree.item(items[0], option='text')
            assignments = self.get_course().get_assignments()
            return next((x for x in assignments if x.name == assignment_name), None)


def generate_grade_files():
    course = app.get_course()
    assignment = app.get_assignment()

    header = [['Assignment Name:', assignment.name], ['Due Date:', assignment.due_at],
              ['Points Possible:', assignment.points_possible], ['Extra Points:', '0'], ['Score Type:', 'POINTS'],
              ['Student Num', 'Student Name', 'Score']]

    entries = {}
    for column in course.get_custom_columns():
        if column.title == 'Notes':
            entries = {entry.user_id: entry.content for entry in column.get_entries(course)}

    if not entries:
        logging.warning("No scholar ids found in "+course.name)
        return

    grades = {}
    ids = []
    for submission in assignment.get_submissions():
        grade = submission.attributes['grade']
        grades[entries[submission.user_id]] = {'Name:': course.get_user(submission.user_id).name, 'Grade:': grade}
        ids.append(entries[submission.user_id])

    for label, template in Templates().templates.iteritems():
        if [value for value in Templates().get_ids(template) if value in ids]:
            filename = template['Class:'] + '_'  +label
            with open(filename+'.csv', 'w') as pstfile:
                writer = csv.writer(pstfile, quoting=csv.QUOTE_MINIMAL)

                writer.writerow(['Teacher Name:', template['Teacher Name:']])
                writer.writerow(['Class:', template['Class:']])

                for row in header:
                    writer.writerow(row)
                for row in template['Scholars']:
                    if row[0] in grades.keys():
                        writer.writerow([row[0], row[1], grades[row[0]]['Grade:']])
                    else:
                        writer.writerow([row[0], row[1], None])


def close_app():
    exit(0)

def get_account():
    global api_key
    canvas = Canvas(preferences.API_URL, api_key)
    canvas_account = None
    while not canvas_account:
        try:
            canvas_account = canvas.get_current_user()
        except (ResourceDoesNotExist, InvalidAccessToken, ValueError) as error:
            dialog = preferences.TokenDialog("Current token is expired or invalid. Please enter new token.")
            api_key = dialog.get_token()
            canvas = Canvas(preferences.API_URL, api_key)

    return canvas_account


# Load templates from files
Templates()

api_key = preferences.load_api_key()

if not api_key:
    sys.exit('No usable API KEY for UC Scout.')

account = get_account()
courses = account.get_courses()

root = Tk()

root.title("UC Scout Grader Exporter")

note = ttk.Notebook(root)

courses_tab = Frame(note)
templates_tab = Frame(note)
note.add(courses_tab, text="Courses")

note.add(templates_tab, text="Templates")
template_form = TemplateForm(templates_tab)
app = App(courses_tab)

note.pack()
root.mainloop()
exit()

root.mainloop()
