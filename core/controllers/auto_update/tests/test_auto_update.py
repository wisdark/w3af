'''
Created on Jan 10, 2011

@author: jandalia
'''

#### TODO: REMOVE ME BEFORE COMMIT!!! ##
import sys
sys.path.append('/home/jandalia/workspace2/w3af')
########################################

from pymock import PyMockTestCase, method, override, dontcare, set_count

from core.controllers.auto_update.auto_update import W3afSVNClient, Revision, SVNFilesList, FILE_UPD, \
    FILE_NEW, FILE_DEL, ST_CONFLICT, ST_MODIFIED, ST_UNKNOWN

REPO_URL = 'http://localhost/svn/w3af'
LOCAL_PATH = '/home/user/w3af'


def dummy(*args, **kwargs):
    pass


class TestW3afSVNClient(PyMockTestCase):
    
    rev = Revision(112, None)
    upd_files = SVNFilesList(
        [('file1.txt', FILE_NEW),
         ('file2.py', FILE_UPD),
         ('file3.jpg', FILE_DEL)],
         rev
        )

    def setUp(self):
        PyMockTestCase.setUp(self)
        
        W3afSVNClient._get_repourl = dummy
        self.client = W3afSVNClient(LOCAL_PATH)
        self.client._repourl = REPO_URL
        self.client._svnclient = self.mock()

    def test_has_repourl(self):
        self.assertTrue(self.client._repourl is not None)

    def test_has_svn_client(self):
        self.assertTrue(self.client._svnclient is not None)

    def test_has_localpath(self):
        self.assertTrue(self.client._localpath is not None)

    def test_upd(self):
        client = self.client
        method(client._svnclient, 'update').expects(LOCAL_PATH).returns([self.rev])
        override(client, '_filter_files').expects(client.UPD_ACTIONS)
        self.returns(self.upd_files)
        ## Stop recording. Play!
        self.replay()
        self.assertEquals(self.upd_files, client.update())
        ## Verify ##
        self.verify()

    def test_upd_fail(self):
        from pysvn import ClientError
        from ..auto_update import SVNUpdateError
        client = self.client
        method(client._svnclient, 'update').expects(LOCAL_PATH)
        self.raises(ClientError('file locked'))
        ## Stop recording. Play!
        self.replay()
        self.assertRaises(SVNUpdateError, client.update)
        ## Verify ##
        self.verify()
        
    def test_upd_conflict(self):
        '''
        Files in conflict exists after update.
        '''
        pass

    def test_upd_nothing_to_update(self):
        '''No update to current copy was made. Tell the user. Presumably 
        the revision was incremented'''
        pass

    def test_filter_files(self):
        import pysvn
        from pysvn import wc_notify_action as wcna
        from pysvn import Revision
        from core.controllers.auto_update.auto_update import os
        client = self.client
        override(os.path, 'isfile').expects(dontcare()).returns(True)
        set_count(exactly=2)
        ## Stop recording. Play!
        self.replay()
        # Call client's callback function several times
        f1 = '/path/to/file/foo.py'
        ev = {'action': wcna.update_delete,
               'error': None, 'mime_type': None, 'path': f1,
               'revision': Revision(pysvn.opt_revision_kind.number, 11)}
        client._register(ev)

        f2 = '/path/to/file/foo2.py'        
        ev2 = {'action': wcna.update_update,
               'error': None, 'mime_type': None,
               'path': f2,
               'revision': Revision(pysvn.opt_revision_kind.number, 11)}
        client._register(ev2)
        
        expected_res = SVNFilesList([(f1, FILE_DEL), (f2, FILE_UPD)])
        self.assertEquals(expected_res, 
            client._filter_files(filterbyactions=W3afSVNClient.UPD_ACTIONS))
        ## Verify ##
        self.verify()

    def test_status(self):
        from pysvn import wc_status_kind as wcsk
        client = self.client
        # Mock pysvnstatus objects
        smock = self.mock()
        smock.path
        self.setReturn('/some/path/foo')
        smock.text_status
        self.setReturn(wcsk.modified)
        
        smock2 = self.mock()
        smock2.path
        self.setReturn('/some/path/foo2')
        smock2.text_status
        self.setReturn(wcsk.conflicted)
        
        smock3 = self.mock()
        smock3.path
        self.setReturn('/some/path/foo3')
        smock3.text_status
        self.setReturn('some_weird_status')
        
        status_files = [smock, smock2, smock3]
        method(client._svnclient, 'status').expects(LOCAL_PATH, recurse=False)
        self.returns(status_files)
        ## Stop recording - Replay ##
        self.replay()
        expected_res = \
            SVNFilesList([
                ('/some/path/foo', ST_MODIFIED),
                ('/some/path/foo2', ST_CONFLICT),
                ('/some/path/foo3', ST_UNKNOWN)])
        self.assertEquals(expected_res, client.status())
        ## Verify ##
        self.verify()

    def test_need_to_update(self):
        client = self.client
        svninfomock = self.mock()
        svninfomock.rev.number
        self.setReturn(50)
        override(client, '_get_svn_info').expects(LOCAL_PATH).returns(svninfomock)
        
        svninfomock2 = self.mock()
        svninfomock2.rev.number
        self.setReturn(55)
        override(client, '_get_svn_info').expects(REPO_URL).returns(svninfomock2)
        ## Stop recording - Replay ##
        self.replay()
        self.assertTrue(client.need_to_update())
        ## Verify ##
        self.verify()

    def test_commit(self):
        pass
