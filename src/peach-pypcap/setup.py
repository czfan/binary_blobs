#!/usr/bin/env python
#
# $Id: setup.py 84 2007-08-17 12:41:03Z dugsong $

from distutils.core import setup, Extension
from distutils.command import config, clean
import cPickle, glob, os, sys
from Pyrex.Distutils import build_ext

pcap_config = {}
pcap_cache = 'config.pkl'

class config_pcap(config.config):
    description = 'configure pcap paths'
    user_options = [ ('with-pcap=', None,
                      'path to pcap build or installation directory') ]
    
    def initialize_options(self):
        config.config.initialize_options(self)
        self.dump_source = 0
        #self.noisy = 0
        self.with_pcap = None

    def _write_config_h(self, cfg):
        # XXX - write out config.h for pcap_ex.c
        d = {}
        if os.path.exists(os.path.join(cfg['include_dirs'][0], 'pcap-int.h')):
            d['HAVE_PCAP_INT_H'] = 1
        buf = open(os.path.join(cfg['include_dirs'][0], 'pcap.h')).read()
        if buf.find('pcap_file(') != -1:
            d['HAVE_PCAP_FILE'] = 1
        if buf.find('pcap_compile_nopcap(') != -1:
            d['HAVE_PCAP_COMPILE_NOPCAP'] = 1
        if buf.find('pcap_setnonblock(') != -1:
            d['HAVE_PCAP_SETNONBLOCK'] = 1
        f = open('config.h', 'w')
        for k, v in d.iteritems():
            f.write('#define %s %s\n' % (k, v))
    
    def _pcap_config(self, dirs=[ None ]):
	print "configuring"
        cfg = {}
        if not dirs[0]:
            dirs = [ '/usr', sys.prefix ] + glob.glob('/opt/libpcap*') + \
                   glob.glob('../libpcap*') + glob.glob('../wpdpack*')
        for d in dirs:
            for sd in ('include', 'include/pcap', ''):
                incdirs = [ os.path.join(d, sd) ]
                if os.path.exists(os.path.join(d, sd, 'pcap.h')):
                    cfg['include_dirs'] = [ os.path.join(d, sd) ]
                    for sd in ('lib', 'lib64', ''):
                        for lib in (('pcap', 'libpcap.a'),
                                    ('pcap', 'libpcap.so'),
                                    ('pcap', 'libpcap.dylib'),
                                    ('wpcap', 'wpcap.lib')):
                            if os.path.exists(os.path.join(d, sd, lib[1])):
                                cfg['library_dirs'] = [ os.path.join(d, sd) ]
                                cfg['libraries'] = [ lib[0] ]
                                if lib[0] == 'wpcap':
                                    cfg['libraries'].append('iphlpapi')
                                    cfg['extra_compile_args'] = \
                                        [ '-DWIN32', '-DWPCAP' ]
                                print 'found', cfg
                                self._write_config_h(cfg)
                                return cfg
        raise "couldn't find pcap build or installation directory"
    
    def run(self):
        #config.log.set_verbosity(0)
	conf = self._pcap_config([ self.with_pcap ])
        cPickle.dump(conf, open(pcap_cache, 'wb'))
        self.temp_files.append(pcap_cache)
	print conf

class clean_pcap(clean.clean):
    def run(self):
        clean.clean.run(self)
        if self.all and os.path.exists(pcap_cache):
            print "removing '%s'" % pcap_cache
            os.unlink(pcap_cache)

if len(sys.argv) > 1 and sys.argv[1] in ['build', 'bdist_msi', 'install']:
    try:
        pcap_config = cPickle.load(open(pcap_cache))
	print pcap_config
    except IOError:
        print >>sys.stderr, 'run "%s config" first!' % sys.argv[0]
        sys.exit(1)


pcap = Extension(name='pcap',
                 sources=[ 'pcap.pyx', 'pcap_ex.c' ],
                 include_dirs=pcap_config.get('include_dirs',''),
                 library_dirs=pcap_config.get('library_dirs',''),
                 libraries=pcap_config.get('libraries', ''),
                 extra_compile_args=pcap_config.get('extra_compile_args', ''))

pcap_cmds = { 'config':config_pcap, 'clean':clean_pcap, 'build_ext': build_ext }

setup(name='pcap',
      version='1.1',
      author='Dug Song',
      author_email='dugsong@monkey.org',
      url='http://monkey.org/~dugsong/pypcap/',
      description='packet capture library',
      cmdclass=pcap_cmds,
      ext_modules = [ pcap ])

