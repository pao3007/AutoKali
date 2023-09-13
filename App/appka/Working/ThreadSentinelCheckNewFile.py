from PyQt5.QtCore import QThread, pyqtSignal
from os import listdir as os_listdir


class ThreadSentinelCheckNewFile(QThread):
    finished_signal = pyqtSignal()

    def __init__(self, folder_opt_export):
        super().__init__()
        self.opt_sentinel_file_name = None
        self.folder_opt_export = folder_opt_export
        self.termination = False

    def run(self):
        self.check_new_files()

    def check_new_files(self):
        print("---->START CHECKING FILE")
        # Get the initial set of files in the folder
        initial_files = set(os_listdir(self.folder_opt_export))

        while not self.termination:
            # Get the current set of files in the folder
            current_files = set(os_listdir(self.folder_opt_export))

            # Find the difference between the current and initial files
            new_files = current_files - initial_files

            if new_files:
                for file in new_files:
                    self.opt_sentinel_file_name = file
                return
            self.msleep(33)
