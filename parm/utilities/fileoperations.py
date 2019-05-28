def write_file(dest, payload):
    
    try:
        with open(dest, 'w') as fh:
            fh.write(payload)
    except IOError as e:
        print("File writing error")