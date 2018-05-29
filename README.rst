=======================
Rasahub-Google-Calendar
=======================

Rasahub-Google-Calendar provides an interface to access Google Calendar entries.
It uses User IDs from Humhub to get authentification and uses them to provide calendar information to Humhub and Rasa_Core.

----

Prerequisites
=============

* Python installed

Installation
============

Pypi package
------------

Install via pip:

.. code-block:: bash

  pip install rasahub-google-calendar


Usage
=====

Create configuration
--------------------

Create file config.yml in working path containing client id, secret, scope and so on. Example:

.. code-block:: yaml

  google:
    package: 'rasahub_google_calendar'
    classname: 'RasaGoogleCalendar'
    type: 'datastore'
    init:
      google_client_id: 'ID.apps.googleusercontent.com'
      google_client_secret: 'm-SECRETKEY'
      google_redirect_uri: 'http://localhost:8080/oauth2callback'
      google_scope: 'https://www.googleapis.com/auth/calendar'



Command-Line API
----------------

Start rasahub:

.. code-block:: bash

  python -m rasahub



* License: MIT
* `PyPi`_ - package installation

.. _PyPi: https://pypi.python.org/pypi/rasahub
