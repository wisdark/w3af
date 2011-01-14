'''
Created on Jan 10, 2011

@author: jandalia
'''

from __future__ import with_statement
import os
import threading


DEBUG = 0


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
    
    def list(self, path_or_url=None):
        pass
    


# See what TODO: here
try:
    import pysvn
except:
    raise

# Actions on files
FILE_UPD = 'UPD' # Updated
FILE_NEW = 'NEW' # New
FILE_DEL = 'DEL' # Removed

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
    
    @property
    def URL(self):
        return self._repourl        
        
    def _get_svn_info(self, path_or_url):
        try:
            return self._svnclient.info2(path_or_url, recurse=False)[0][1]
        except pysvn.ClientError, ce:
            raise SVNUpdateError(*ce.args)
    
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
                updfiles = self._filter_files(self.UPD_ACTIONS)
                updfiles.rev = Revision(pysvn_rev.number, pysvn_rev.date)
                return updfiles
    
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
            except pysvn.ClientError, ce:
                raise SVNError(*ce)
            else:
                res = [(ent.path, pysvn_status_translator.get(ent.text_status,
                                              ST_UNKNOWN)) for ent in entries]
                return SVNFilesList(res)
    
    def list(self, path_or_url=None):
        '''
        TODO: Add docstring.
        '''
        with self._actionlock:
            if not path_or_url:
                path_or_url = self._localpath
            try:
                entries = self._svnclient.list(path_or_url, recurse=False)
            except pysvn.ClientError, ce:
                raise SVNError(*ce)
            else:
                res = [(ent.path, None) for ent, _ in entries]
                return SVNFilesList(res)
                
        

    def _filter_files(self, filterbyactions=()):
        '''
        Filter... Return files-actions
        @param filterby: 
        '''
        files = SVNFilesList()
        for ev in self._events:
            action = ev['action']
            if action in filterbyactions:
                path = ev['path']
                if os.path.isfile(path):
                    files.append(path, pysvn_action_translator[action])
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


class SVNFilesList(list):
    '''
    Wrapper for python list type. It may contain the number of the current
    revision and perform a 'smart' data (file paths along with their statuses)
    printing.
    '''
    def __init__(self, seq=(), rev=None):
        '''
        @param rev: Revision object
        '''
        list.__init__(self, seq)
        self._rev = rev
        self._sorted = True

    def _getrev(self):
        return self._rev

    def _setrev(self, rev):
        self._rev = rev

    # TODO: Cannot use *full* decorators as we're still on py2.5
    rev = property(_getrev, _setrev)

    def append(self, path, status):
        list.append(self, (path, status))
        self._sorted = False

    def __str__(self):
        # First sort by status
        sortfunc = lambda x, y: cmp(x[1], y[1])
        self.sort(cmp=sortfunc)
        print_list = ['%s    %s' % (f, s) for s, f in self]
        if self._rev:
            print_list.append('At revision %s.' % self._rev.number)
        return os.linesep.join(print_list)
    
    def __eq__(self, olist):
        return list.__eq__(self, olist) and self._rev == olist.rev
        

# Use this class to perform svn actions on code
SVNClientClass = W3afSVNClient


# Facade class. Intended to be used to to interact with the module
class VersionMgr(object): #TODO: Make it singleton?
    
    # Events
    ON_UPDATE = 1
    ON_UPDATE_CHECK = 2
    ON_COMMIT = 3
    
    def __init__(self, localpath):
        self._localpath = localpath
        self._client = SVNClientClass(localpath)
        self._reg_funcs = {} # Registered functions
    
    def is_update_avail(self):
        self._notify(VersionMgr.ON_UPDATE_CHECK)
        return self._client.need_to_update()
    
    def update(self):
        self._notify(VersionMgr.ON_UPDATE)
        
        if DEBUG:
            files = [('/some/path/foo', 'M'), ('/some/path/foo2', 'C'),
                        ('/some/path/foo3', 'N')]
            files = SVNFilesList(files, Revision(12, None))
            return files
        
        client = self._client
        #
        # Check if a new directory was added to extlib
        #
        ospath = os.path
        join = ospath.join
        # Find dirs in repo
        repourl = self._client.URL + '/' + 'extlib'
        # In repo we distinguish dirs from files by the dot (.) presence
        repodirs = (ospath.basename(d) for d, _ in client.list(repourl)[1:] \
                                        if ospath.basename(d).find('.') == -1)
        # Get local dirs
        extliblocaldir = join(self._localpath, 'extlib')
        extlibcontent = (join(extliblocaldir, f) for f in \
                                                os.listdir(extliblocaldir))
        localdirs = (ospath.basename(d) for d in extlibcontent \
                                                        if ospath.isdir(d))
        # At least one dir was added to the repo. We're not interested on
        # performing the update
        deps = set(repodirs).difference(localdirs)
        if deps:
            msg = 'At least one new dependency (%s) was included in w3af. ' \
            'Please update manually.' % str(', '.join(deps))
            self._notify(VersionMgr.ON_UPDATE, msg)
            return ()
        return client.update()
    
    def status(self, path=None):
        return self._client.status(path)
    
    def commit(self):
        self._notify(VersionMgr.ON_COMMIT)
        # TODO: Add implementation
    
    def register(self, eventname, func, msg):
        funcs = self._reg_funcs.setdefault(eventname, [])
        funcs.append((func, msg))
    
    def _notify(self, event, msg=''):
        '''
        Call registered functions for event. If `msg` is not empty then force
        to call the registered functions with `msg`.
        '''
        for f, _msg in self._reg_funcs.get(event, []):
            f(msg or _msg)

