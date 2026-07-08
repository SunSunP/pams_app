import os
from pams_app.gui_app import PamsApp
from pams_app.database import DB_PATH


def main():
    if not os.path.exists(DB_PATH):
        print("No database found - run 'python3 seed_data.py' first to create one.")
        return
    app = PamsApp()
    app.mainloop()


if __name__ == "__main__":
    main()
