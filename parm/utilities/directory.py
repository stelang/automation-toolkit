from os import getcwd
from os.path import join, abspath, dirname, realpath, split, basename, normpath
        
def get_parm_file(postfix_dir):
    
    dir_list = split_dir(postfix_dir)
    
    return join(getcwd(), *dir_list)
    
def get_conf_file(postfix_dir):
    
    dir_list = split_dir(postfix_dir)
    
    return realpath(join(dirname(__file__), *dir_list))

def split_dir(path):
    dirs = []
    
    while 1:
        path, dir = split(path)

        if dir != "":
            dirs.append(dir)
        else:
            if path != "":
                dirs.append(path)

            break
    
    dirs.reverse()
    
    return dirs
    
def get_last_directory(file):
    return basename(normpath(file))