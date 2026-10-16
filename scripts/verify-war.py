"""Reject incompatible bytecode, bundled container APIs and private configuration."""
import io
import sys
import zipfile
import xml.etree.ElementTree as ET


def inspect(archive, label):
    count = 0
    for name in archive.namelist():
        if name.endswith('.class'):
            data = archive.read(name)
            if data[:4] != b'\xca\xfe\xba\xbe':
                raise ValueError('Invalid class: ' + label + ':' + name)
            major = int.from_bytes(data[6:8], 'big')
            if major > 51:
                raise ValueError('Java 7 incompatible class: %s:%s (major %s)' % (label, name, major))
            if name.startswith(('javax/servlet/', 'jakarta/servlet/')):
                raise ValueError('Container API bundled: ' + name)
            count += 1
        elif name.endswith('.jar'):
            with zipfile.ZipFile(io.BytesIO(archive.read(name))) as nested:
                count += inspect(nested, name)
        elif name.rsplit('/', 1)[-1] == '.env' or '.sqlite' in name:
            raise ValueError('Private runtime file bundled: ' + name)
    return count


with zipfile.ZipFile(sys.argv[1]) as war:
    descriptor = ET.fromstring(war.read('WEB-INF/web.xml'))
    if descriptor.tag != '{http://java.sun.com/xml/ns/javaee}web-app' or descriptor.get('version') != '3.0':
        raise ValueError('Servlet 3.0 descriptor required')
    count = inspect(war, sys.argv[1])
    print('Java 7 WAR verified: %s classes, all major versions <= 51; Servlet 3.0; no bundled servlet APIs or private files' % count)
