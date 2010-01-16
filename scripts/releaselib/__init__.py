import sys, os, re, ConfigParser, time, zipfile

def print_title(string):
    print('\n### %-40s ###'%string)

DIR_STACK = []
def pushd(path):
    global DIR_STACK
    if os.path.exists(path):
        DIR_STACK.append(os.getcwd())
        os.chdir(path)
    
def popd():
    global DIR_STACK
    if len(DIR_STACK) > 0:
        d = DIR_STACK.pop()
        os.chdir(d)
        
rep_count = 0
def repl(m):
    global rep_count
    rep_count += 1
    return ''
        
def strip_dev_code(FILE):
    global rep_count
    START_TAG = r'# !\-\- RELEASE SNIP'
    END_TAG   = r'# RELEASE SNIP \-\-!'
    
    pattern = r'(' + START_TAG + r')(.*?)('+ END_TAG + r')'
    
    print('Modifying %s' % FILE)
    
    fh = open(FILE, 'r')
    FILE_CONTENTS = fh.read()
    fh.close()
    
    rep_count = 0
    
    cre = re.compile(pattern, re.MULTILINE|re.DOTALL)
    FILE_CONTENTS = cre.sub(repl, FILE_CONTENTS)
    
    fh = open(FILE, 'w')
    fh.write(FILE_CONTENTS)
    fh.close
    
    print('\t%i blocks replaced' % rep_count)
    
def make_config_file(EXDIR, VER, AUTOUPDATE_URLs):
    VER = '%i'%VER
        
    cf = ConfigParser.SafeConfigParser()
    
    for s in ['EF', 'indigo']:
        cf.add_section(s)
        cf.set(s, 'update_location', AUTOUPDATE_URLs['EF']+'/%s_update.manifest'%s.lower())
        cf.set(s, 'ver', VER)
        cf.set(s, 'last_check', '0')
        cf.set(s, 'update_period', '864000')
        
        cm = ConfigParser.SafeConfigParser()
        cm.add_section(s)
        cm.set(s, 'latest_version', VER)
        cm.set(s, 'package_location', AUTOUPDATE_URLs[s]+'/release/%s/%s_%s.zip'%(s.lower(),s.lower(),VER))
        fh=open(EXDIR+'/../%s_update.manifest'%s.lower(), 'w')
        cm.write(fh)
        fh.close()
        
        
    fh = open(EXDIR+'/ef.cfg', 'w')
    cf.write(fh)
    fh.close()

def zipper(dir, zip_file):
    zip = zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED)
    root_len = len(os.path.abspath(dir))
    for root, dirs, files in os.walk(dir):
        archive_root = os.path.abspath(root)[root_len:]
        for f in files:
            if '.svn' in root: continue
            if f[-4:] == '.pyc': continue
            fullpath = os.path.join(root, f)
            archive_name = os.path.join(archive_root, f)
            #print f
            zip.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
    zip.close()
    return zip_file

def make_release_zips(release_dir, VER):
    VER = '%i'%VER
    output_dir = os.path.split(release_dir)[0]
    
    zipper(release_dir+'/ef', output_dir+'/ef_'+VER+'.zip')
    zipper(release_dir+'/engines/indigo', output_dir+'/indigo_'+VER+'.zip')