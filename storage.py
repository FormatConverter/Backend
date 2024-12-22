from threading import local

_thread_locals = local() # Thread local storage

def get_file_mapping():
    '''
    Get the file mapping dictionary from the thread local storage
    '''
    if not hasattr(_thread_locals, "file_mapping"):
        _thread_locals.file_mapping = {}
    return _thread_locals.file_mapping
