PyZenfolio
==========

.. image:: https://badge.fury.io/py/pyzenfolio.png
    :target: http://badge.fury.io/py/pyzenfolio

Light-weight Zenfolio API Python wrapper.

Using this wrapper is pretty straight-forward and does not
require to use any special data-structures. Everything is
returned as an ``AttrDict`` (same as ``dict`` however
dictionary items can be accessed via Python attribute
dot notation ``foo['bar'] == foo.bar``).

Example
-------

::

    from pyzenfolio import PyZenfolio

    api = PyZenfolio(auth={'username': 'foo', 'password': 'bar'})
    api.Authenticate()

    # lookup user
    user = api.LoadPublicProfile()
    # AttrDict allows to access items like this
    domain = user.DomainName
    uploaded_photos = user.PhotoCount

    # create photoset
    photoset = api.CreatePhotoSet(
        user.RootGroup.Id,
        attr={
            'Title': 'foo'
        }
    )
    photoset_url = photoset.PageUrl

    # upload image
    api.UploadPhoto(photoset, 'bar.jpg')

    # get image download URL
    image = api.LoadPhotoSetPhotos(photoset.Id)
    url = image.OriginalUrl

.. warning::

    This is a beta release. Please report bugs via GitHub issues.

