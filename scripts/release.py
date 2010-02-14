#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
# --------------------------------------------------------------------------
# Blender 2.5 Exporter Framework - LuxRender Plug-in
# --------------------------------------------------------------------------
#
# Authors:
# Doug Hammond
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****
#

# Standard Library imports
import sys, os, shutil, glob
import releaselib

# Check CLI args
if len(sys.argv) < 2:
    print('No version or upload username given')
    print('%s <version> [username]' % sys.argv[0])
    sys.exit(1)
if len(sys.argv) < 3:
    print('No upload username given, will not upload release')
    print('%s <version> [username]' % sys.argv[0])
    #sys.exit(1)

# Important URLs + Constants
FRAMEWORK_REPO  = 'http://ef.beulahelectronics.co.uk/hg/ef'
UPLOAD_HOSTS    = {
    'EF':           'ef.beulahelectronics.co.uk',
    'luxrender':    'ef.beulahelectronics.co.uk'
}
AUTOUPDATE_URLs = {
    'EF':           'http://%s/auto_update/' % UPLOAD_HOSTS['EF'],
    'luxrender':    'http://%s/auto_update/' % UPLOAD_HOSTS['luxrender'],
}
AUTOUPDATE_PATHs = {
    'EF':           '/home/beulahelectronics/%s/auto_update' % UPLOAD_HOSTS['EF'],
    'luxrender':    '/home/beulahelectronics/%s/auto_update' % UPLOAD_HOSTS['luxrender'],
}

if len(sys.argv) > 2:
    AUTOUPDATE_USERNAMES = {
        'EF': 'beulahelectronics',
        'luxrender': sys.argv[2]
    }

# NON-standard library imports
try:
    import mercurial.ui
    import mercurial.hg
    import mercurial.commands
    mui = mercurial.ui.ui()
except ImportError:
    print('This script requires Mercurial')
    if sys.platform[:3] == 'win':
        print(' -> http://mercurial.berkwood.com/ (win32-py2.6 binaries)')
    else:
        print(' -> http://mercurial.selenic.com/downloads/')
    sys.exit(1)
    
try:
    import paramiko
    ssh_key_agent = paramiko.Agent()
except ImportError:
    print('This script requires Paramiko')
    print(' -> http://www.voidspace.org.uk/python/modules.shtml#pycrypto')
    print(' -> http://www.lag.net/paramiko/')
    sys.exit(1)

# Go up to repo root
releaselib.pushd('../')
REPO_DIR = os.getcwd()

# Get the repo revision number
repo_root = mercurial.hg.repository(mui, REPO_DIR)
repo_cl = repo_root.changelog
REPO_REV = repo_cl.rev( repo_cl.tip() )
print('luxblend25 revision is %i'%REPO_REV)

# Create release directory
releaselib.print_title('Create release directory')
RELEASE_PARENT = os.path.join(os.getcwd(), 'release')
RELEASE_DIR = os.path.join(os.getcwd(), 'release', sys.argv[1])
try:
    os.makedirs(RELEASE_DIR)
    print('Assembling to directory: %s' % RELEASE_DIR)
except Exception as err:
    if not 'exists' in str(err): # it's OK if the target dir exists
        print(err) #'Cannot make release dir: %s' % RELEASE_DIR)
        sys.exit(1)

# Pull a copy of the Exporter Framework into release directory
releaselib.print_title('Get latest Exporter Framework')
mercurial.commands.init(mui, RELEASE_DIR)
hg_local = mercurial.hg.repository(mui, RELEASE_DIR)
mercurial.commands.pull(mui, hg_local, source=FRAMEWORK_REPO)
mercurial.commands.update(mui, hg_local)
# Get HG repo version
EF_REV = hg_local.changelog.rev( hg_local.changelog.tip() )
print('EF revision is %i'%EF_REV)

# remove hg repo files, not needed any more
for hgfiles in glob.glob(RELEASE_DIR+'/.hg*'):
    if os.path.isdir(hgfiles):
        shutil.rmtree(hgfiles, True)
    else:
        os.remove(hgfiles)

# REPO add the Exporter Framework files
releaselib.print_title('Add Exporter Framework to release')
mercurial.commands.add(mui, repo_root)

# Add trunk sources as EF engine
releaselib.print_title('Copy LuxRender plugin to release')
mercurial.commands.copy(
    mui,
    repo_root,
    'src/luxrender',
    os.path.join(RELEASE_DIR, 'engines', 'luxrender'),
    exclude=['(.*)\.pyc$'] #,'(.*)\.so$']
)

# Remove development code from source files
releaselib.print_title('Finalise source code')
STRIP_FILES = ['bootstrap.py']
for f in STRIP_FILES:
    releaselib.strip_dev_code(os.path.join(RELEASE_DIR, f))

VERSIONS = {
 'EF':          '%i'%EF_REV,
 'luxrender':   '%i'%REPO_REV
} 

# Create config file
releaselib.print_title('Create config files')
releaselib.make_config_file(
	RELEASE_DIR,
	VERSIONS,
	AUTOUPDATE_URLs
)
mercurial.commands.add(mui, repo_root, os.path.join(RELEASE_DIR, 'ef.cfg'))

# Create zipfiles
releaselib.print_title('Create release ZIPs')
for f in glob.glob(RELEASE_PARENT+'/*.zip'):
    os.remove(f)
releaselib.make_release_zips(RELEASE_DIR, VERSIONS)

# Upload
#if len(sys.argv) > 2:
#    releaselib.print_title('Upload release files')
#    if len(ssh_key_agent.keys) > 0:
#        # only try 1st key
#        key = ssh_key_agent.keys[0]
#        # upload zips
#        for mod in ['EF', 'luxrender']:
#            print('Connecting %s@%s' % (AUTOUPDATE_USERNAMES[mod],UPLOAD_HOSTS[mod]))
#            ssh_transport = paramiko.Transport(UPLOAD_HOSTS[mod])
#            ssh_transport.connect()
#            ssh_transport.auth_publickey(AUTOUPDATE_USERNAMES[mod], key)
#            sftp = paramiko.SFTPClient.from_transport(ssh_transport)
#            for modf in glob.glob(RELEASE_PARENT+'/%s*.zip'%mod.lower()):
#                src = modf
#                trg = AUTOUPDATE_PATHs[mod] + ('/release/%s/'%mod.lower()) + os.path.basename(modf)
#                print('%s -> %s@%s:%s' % (src,AUTOUPDATE_USERNAMES[mod],UPLOAD_HOSTS[mod],trg))
#                sr = sftp.put(src, trg)
#                print('%i bytes transferred' % sr.st_size)
#            sftp.close()
#            ssh_transport.close()
#            del sftp
#            del ssh_transport
#            
#        # Upload manifests
#        print('Connecting %s@%s' % (AUTOUPDATE_USERNAMES['EF'],UPLOAD_HOSTS['EF']))
#        ssh_transport = paramiko.Transport(UPLOAD_HOSTS['EF'])
#        ssh_transport.connect()
#        ssh_transport.auth_publickey(AUTOUPDATE_USERNAMES['EF'], key)
#        sftp = paramiko.SFTPClient.from_transport(ssh_transport)
#        for modf in glob.glob(RELEASE_PARENT+'/*_update.manifest'):
#            src = modf
#            trg = AUTOUPDATE_PATHs[mod] + '/' + os.path.basename(modf)
#            print('%s -> %s@%s:%s' % (src,AUTOUPDATE_USERNAMES['EF'],UPLOAD_HOSTS['EF'],trg))
#            sftp.put(src, trg)
#            print('%i bytes transferred' % sr.st_size)
#        sftp.close()
#        ssh_transport.close()
#        del sftp
#        del ssh_transport
#    else:
#        print('No SSH Key Agent found, or no keys available; cannot upload')


releaselib.print_title('Finished')
print('Please check contents of %s and commit if OK' % RELEASE_DIR)
# return to script dir
releaselib.popd()