import shutil

def backup_db(file_name):
    log.info("Backing up Serato library file '%s' to '%s.bak'"
                    % (file_name, file_name))
    try:
        shutil.copy(file_name, "%s.bak" % file_name)
    except IOError, e:
        log.warn("Skipping back-up due to '%s'" % e)

