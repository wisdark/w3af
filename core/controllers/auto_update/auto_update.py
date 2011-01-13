'''
Created on Jan 10, 2011

@author: jandalia
'''

from __future__ import with_statement
import os
import threading


class SVNError(Exception):
    pass


class SVNUpdateError(SVNError):
    pass


class SVNCommitError():
    pass


class SVNClient(object):
    '''
    Typically an abstract class. Intended to define behaviour. Not to be
    instantiated.
    '''
    
    def __init__(self, localpath):
        self._localpath = localpath
        self._repourl = self._get_repourl()
        # Action Locker! 
        self._actionlock = threading.RLock()
    
    def _get_repourl(self):
        '''
        Get repo's URL. To be implemented by subclasses.
        '''
        pass
    
    def update(self):
        pass
    
    def commit(self):
        pass
    
    def status(self, path=None):
        pass


# See what TODO: here
try:
    import pysvn
except:
    raise

# Actions on files
FILE_UPD = 1 # Updated
FILE_NEW = 2 # New
FILE_DEL = 3 # Removed

wcna = pysvn.wc_notify_action
pysvn_action_translator = {
    wcna.update_add: FILE_NEW,
    wcna.update_delete: FILE_DEL,
    wcna.update_update: FILE_UPD
}

# Files statuses
ST_CONFLICT = 'C'
ST_NORMAL = 'N'
ST_UNVERSIONED = 'U'
ST_MODIFIED = 'M'
ST_UNKNOWN = '?'

wcsk = pysvn.wc_status_kind
pysvn_status_translator = {
    wcsk.conflicted: ST_CONFLICT,
    wcsk.normal: ST_NORMAL,
    wcsk.unversioned: ST_UNVERSIONED,
    wcsk.modified: ST_MODIFIED
}


class W3afSVNClient(SVNClient):
    '''
    TODO: Add docstring
    '''
    
    UPD_ACTIONS = (wcna.update_add, wcna.update_delete, wcna.update_update)
    
    def __init__(self, localpath):
        '''
        TODO: Add docstring
        '''
        self._svnclient = pysvn.Client()
        # Call parent's __init__
        super(W3afSVNClient, self).__init__(localpath)
        # Set callback function
        self._svnclient.callback_notify = self._register
        # Events occurred in current action
        self._events = []
    
    def _get_repourl(self):
        '''
        Get repo's URL.
        '''
        svninfo = self._get_svn_info(self._localpath)
        return svninfo.URL
        
        
    def _get_svn_info(self, path_or_url):
        return self._svnclient.info2(path_or_url, recurse=False)[0][1]
    
    def need_to_update(self):
        '''
        Compares local revision to repo's and if the latter is greater return
        True. Otherwise False.
        '''
        localrev = self._get_svn_info(self._localpath).rev.number
        reporev = self._get_svn_info(self._repourl).rev.number
        if reporev > localrev:
            return True
        return False

    def update(self):
        '''
        TODO: Add docstring
        '''
        with self._actionlock:
            self._events = []
            try:
                pysvn_rev = self._svnclient.update(self._localpath)[0]
            except pysvn.ClientError, ce:
                raise SVNUpdateError(*ce.args)
            else:
                # Use our Revision class
                rev = Revision(pysvn_rev.number, pysvn_rev.date)
                updfiles = self._filter_files(self.UPD_ACTIONS)
                return (rev, updfiles)
    
    def commit(self):
        '''
        TODO: Add docstring
        '''
        pass
    
    def status(self, localpath=None):
        '''
        TODO: Add docstring
        
        @param localpath: Path to get the status from. If is None use project
            root.
        '''
        with self._actionlock:
            path = localpath or self._localpath
            try:
                entries = self._svnclient.status(path, recurse=False)
            except Exception:
                raise
            else:
                return \
                    [(ent.path, pysvn_status_translator.get(ent.text_status,
                                              ST_UNKNOWN)) for ent in entries]

    def _filter_files(self, filterbyactions=()):
        '''
        Filter... Return files-actions
        @param filterby: 
        '''
        files = []
        for ev in self._events:
            action = ev['action']
            if action in filterbyactions:
                path = ev['path']
                if os.path.isfile(path):
                    files.append((path, pysvn_action_translator[action]))
        return files
    
    def _register(self, event):
        '''
        Callback method. Registers all events taking place during this action.
        '''
        self._events.append(event)


class Revision(object):
    
    def __init__(self, number, date):
        self._number = number
        self._date = date

    def __eq__(self, rev):
        return self._number == rev.number and \
                self._date == rev.date
    
    @property
    def date(self):
        return self._date
    
    @property
    def number(self):
        return self._number

# Use this class to perform svn actions on code
SVNClientClass = W3afSVNClient


# Facade class. Intended to be used to to interact with the module
class VersionMgr(object): #TODO: Make it singleton?
    
    def __init__(self, localpath):
        # TODO: see exceptions here
        self._client = SVNClientClass(localpath)
    
    def is_update_avail(self):
        return self._client.need_to_update()
    
    def update(self):
        return self._client.update()
    
    def status(self, path=None):
        return self._client.status(path)
    
    def commit(self):
        pass

