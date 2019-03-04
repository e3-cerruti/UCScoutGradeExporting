import logging
import ttk as ttk
from Tkinter import Tk, Toplevel, StringVar, NORMAL, DISABLED

from canvasapi import Canvas
from canvasapi.exceptions import InvalidAccessToken, ResourceDoesNotExist

API_URL = "https://classroom.ucscout.org/"
api_key = None


# def __init__(self):
# Register default preferences
# self.defaults = NSUserDefaults.standardUserDefaults()

# NSDictionary * appDefaults = [NSDictionary
#                               dictionaryWithObject:[NSNumber numberWithBool:YES] forKey:
#
# @
#
#
# "CacheDataAgressively"];
# standardUserDefaults.registerDefaults_(app_defaults)

def load_api_key():
    global api_key
    # Attempt to obtain password. Short circuit evaluation at the first
    # sign of success.
    api_key = (
            api_key or
            _load_api_key_from_keyring() or
            _load_api_key_from_file() or
            _prompt_for_api_key()
    )
    return api_key


def _load_api_key_from_keyring():
    """
    Attempt to load API key from keyring. Suppress Exceptions.
    """
    try:
        keyring = __import__('keyring')
        getpass = __import__('getpass')
        return keyring.get_password(API_URL, getpass.getuser())
    except Exception:
        logging.warning("Error loading token from keyring", exc_info=1)


def _load_api_key_from_file():
    """
    Attempt to load API key from a file. Suppress Exceptions.

    This is bad because the key is stored in plain text but it may be required if I can't sign the executable.
    """
    try:
        path = home().joinpath('.token')

        with path.open("r") as token_file:
            token = token_file.readline()
        return token
    except Exception:
        logging.warning("Error loading token from file", exc_info=1)


def _prompt_for_api_key():
    """
    Prompt for a API key. Suppress Exceptions.
    """
    try:
        dialog = TokenDialog()
        token = dialog.get_token()
        return token
    except Exception:
        pass


def save_token(token):
    return (
            _save_api_key_to_keyring(token) or
            _save_api_key_to_file(token)
    )


def _save_api_key_to_keyring(token):
    """
    Attempt to save API key to keyring. Suppress Exceptions.
    """
    try:
        keyring = __import__('keyring')
        getpass = __import__('getpass')
        return keyring.set_password(API_URL, getpass.getuser(), token)
    except Exception as error:
        logging.warning("Error saving token to keyring", exc_info=1)


def _save_api_key_to_file(token):
    """
    Attempt to save API key to a file. Suppress Exceptions.

    This is bad because the key is stored in plain text but it may be required if I can't sign the executable.
    """
    try:
        path = home().joinpath('.token')

        with path.open("w") as token_file:
            token = token_file.write(unicode(token))
        return token
    except Exception as error:
        logging.warning("Error saving token to file", exc_info=1)


def home():
    path_lib = __import__('pathlib2')
    directory = path_lib.Path.home().joinpath('.ucscoutexport')

    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)

    return directory


class TokenDialog:
    def __init__(self, error_message=None):
        self.token = None
        root = self.root = Tk()
        self.error_message = StringVar(root)

        root.title("UC Scout Token")
        root.bind('<Return>', self.ok)

        frame = ttk.Frame(root)
        frame.grid(column=0, row=0, sticky=('n', 'e', 's', 'w'))

        message = 'A UC Scout token is required to access grades from UC Scout. Please consult the documentation for ' \
                  'instructions on creating a token. '
        ttk.Label(frame, text=message, wraplength=400).grid(row=0, column=0)

        vcmd = (frame.register(self.validate), '%P', '%W')
        self.e = ttk.Entry(frame, show="*", width=45, validate='key', validatecommand=vcmd)
        self.e.grid(row=1, column=0, padx=5)
        self.e.focus_set()

        self.error_label = ttk.Label(frame, textvariable=self.error_message, wraplength=400, foreground='red')
        self.error_label.grid(row=2, column=0)
        if error_message:
            self.error_message.set(error_message)
        else:
            self.error_label.grid_forget()

        self.ok_button = ttk.Button(frame, text="OK", command=self.ok, state=DISABLED)
        self.ok_button.grid(row=3, column=0, pady=5)

    def get_token(self):
        self.root.mainloop()
        return self.token

    def ok(self, _event=None):
        self.token = self.e.get()

        if not self.token:
            self.display_error('Please enter a token from UC Scout.')
            return

        canvas = Canvas(API_URL, self.token)

        try:
            canvas.get_current_user()
        except (ResourceDoesNotExist, InvalidAccessToken, ValueError) as error:
            self.display_error(str(error))
            return

        save_token(self.token)
        self.root.destroy()

    def validate(self, p, w):
        self.ok_button.config(state=(NORMAL if p else DISABLED))
        return True

    def display_error(self, message):
        self.e.config(text='')
        self.e.update()
        self.error_message.set(message)
        self.error_label.grid(row=2, column=0)


if __name__ == '__main__':

    print(home())
    d = TokenDialog()
    print(d.get_token())
