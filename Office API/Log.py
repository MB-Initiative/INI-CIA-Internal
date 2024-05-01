import logging
import os

class Log:
    
    def __init__(self, log_file_name = 'logger.txt', log_append = True):
        
        if not log_file_name:
            log_file_name = 'logger.txt'
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s|%(name)s|%(filename)s|%(levelname)s|%(lineno)d|%(message)s')
#         |%(name)s|%(filename)s

        if not log_append:
            try:
                os.remove(log_file_name)
            except:
                pass
        file_handler = logging.FileHandler(log_file_name)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.INFO)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(stream_handler)
        