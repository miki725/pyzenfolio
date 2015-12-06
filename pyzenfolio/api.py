from __future__ import print_function, unicode_literals
import json
import mimetypes
import os
import urllib
from hashlib import sha256
from random import randint

import requests
import six

from .constants import (
    API_ENDPOINT,
    DEFAULT_CONFIG,
    DEFAULT_OBJECTS,
    REQUEST_HEADERS,
)
from .exceptions import APIError, ConfigError, HTTPError, ZenfolioError
from .utils import AttrDict, convert_from_datetime, convert_to_datetime
from .validate import assert_type, validate_object, validate_value


class PyZenfolio(object):
    def __init__(self, config_file=None, auth=None):
        self.config = AttrDict(DEFAULT_CONFIG)
        if config_file:
            self.config.update(self.get_config(config_file))
            self.auth = self.config.auth
        if auth:
            self.auth = AttrDict(auth)
        self.init_session()

    # ---------------------------------------------------------------#
    #                      Authentication                            #
    # ---------------------------------------------------------------#

    def Authenticate(self, force=False):
        if 'token' in self.auth and self.auth.token and not force:
            return

        _challenge = self.GetChallenge()
        salt = b''.join(map(six.int2byte, _challenge.PasswordSalt))
        challenge = b''.join(map(six.int2byte, _challenge.Challenge))

        password_hash = sha256(salt + self.auth.password.encode('utf-8')).digest()
        proof = sha256(challenge + password_hash).digest()
        proof_as_ints = list(six.iterbytes(proof))

        token = self.call('Authenticate', [_challenge.Challenge, proof_as_ints])
        self.auth.token = token
        return token

    def GetChallenge(self):
        return self.call('GetChallenge', self.auth.username)

    def AuthenticatePlain(self):
        token = self.call('AuthenticatePlain', [self.auth.username, self.auth.password])
        self.auth.token = token

    def AuthenticateVisitor(self):
        visitor_key = self.GetVisitorKey()
        token = self.call('AuthenticateVisitor', [visitor_key])
        self.auth.token = token

    def GetVisitorKey(self):
        return self.call('GetVisitorKey')

    # ---------------------------------------------------------------#
    #                        Get methods                             #
    # ---------------------------------------------------------------#

    def GetCategories(self):
        return self.call('GetCategories')

    def GetDownloadOriginalKey(self, photo_id, password):
        return self.call('GetDownloadOriginalKey', [photo_id, password])

    def GetPopularPhotos(self, offset=0, limit=1000):
        return self.call('GetPopularPhotos', [offset, limit])

    def GetPopularSets(self, set_type='Gallery', offset=0, limit=1000):
        validate_value(set_type, 'PhotoSetType', 'GetPopularSets')
        return self.call('GetPopularSets', [set_type, offset, limit])

    def GetRecentPhotos(self, offset=0, limit=1000):
        return self.call('GetRecentPhotos', [offset, limit])

    def GetRecentSets(self, set_type='Gallery', offset=0, limit=1000):
        validate_value(set_type, 'PhotoSetType', 'GetRecentSets')
        return self.call('GetRecentSets', [set_type, offset, limit])

    def GetVideoPlaybackUrl(self, photo_id, mode='Http', width=1920, height=1080):
        validate_value(mode, 'VideoPlaybackMode', 'GetVideoPlaybackUrl')
        return self.call('GetVideoPlaybackUrl', [photo_id, mode, width, height])

    # ---------------------------------------------------------------#
    #                        Load methods                            #
    # ---------------------------------------------------------------#

    def LoadAccessRealm(self, realm_id):
        return self.call('LoadAccessRealm', realm_id)

    def LoadGroup(self, id, info_level='Full', recursive=False):
        validate_value(info_level, 'InformationLevel', 'LoadGroup')
        return self.call('LoadGroup', [id, info_level, recursive])

    def LoadGroupHierarchy(self, username=None):
        if username is None:
            username = self.auth.username
        return self.call('LoadGroupHierarchy', username)

    def LoadMessages(self, mailbox_id, posted_since=None, include_deleted=False):
        posted_since = convert_from_datetime(posted_since)
        return self.call('LoadMessages', [mailbox_id, posted_since, include_deleted])

    def LoadSharedFavoritesSets(self):
        return self.call('LoadSharedFavoritesSets')

    def LoadPhoto(self, photo_id, info_level='Full'):
        validate_value(info_level, 'InformationLevel', 'LoadPhoto')
        return self.call('LoadPhoto', [photo_id, info_level])

    def LoadPhotoSet(self, set_id, info_level='Full', with_photos=True):
        validate_value(info_level, 'InformationLevel', 'LoadPhotoSet')
        return self.call('LoadPhotoSet', [set_id, info_level, with_photos])

    def LoadPhotoSetPhotos(self, set_id, start_index=0, limit=5000):
        return self.call('LoadPhotoSetPhotos', [set_id, start_index, limit])

    def LoadPrivateProfile(self):
        return self.call('LoadPrivateProfile')

    def LoadPublicProfile(self, username=None):
        if username is None:
            username = self.auth.username
        return self.call('LoadPublicProfile', username)

    # ---------------------------------------------------------------#
    #                       Create methods                           #
    # ---------------------------------------------------------------#

    def CreateFavoritesSet(self, name, username, ids):
        return self.call('CreateFavoritesSet', [name, username, ids])

    def CreateGroup(self, parent_id, group=None):
        if group is None:
            group = {}
        updater = dict(DEFAULT_OBJECTS['GroupUpdater'])
        updater.update(group)
        validate_object(group, 'GroupUpdater', 'CreateGroup')
        return self.call('CreateGroup', [parent_id, updater])

    def CreatePhotoFromUrl(self, photoset_id, url, cookies=None):
        if isinstance(cookies, dict):
            cookies = ';'.join(['='.join([urllib.quote_plus(i) for i in c])
                                for c in cookies.items()])
        return self.call('CreatePhotoFromUrl', [photoset_id, url, cookies])

    def CreatePhotoSet(self, group_id, set_type='Gallery', photoset=None):
        validate_value(set_type, 'PhotoSetType', 'CreatePhotoSet')
        if photoset is None:
            photoset = {}
        updater = dict(DEFAULT_OBJECTS['PhotoSetUpdater'])
        updater.update(photoset)
        validate_object(updater, 'PhotoSetUpdater', 'CreatePhotoSet')
        return self.call('CreatePhotoSet', [group_id, set_type, updater])

    def CreateVideoFromUrl(self, photoset_id, url, cookies=None):
        if isinstance(cookies, dict):
            cookies = ';'.join(['='.join([urllib.quote_plus(i) for i in c])
                                for c in cookies.items()])
        return self.call('CreateVideoFromUrl', [photoset_id, url, cookies])

    def UploadPhoto(self, photoset, path, filename=None):
        assert_type(photoset, 'PhotoSet', 'photoset', 'UploadPhoto')
        upload_url = photoset.UploadUrl

        with open(path, 'rb') as fid:
            data = fid.read()
            filename = filename or os.path.basename(path)

            headers = self.get_request_headers()
            headers.update({
                'Content-Type': mimetypes.guess_type(filename)[0],
            })
            params = {
                'filename': filename,
            }
            request = requests.post(upload_url,
                                    params=params,
                                    data=data,
                                    headers=headers)
            if request.status_code != 200:
                raise HTTPError(API_ENDPOINT,
                                request.status_code,
                                request.headers,
                                request.content)
            return request.text

        raise APIError('Could not upload photo')

    def AddMessage(self, mail_id, message):
        validate_object(message, 'MessageUpdater', 'AddMessage')
        return self.call('AddMessage', [mail_id, message])

    # ---------------------------------------------------------------#
    #                         Set  methods                           #
    # ---------------------------------------------------------------#

    def SetGroupTitlePhoto(self, group_id, photo_id):
        return self.call('SetGroupTitlePhoto', [group_id, photo_id])

    def SetPhotoSetFeaturedIndex(self, photoset_id, index):
        return self.call('SetPhotoSetFeaturedIndex', [photoset_id, index])

    def SetPhotoSetTitlePhoto(self, photoset_id, photo_id):
        return self.call('SetPhotoSetTitlePhoto', [photoset_id, photo_id])

    def SetRandomPhotoSetTitlePhoto(self, photoset_id):
        return self.call('SetRandomPhotoSetTitlePhoto', [photoset_id])

    # ---------------------------------------------------------------#
    #                        Update methods                          #
    # ---------------------------------------------------------------#

    def UpdateGroup(self, group_id, group=None):
        if group is None:
            group = {}
        updater = dict(DEFAULT_OBJECTS['GroupUpdater'])
        updater.update(group)
        validate_object(updater, 'GroupUpdater', 'UpdateGroup')
        return self.call('UpdateGroup', [group_id, updater])

    def UpdateGroupAccess(self, group_id, group_access=None):
        if group_access is None:
            group_access = {}
        updater = dict(DEFAULT_OBJECTS['AccessUpdater'])
        updater.update(group_access)
        validate_object(updater, 'AccessUpdater', 'UpdateGroupAccess')
        return self.call('UpdateGroupAccess', [group_id, updater])

    def UpdatePhoto(self, photo_id, photo=None):
        if photo is None:
            photo = {}
        updater = dict(DEFAULT_OBJECTS['PhotoUpdater'])
        updater.update(photo)
        validate_object(updater, 'PhotoUpdater', 'UpdatePhoto')
        return self.call('UpdatePhoto', [photo_id, updater])

    def UpdatePhotoAccess(self, photo_id, photo_access=None):
        if photo_access is None:
            photo_access = {}
        updater = dict(DEFAULT_OBJECTS['AccessUpdater'])
        updater.update(photo_access)
        validate_object(updater, 'AccessUpdater', 'UpdatePhotoAccess')
        return self.call('UpdatePhotoAccess', [photo_id, updater])

    def UpdatePhotoSet(self, photoset_id, photoset=None):
        if photoset is None:
            photoset = {}
        updater = dict(DEFAULT_OBJECTS['PhotoSetUpdater'])
        updater.update(photoset)
        validate_object(updater, 'PhotoSetUpdater', 'UpdatePhotoSet')
        return self.call('UpdatePhotoSet', [photoset_id, updater])

    def UpdatePhotoSetAccess(self, photoset_id, photoset_access=None):
        if photoset_access is None:
            photoset_access = {}
        updater = dict(DEFAULT_OBJECTS['AccessUpdater'])
        updater.update(photoset_access)
        validate_object(updater, 'AccessUpdater', 'UpdatePhotoSetAccess')
        return self.call('UpdatePhotoSetAccess', [photoset_id, updater])

    # ---------------------------------------------------------------#
    #                          Move methods                          #
    # ---------------------------------------------------------------#

    def MoveGroup(self, group_id, dest_group_id, index):
        return self.call('MoveGroup', [group_id, dest_group_id, index])

    def MovePhoto(self, photoset_id, photo_id, dest_photoset_id, index):
        return self.call('MovePhoto', [photoset_id, photo_id, dest_photoset_id, index])

    def MovePhotos(self, photoset_id, dest_photoset_id, ids):
        return self.call('MovePhotos', [photoset_id, dest_photoset_id, ids])

    def MovePhotoSet(self, photoset_id, dest_group_id, index):
        return self.call('MovePhotoSet', [photoset_id, dest_group_id, index])

    # ---------------------------------------------------------------#
    #                            Search                              #
    # ---------------------------------------------------------------#

    def SearchPhotoByCategory(self, search_id, sort, category, offset, limit):
        validate_value(sort, 'SortOrder', 'SearchPhotoByCategory')
        return self.call('SearchPhotoByCategory', [search_id, sort, category, offset, limit])

    def SearchPhotoByText(self, search_id, sort, query, offset, limit):
        validate_value(sort, 'SortOrder', 'SearchPhotoByText')
        return self.call('SearchPhotoByText', [search_id, sort, query, offset, limit])

    def SearchSetByCategory(self, search_id, photoset_type, sort, category, offset, limit):
        validate_value(photoset_type, 'PhotoSetType', 'SearchSetByCategory')
        validate_value(sort, 'SortOrder', 'SearchSetByCategory')
        return self.call('SearchSetByCategory', [search_id, photoset_type, sort, category, offset, limit])

    def SearchSetByText(self, search_id, photoset_type, sort, query, offset, limit):
        validate_value(photoset_type, 'PhotoSetType', 'SearchSetByText')
        validate_value(sort, 'SortOrder', 'SearchSetByText')
        return self.call('SearchSetByText', [search_id, photoset_type, sort, query, offset, limit])

    # ---------------------------------------------------------------#
    #                        Delete methods                          #
    # ---------------------------------------------------------------#

    def DeleteGroup(self, group_id):
        return self.call('DeleteGroup', group_id)

    def DeleteMessage(self, mailbox_id, index):
        return self.call('DeleteMessage', [mailbox_id, index])

    def DeletePhoto(self, photo_id):
        return self.call('DeletePhoto', photo_id)

    def DeletePhotos(self, photo_ids):
        return self.call('DeletePhotos', photo_ids)

    def DeletePhotoSet(self, photoset_id):
        return self.call('DeletePhotoSet', photoset_id)

    # ---------------------------------------------------------------#
    #                         Miscellaneous                          #
    # ---------------------------------------------------------------#

    def CollectionAddPhoto(self, coll_id, photo_id):
        return self.call('CollectionAddPhoto', [coll_id, photo_id])

    def CollectionRemovePhoto(self, coll_id, photo_id):
        return self.call('CollectionRemovePhoto', [coll_id, photo_id])

    def KeyringAddKeyPlain(self, keyring, realm_id, password):
        return self.call('KeyringAddKeyPlain', [keyring, realm_id, password])

    def KeyringGetUnlockedRealms(self, keyring):
        return self.call('KeyringGetUnlockedRealms', keyring)

    def ReindexPhotoSet(self, photoset_id, index, mapping):
        return self.call('ReindexPhotoSet', [photoset_id, index, mapping])

    def RemoveGroupTitlePhoto(self, group_id):
        return self.call('RemoveGroupTitlePhoto', [group_id])

    def RemovePhotoSetTitlePhoto(self, photoset_id):
        return self.call('RemovePhotoSetTitlePhoto', [photoset_id])

    def ReorderGroup(self, group_id, order):
        validate_value(order, 'GroupShiftOrder', 'ReorderGroup')
        return self.call('ReorderGroup', [group_id, order])

    def ReorderPhotoSet(self, photoset_id, order):
        validate_value(order, 'ShiftOrder', 'ReorderPhotoSet')
        return self.call('ReorderPhotoSet', [photoset_id, order])

    def ReplacePhoto(self, original_id, replacement_id):
        return self.call('ReplacePhoto', [original_id, replacement_id])

    def RotatePhoto(self, photo_id, rotation):
        validate_value(rotation, 'PhotoRotation', 'RotatePhoto')
        return self.call('RotatePhoto', [photo_id, rotation])

    def ShareFavoritesSet(self, favset_id, favset_name, name, email, message):
        return self.call('ShareFavoritesSet', [favset_id, favset_name, name, email, message])

    def UndeleteMessage(self, mailbox_id, message_index):
        return self.call('UndeleteMessage', [mailbox_id, message_index])

    # ---------------------------------------------------------------#
    #                           Internals                            #
    # ---------------------------------------------------------------#

    def get_config(self, config_file):
        with open(config_file, 'rb') as fid:
            data = fid.read().decode('utf-8')
            try:
                return AttrDict(json.loads(data))
            except ValueError:
                raise ConfigError('Could not open config file')

    def get_request_headers(self):
        headers = dict(REQUEST_HEADERS)
        if 'token' in self.auth:
            headers.update({
                'X-Zenfolio-Token': self.auth.token
            })
        return headers

    def init_session(self):
        self.session = requests.Session()

    def call(self, method, params=None):
        if params is None:
            params = []
        elif not isinstance(params, (list, tuple)):
            params = [params]

        data = AttrDict({
            'method': method,
            'params': params,
            'id': randint(0, 2 ** 16 - 1)
        })

        try:
            request = self.session.post(API_ENDPOINT,
                                        data=json.dumps(data),
                                        headers=self.get_request_headers())
        except Exception as e:
            raise APIError(e.message)
        if request.status_code != 200:
            raise HTTPError(API_ENDPOINT,
                            request.status_code,
                            request.headers,
                            request.content)

        body = convert_to_datetime(AttrDict(request.json()))

        if body.error:
            code = None
            if 'code' in body.error:
                code = body.error.code
            raise ZenfolioError(code, body.error.message)

        if body.id != data.id:
            raise APIError('Response ID does match request ID')

        return body.result
