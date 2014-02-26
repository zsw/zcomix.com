zcomix.com
==========

zcomix.com code base.

Requirements
------------

web2py[1] requires python version 2.5 or later 2.x. 

The following python modules are used.

    [BeautifulSoup Ver 3][2]
    [Python Imaging Library][3] or [Pillow][4]


To install with ArchLinux[4], use the following command.

$ pacman -S python2-beautifulsoup3 python2-pillow


Configuration
-------------

1. Copy settings.examples.conf to settings.conf

    $ cp applications/zcomix/private/{settings.example.conf,settings.conf}


2. Edit the settings as required.

    $ vi applications/zcomix/private/settings.conf


Run
---

Start the web2py server.

    $ cd zcomix.com
    $ SERVER_PRODUCTION_MODE=test python2 web2py.py 

If running on a remote server with ip address 123.123.123.123:

    $ SERVER_PRODUCTION_MODE=test python2 web2py.py -i 123.123.123.123 -p 80


[1]: http://web2py.com "web2py"
[2]: http://www.crummy.com/software/BeautifulSoup/index.html  "Beautiful Soup"
[3]: http://pythonware.com/products/pil/ "Python Imaging Library (PIL)"
[4]: https://github.com/python-imaging/Pillow "Pillow on github.com"
